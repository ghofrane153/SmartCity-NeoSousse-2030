"""
manager.py
==========
Le chef d'orchestre des automates.

SON RÔLE :
  - Charger les états depuis MySQL (ex: un capteur est 'SIGNALE' en DB → créer son FSM dans cet état)
  - Appliquer un événement sur un automate ET mettre à jour la DB en même temps
  - Exposer un résumé de tous les états pour l'API de ton ami

C'est CE fichier que l'endpoint GET /automates/status de ton ami va utiliser.
"""

import mysql.connector
from automaton.capteur_fsm import CapteurFSM
from automaton.intervention_fsm import InterventionFSM
from automaton.vehicule_fsm import VehiculeFSM

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",      # ← adapte si besoin
    "database": "smart_city"
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# CAPTEURS
# ============================================================

def charger_capteur(capteur_id: str) -> CapteurFSM:
    """
    Lit l'état actuel du capteur en DB et crée un FSM dans cet état.
    Comme ça, si le capteur est déjà 'SIGNALE' en DB, l'automate
    reprend exactement là où on en était.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT statut FROM CAPTEUR WHERE id_capteur = %s", (capteur_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Capteur '{capteur_id}' non trouvé en base de données")

    # Normalise le statut DB vers le nom d'état de l'automate
    # (la DB stocke 'SIGNALE', l'automate attend 'SIGNALE')
    etat_db = row['statut'].upper().replace(' ', '_')
    return CapteurFSM(capteur_id=capteur_id, etat_initial=etat_db)


def appliquer_evenement_capteur(capteur_id: str, evenement: str) -> dict:
    """
    Applique un événement sur un capteur ET sauvegarde le nouvel état en DB.
    C'est la fonction principale utilisée par l'API.
    """
    fsm = charger_capteur(capteur_id)
    resultat = fsm.appliquer_evenement(evenement)

    if resultat["succes"]:
        # Mise à jour du statut en base de données
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE CAPTEUR SET statut = %s WHERE id_capteur = %s",
            (fsm.state, capteur_id)
        )
        conn.commit()
        conn.close()
        print(f"✓ DB mise à jour : capteur {capteur_id} → {fsm.state}")

    return resultat


def get_statut_tous_capteurs() -> list:
    """Retourne un résumé de tous les capteurs avec leur état et transitions disponibles"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_capteur, type_capteur, statut, zone FROM CAPTEUR LIMIT 100")
    capteurs = cursor.fetchall()
    conn.close()

    resultat = []
    for c in capteurs:
        etat = c['statut'].upper().replace(' ', '_')
        fsm = CapteurFSM(capteur_id=c['id_capteur'], etat_initial=etat)
        resultat.append({
            "id": c['id_capteur'],
            "type": c['type_capteur'],
            "zone": c['zone'],
            "etat": fsm.state,
            "transitions_disponibles": fsm.get_transitions_disponibles()
        })
    return resultat


# ============================================================
# INTERVENTIONS
# ============================================================

def charger_intervention(intervention_id: int) -> InterventionFSM:
    """
    Reconstitue l'état d'une intervention depuis la DB.
    La DB ne stocke pas directement l'état FSM, on le déduit :
      - date_heure_fin = NULL → en cours
      - date_heure_fin != NULL → TERMINE
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id_intervention, id_capteur, date_heure_fin FROM INTERVENTION WHERE id_intervention = %s",
        (intervention_id,)
    )
    row = cursor.fetchone()

    # Compte le nombre de techniciens associés
    cursor.execute(
        "SELECT COUNT(*) as nb FROM INTERVENTION_TECHNICIEN WHERE id_intervention = %s",
        (intervention_id,)
    )
    nb_tech = cursor.fetchone()['nb']
    conn.close()

    if not row:
        raise ValueError(f"Intervention {intervention_id} non trouvée")

    fsm = InterventionFSM(intervention_id=intervention_id, capteur_id=row['id_capteur'])

    # Reconstitution de l'état basée sur les données DB
    if row['date_heure_fin'] is not None:
        # Simulation rapide pour arriver à l'état TERMINE
        fsm.machine.set_state('TERMINE')
    elif nb_tech >= 2:
        fsm.machine.set_state('TECH2_VALIDE')
    elif nb_tech == 1:
        fsm.machine.set_state('TECH1_ASSIGNE')
    # Sinon reste à DEMANDE

    return fsm


def get_statut_interventions_en_cours() -> list:
    """Retourne les interventions sans date de fin (encore en cours)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.id_intervention, i.id_capteur, i.nature, i.date_heure_debut,
               COUNT(it.id_technicien) as nb_techniciens
        FROM INTERVENTION i
        LEFT JOIN INTERVENTION_TECHNICIEN it ON i.id_intervention = it.id_intervention
        WHERE i.date_heure_fin IS NULL
        GROUP BY i.id_intervention
        ORDER BY i.date_heure_debut DESC
    """)
    interventions = cursor.fetchall()
    conn.close()

    resultat = []
    for inter in interventions:
        nb = inter['nb_techniciens']
        if nb == 0:
            etat = 'DEMANDE'
        elif nb == 1:
            etat = 'TECH1_ASSIGNE'
        else:
            etat = 'TECH2_VALIDE'

        resultat.append({
            "id": inter['id_intervention'],
            "capteur_id": inter['id_capteur'],
            "nature": inter['nature'],
            "debut": str(inter['date_heure_debut']),
            "etat_fsm": etat,
            "nb_techniciens": nb
        })
    return resultat


# ============================================================
# VÉHICULES
# ============================================================

def get_statut_vehicules() -> list:
    """
    Déduit l'état des véhicules depuis les trajets en DB :
    - Si un trajet a depart mais pas d'arrivee → EN_ROUTE
    - Sinon → STATIONNE
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.id_vehicule, v.plaque_immatriculation, v.type_vehicule,
               t.id_trajet, t.origine, t.destination, t.date_heure_arrivee
        FROM VEHICULE_AUTONOME v
        LEFT JOIN TRAJET t ON v.id_vehicule = t.id_vehicule
            AND t.date_heure_depart = (
                SELECT MAX(date_heure_depart) FROM TRAJET WHERE id_vehicule = v.id_vehicule
            )
    """)
    vehicules = cursor.fetchall()
    conn.close()

    resultat = []
    for v in vehicules:
        if v['id_trajet'] and v['date_heure_arrivee'] is None:
            etat = 'EN_ROUTE'
            fsm = VehiculeFSM(v['id_vehicule'], v['plaque_immatriculation'])
            fsm.machine.set_state('EN_ROUTE')
        else:
            etat = 'STATIONNE'
            fsm = VehiculeFSM(v['id_vehicule'], v['plaque_immatriculation'])

        resultat.append({
            "id": v['id_vehicule'],
            "plaque": v['plaque_immatriculation'],
            "type": v['type_vehicule'],
            "etat": etat,
            "destination": v.get('destination'),
            "transitions_disponibles": fsm.machine.get_triggers(fsm.state)
        })
    return resultat


# ============================================================
# POINT D'ENTRÉE GLOBAL — utilisé par GET /automates/status
# ============================================================

def get_statut_global() -> dict:
    """
    Retourne un résumé complet de tous les automates.
    C'est ce que ton ami appellera depuis son endpoint FastAPI.
    """
    return {
        "capteurs": get_statut_tous_capteurs(),
        "interventions_en_cours": get_statut_interventions_en_cours(),
        "vehicules": get_statut_vehicules(),
    }


# ── TEST ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== TEST MANAGER ===\n")

    print("--- Statut global ---")
    statut = get_statut_global()
    print(f"Capteurs chargés    : {len(statut['capteurs'])}")
    print(f"Interventions actives: {len(statut['interventions_en_cours'])}")
    print(f"Véhicules           : {len(statut['vehicules'])}")

    print("\n--- Test événement sur C-001 ---")
    # Essaie d'installer le capteur C-001 (marche seulement s'il est INACTIF)
    result = appliquer_evenement_capteur("C-001", "installer")
    print(result)