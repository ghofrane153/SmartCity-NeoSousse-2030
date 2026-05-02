"""
capteur_fsm.py
==============
Automate à États Finis — Cycle de vie d'un capteur urbain

COMMENT ÇA MARCHE (transitions library) :
  - On définit une liste d'ÉTATS possibles
  - On définit des TRANSITIONS : (trigger, état_source, état_destination)
  - La lib gère automatiquement les règles : si tu essaies une transition
    non autorisée, elle lève une exception → c'est ça la validation !

DIAGRAMME :
                  installation
    INACTIF ──────────────────────► ACTIF
                                      │
                          anomalie     │      réparation
                         ┌────────────┘◄──────────────┐
                         ▼                             │
                      SIGNALÉ ──────────────► EN_MAINTENANCE
                                  assignation          │
                                                       │ panne
                                                       ▼
                                                  HORS_SERVICE
"""

from transitions import Machine


class CapteurFSM:
    """
    Représente l'état d'un capteur dans la ville.
    Chaque instance gère UN capteur identifié par son id.
    """

    # ── 1. Définition des états ──────────────────────────────────────
    STATES = [
        'INACTIF',          # Capteur installé mais pas encore activé
        'ACTIF',            # Capteur fonctionnel, envoie des mesures
        'SIGNALE',          # Anomalie détectée, nécessite attention
        'EN_MAINTENANCE',   # Technicien en train de travailler dessus
        'HORS_SERVICE',     # Capteur mort, ne peut plus être réparé
    ]

    # ── 2. Définition des transitions ────────────────────────────────
    # Format : {'trigger': 'nom_evenement', 'source': 'etat_depart', 'dest': 'etat_arrivee'}
    TRANSITIONS = [
        # Événement : installation → le capteur devient actif
        {'trigger': 'installer',      'source': 'INACTIF',        'dest': 'ACTIF'},

        # Événement : anomalie détectée par le système
        {'trigger': 'detecter_anomalie', 'source': 'ACTIF',       'dest': 'SIGNALE'},

        # Événement : un technicien est assigné pour réparer
        {'trigger': 'assigner_technicien', 'source': 'SIGNALE',   'dest': 'EN_MAINTENANCE'},

        # Événement : réparation réussie → retour à l'état actif
        {'trigger': 'reparer',        'source': 'EN_MAINTENANCE',  'dest': 'ACTIF'},

        # Événement : panne irréparable pendant la maintenance
        {'trigger': 'panne_critique', 'source': 'EN_MAINTENANCE',  'dest': 'HORS_SERVICE'},

        # Événement : désactivation volontaire (depuis ACTIF)
        {'trigger': 'desactiver',     'source': 'ACTIF',           'dest': 'INACTIF'},
    ]

    def __init__(self, capteur_id: str, etat_initial: str = 'INACTIF'):
        self.capteur_id = capteur_id
        self.historique = []   # Garde en mémoire tous les changements d'état

        # La Machine gère tout : elle ajoute les méthodes trigger automatiquement
        # Ex: self.installer() sera disponible grâce à la Machine
        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial=etat_initial,
            auto_transitions=False,  # Désactive les transitions automatiques non définies
        )
        
        # Enregistrer les callbacks pour chaque état
        self.machine.add_states(
            [
                {'name': 'SIGNALE', 'on_enter': self._alerte_signalement},
                {'name': 'HORS_SERVICE', 'on_enter': self._alerte_hors_service},
            ]
        )

    # ── 3. Callbacks (actions automatiques lors des transitions) ─────

    def _alerte_signalement(self):
        """Déclenchée automatiquement quand le capteur passe en SIGNALÉ"""
        msg = f"⚠️  ALERTE : Capteur {self.capteur_id} vient d'être SIGNALÉ — intervention recommandée"
        print(msg)
        self.historique.append({'etat': 'SIGNALE', 'alerte': msg})

    def _alerte_hors_service(self):
        """Déclenchée automatiquement quand le capteur tombe HORS SERVICE"""
        msg = f"🔴 CRITIQUE : Capteur {self.capteur_id} est HORS SERVICE — remplacement nécessaire"
        print(msg)
        self.historique.append({'etat': 'HORS_SERVICE', 'alerte': msg})

    # ── 4. Méthodes utilitaires ──────────────────────────────────────

    def appliquer_evenement(self, evenement: str) -> dict:
        """
        Tente d'appliquer un événement et retourne le résultat.
        Utilisé par l'API FastAPI de ton ami.
        
        Retourne: {"succes": bool, "ancien_etat": str, "nouvel_etat": str, "erreur": str}
        """
        ancien_etat = self.state
        try:
            # getattr permet d'appeler dynamiquement la méthode par son nom
            trigger = getattr(self, evenement)
            trigger()
            self.historique.append({'evenement': evenement, 'de': ancien_etat, 'vers': self.state})
            return {
                "succes": True,
                "capteur_id": self.capteur_id,
                "ancien_etat": ancien_etat,
                "nouvel_etat": self.state,
                "erreur": None
            }
        except Exception as e:
            return {
                "succes": False,
                "capteur_id": self.capteur_id,
                "ancien_etat": ancien_etat,
                "nouvel_etat": ancien_etat,  # Pas changé
                "erreur": f"Transition '{evenement}' non autorisée depuis l'état '{ancien_etat}'"
            }

    def get_transitions_disponibles(self) -> list:
        """Retourne les événements possibles depuis l'état actuel"""
        return self.machine.get_triggers(self.state)

    def to_dict(self) -> dict:
        """Sérialise l'état courant pour l'API"""
        return {
            "capteur_id": self.capteur_id,
            "etat": self.state,
            "transitions_disponibles": self.get_transitions_disponibles(),
            "historique": self.historique
        }


# ── TABLE DE TRANSITION (pour le rapport du prof) ─────────────────
TABLE_TRANSITION_CAPTEUR = """
╔══════════════════╦═══════════════════╦══════════════════╦════════════════╗
║  État Actuel     ║  Événement        ║  État Suivant    ║  Action        ║
╠══════════════════╬═══════════════════╬══════════════════╬════════════════╣
║  INACTIF         ║  installer        ║  ACTIF           ║  -             ║
║  ACTIF           ║  detecter_anomalie║  SIGNALE         ║  Alerte email  ║
║  ACTIF           ║  desactiver       ║  INACTIF         ║  -             ║
║  SIGNALE         ║  assigner_tech    ║  EN_MAINTENANCE  ║  -             ║
║  EN_MAINTENANCE  ║  reparer          ║  ACTIF           ║  -             ║
║  EN_MAINTENANCE  ║  panne_critique   ║  HORS_SERVICE    ║  Alerte CRIT.  ║
╚══════════════════╩═══════════════════╩══════════════════╩════════════════╝
"""


# ── TEST RAPIDE ───────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== TEST AUTOMATE CAPTEUR ===\n")
    print(TABLE_TRANSITION_CAPTEUR)

    c = CapteurFSM("C-001", etat_initial="INACTIF")
    print(f"État initial : {c.state}")
    print(f"Transitions disponibles : {c.get_transitions_disponibles()}\n")

    # Scénario normal
    print("--- Scénario : installation puis anomalie ---")
    print(c.appliquer_evenement("installer"))
    print(c.appliquer_evenement("detecter_anomalie"))
    print(c.appliquer_evenement("assigner_technicien"))
    print(c.appliquer_evenement("reparer"))

    print(f"\nÉtat final : {c.state}")

    # Test transition invalide
    print("\n--- Test transition INVALIDE ---")
    result = c.appliquer_evenement("panne_critique")  # Pas possible depuis ACTIF
    print(result)