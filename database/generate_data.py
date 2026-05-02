"""
generate_data.py
================
Ce script remplit la base de données avec des données réalistes.

COMMENT ÇA MARCHE :
- On utilise 'faker' pour générer des noms, adresses, etc. faux mais réalistes
- On génère des séries temporelles sur 90 jours pour les mesures
- L'ordre d'insertion respecte les FK (mêmes règles que le schema.sql)

AVANT DE LANCER :
    pip install faker mysql-connector-python

LANCER :
    python generate_data.py
"""

import mysql.connector
import random
from datetime import datetime, timedelta, date
from faker import Faker

# ---- Configuration ----
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",       # ← change si ton mot de passe MySQL est différent
    "database": "smart_city"
}

fake = Faker('fr_FR')          # Faker en français (noms, adresses tunisiens-style)
random.seed(42)                 # Graine fixe = résultats reproductibles
Faker.seed(42)

# ---- Connexion ----
print("Connexion à la base de données...")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
print("✓ Connecté !\n")

# ---- Nettoyage des anciennes données ----
print("Nettoyage des anciennes données...")
try:
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute("TRUNCATE TABLE PARTICIPATION")
    cursor.execute("TRUNCATE TABLE CONSULTATION_CITOYENNE")
    cursor.execute("TRUNCATE TABLE TRAJET")
    cursor.execute("TRUNCATE TABLE VEHICULE_AUTONOME")
    cursor.execute("TRUNCATE TABLE INTERVENTION_TECHNICIEN")
    cursor.execute("TRUNCATE TABLE INTERVENTION")
    cursor.execute("TRUNCATE TABLE TECHNICIEN")
    cursor.execute("TRUNCATE TABLE MESURE_CAPTEUR")
    cursor.execute("TRUNCATE TABLE CAPTEUR")
    cursor.execute("TRUNCATE TABLE PROPRIETAIRE")
    cursor.execute("TRUNCATE TABLE CITOYEN")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    print("✓ Tables vidées !\n")
except Exception as e:
    print(f"⚠ Erreur lors du nettoyage (tables vides?): {e}\n")

# ============================================================
# ÉTAPE 1 — PROPRIÉTAIRES (20 entrées)
# ============================================================
print("Insertion des propriétaires...")

types_proprietaire = ['ENTREPRISE', 'MUNICIPALITE', 'PARTICULIER', 'ONG']
proprietaires = []

for i in range(20):
    nom = fake.company() if random.random() > 0.3 else fake.last_name()
    type_p = random.choice(types_proprietaire)
    proprietaires.append((
        nom,
        fake.address().replace('\n', ', '),
        fake.phone_number(),
        fake.email(),
        type_p
    ))

cursor.executemany(
    "INSERT INTO PROPRIETAIRE (nom_proprietaire, adresse, telephone, email, type_proprietaire) VALUES (%s, %s, %s, %s, %s)",
    proprietaires
)
conn.commit()
print(f"  ✓ {len(proprietaires)} propriétaires insérés")

# ============================================================
# ÉTAPE 2 — CAPTEURS (100 capteurs dans 5 zones)
# ============================================================
print("Insertion des capteurs...")

# Les zones correspondent à des quartiers de Sousse
zones = ['ZONE_NORD', 'CENTRE_VILLE', 'ZONE_INDUSTRIELLE', 'ZONE_SUD', 'ZONE_PORTUAIRE']
types_capteur = ['POLLUTION', 'BRUIT', 'TRAFIC', 'TEMPERATURE', 'HUMIDITE', 'RADIATION']

# Coordonnées GPS centrées sur Sousse, Tunisie
BASE_LAT = 35.8256
BASE_LON = 10.6369

# Distribution réaliste des statuts (la majorité est ACTIF)
statuts_distribution = (
    ['ACTIF'] * 55 +
    ['INACTIF'] * 15 +
    ['SIGNALE'] * 15 +
    ['EN_MAINTENANCE'] * 10 +
    ['HORS_SERVICE'] * 5
)

capteurs = []
for i in range(1, 101):
    capteur_id = f"C-{i:03d}"       # C-001, C-002, ..., C-100
    capteurs.append((
        capteur_id,
        random.choice(types_capteur),
        BASE_LAT + random.uniform(-0.05, 0.05),
        BASE_LON + random.uniform(-0.05, 0.05),
        random.choice(statuts_distribution),
        random.choice(zones),
        random.randint(1, 20)        # id_proprietaire
    ))

cursor.executemany(
    "INSERT INTO CAPTEUR (id_capteur, type_capteur, latitude, longitude, statut, zone, id_proprietaire) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    capteurs
)
conn.commit()
print(f"  ✓ {len(capteurs)} capteurs insérés")

# ============================================================
# ÉTAPE 3 — MESURES (séries temporelles sur 90 jours)
# Environ 10-15 mesures par capteur actif = ~1200 mesures total
# ============================================================
print("Insertion des mesures (ça peut prendre quelques secondes)...")

# Paramètres par type de capteur (valeur_min, valeur_max, unité)
params_capteur = {
    'POLLUTION':    (5.0,  150.0,  'µg/m³'),
    'BRUIT':        (30.0,  95.0,  'dB'),
    'TRAFIC':       (10.0, 500.0,  'véh/h'),
    'TEMPERATURE':  (15.0,  40.0,  '°C'),
    'HUMIDITE':     (20.0,  95.0,  '%'),
    'RADIATION':     (0.1,   5.0,  'mSv/h'),
}

mesures = []
date_debut = datetime.now() - timedelta(days=90)

# Seulement les capteurs ACTIF ou SIGNALE génèrent des mesures
capteurs_actifs = [c for c in capteurs if c[4] in ('ACTIF', 'SIGNALE')]

for capteur in capteurs_actifs:
    capteur_id = capteur[0]
    type_c = capteur[1]
    vmin, vmax, unite = params_capteur[type_c]
    
    # 10 à 15 mesures par capteur, réparties sur 90 jours
    nb_mesures = random.randint(10, 15)
    for _ in range(nb_mesures):
        ts = date_debut + timedelta(
            days=random.uniform(0, 90),
            hours=random.uniform(0, 24)
        )
        valeur = round(random.uniform(vmin, vmax), 2)
        mesures.append((ts, valeur, unite, capteur_id))

# Insertion par batch de 500 pour aller plus vite
batch_size = 500
for i in range(0, len(mesures), batch_size):
    batch = mesures[i:i+batch_size]
    cursor.executemany(
        "INSERT INTO MESURE_CAPTEUR (timestamp_mesure, valeur, unite, id_capteur) VALUES (%s, %s, %s, %s)",
        batch
    )
conn.commit()
print(f"  ✓ {len(mesures)} mesures insérées")

# ============================================================
# ÉTAPE 4 — TECHNICIENS (15 techniciens)
# ============================================================
print("Insertion des techniciens...")

certifications = ['ELEC_NIVEAU1', 'ELEC_NIVEAU2', 'RESEAU_AVANCE', 'IOT_CERTIFIE', 'MAINTENANCE_INDUSTRIELLE']
techniciens = []

for _ in range(15):
    techniciens.append((
        fake.last_name(),
        fake.first_name(),
        fake.phone_number(),
        fake.email(),
        random.choice(certifications)
    ))

cursor.executemany(
    "INSERT INTO TECHNICIEN (nom, prenom, telephone, email, certification) VALUES (%s, %s, %s, %s, %s)",
    techniciens
)
conn.commit()
print(f"  ✓ {len(techniciens)} techniciens insérés")

# ============================================================
# ÉTAPE 5 — INTERVENTIONS (40 interventions)
# ============================================================
print("Insertion des interventions...")

natures = ['REMPLACEMENT_CAPTEUR', 'CALIBRATION', 'REPARATION_URGENTE', 'MAINTENANCE_PREVENTIVE', 'MISE_A_JOUR_FIRMWARE']

# Seulement les capteurs en mauvais état ont des interventions
capteurs_problematiques = [c[0] for c in capteurs if c[4] in ('SIGNALE', 'EN_MAINTENANCE', 'HORS_SERVICE')]

interventions_ids = []
interventions = []

for i in range(40):
    debut = date_debut + timedelta(days=random.uniform(0, 85))
    duree_h = random.uniform(1, 8)
    fin = debut + timedelta(hours=duree_h) if random.random() > 0.15 else None  # 15% encore en cours

    capteur_id = random.choice(capteurs_problematiques) if capteurs_problematiques else capteurs[0][0]
    
    interventions.append((
        debut,
        fin,
        random.choice(natures),
        round(random.uniform(0.5, 5.0), 2),
        fake.sentence(nb_words=8),
        capteur_id
    ))

cursor.executemany(
    "INSERT INTO INTERVENTION (date_heure_debut, date_heure_fin, nature, impact_co2, commentaire, id_capteur) VALUES (%s, %s, %s, %s, %s, %s)",
    interventions
)
conn.commit()

# Récupère les IDs générés pour les lier aux techniciens
cursor.execute("SELECT id_intervention FROM INTERVENTION ORDER BY id_intervention DESC LIMIT 40")
interventions_ids = [row[0] for row in cursor.fetchall()]
print(f"  ✓ {len(interventions)} interventions insérées")

# ============================================================
# ÉTAPE 6 — LIAISON INTERVENTION_TECHNICIEN
# ============================================================
print("Association techniciens ↔ interventions...")

roles = ['RESPONSABLE', 'ASSISTANT', 'VALIDATEUR']
liens = set()

for inter_id in interventions_ids:
    # Chaque intervention a 1 à 3 techniciens
    nb_tech = random.randint(1, 3)
    techs_choisis = random.sample(range(1, 16), nb_tech)
    for j, tech_id in enumerate(techs_choisis):
        lien = (inter_id, tech_id)
        if lien not in liens:
            liens.add(lien)
            role = roles[j] if j < len(roles) else 'ASSISTANT'
            cursor.execute(
                "INSERT INTO INTERVENTION_TECHNICIEN VALUES (%s, %s, %s)",
                (inter_id, tech_id, role)
            )

conn.commit()
print(f"  ✓ {len(liens)} liens intervention-technicien créés")

# ============================================================
# ÉTAPE 7 — CITOYENS (200 citoyens)
# ============================================================
print("Insertion des citoyens...")

preferences = ['VELO', 'TRANSPORT_PUBLIC', 'VOITURE', 'MARCHE', 'MIXTE']
citoyens = []

for _ in range(200):
    citoyens.append((
        fake.last_name(),
        fake.first_name(),
        fake.address().replace('\n', ', '),
        fake.phone_number(),
        fake.email(),
        random.randint(0, 100),          # score_engagement
        random.choice(preferences)
    ))

cursor.executemany(
    "INSERT INTO CITOYEN (nom, prenom, adresse, telephone, email, score_engagement, preferences_mobilite) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    citoyens
)
conn.commit()
print(f"  ✓ {len(citoyens)} citoyens insérés")

# ============================================================
# ÉTAPE 8 — CONSULTATIONS CITOYENNES (10 consultations)
# ============================================================
print("Insertion des consultations...")

themes = ['MOBILITE', 'ENERGIE', 'SECURITE', 'ENVIRONNEMENT', 'URBANISME']
consultations = [
    ("Plan de mobilité 2030", "Discussion sur les nouvelles lignes de transport", date(2026, 3, 15), "MOBILITE"),
    ("Transition énergétique", "Objectifs énergies renouvelables Neo-Sousse", date(2026, 2, 20), "ENERGIE"),
    ("Sécurité routière", "Zones à risque et mesures préventives", date(2026, 1, 10), "SECURITE"),
    ("Qualité de l'air", "Plan d'action zones polluées", date(2026, 4, 5), "ENVIRONNEMENT"),
    ("Espaces verts", "Développement des parcs urbains", date(2026, 3, 28), "URBANISME"),
]
# 5 consultations générées dynamiquement
from datetime import date
for i in range(5):
    consultations.append((
        fake.sentence(nb_words=4),
        fake.paragraph(nb_sentences=2),
        date(2026, random.randint(1, 4), random.randint(1, 28)),
        random.choice(themes)
    ))

cursor.executemany(
    "INSERT INTO CONSULTATION_CITOYENNE (titre, description, date_consultation, theme) VALUES (%s, %s, %s, %s)",
    consultations
)
conn.commit()
print(f"  ✓ {len(consultations)} consultations insérées")

# ============================================================
# ÉTAPE 9 — PARTICIPATIONS (chaque citoyen participe à 1-5 consultations)
# ============================================================
print("Insertion des participations...")

participations = set()
for citoyen_num in range(1, 201):
    nb_participations = random.randint(1, 5)
    for _ in range(nb_participations):
        consult_id = random.randint(1, 10)
        participations.add((citoyen_num, consult_id))

cursor.executemany(
    "INSERT INTO PARTICIPATION VALUES (%s, %s)",
    list(participations)
)
conn.commit()
print(f"  ✓ {len(participations)} participations insérées")

# ============================================================
# ÉTAPE 10 — VÉHICULES AUTONOMES (20 véhicules)
# ============================================================
print("Insertion des véhicules autonomes...")

types_vehicule = ['BUS', 'NAVETTE', 'CAMION_COLLECTE', 'VOITURE_PARTAGE']
energies = ['ELECTRIQUE', 'HYBRIDE', 'HYDROGENE']
vehicules = []

for i in range(1, 21):
    vehicules.append((
        f"NS-{i:03d}-AUTO",
        random.choice(types_vehicule),
        random.choice(energies)
    ))

cursor.executemany(
    "INSERT INTO VEHICULE_AUTONOME (plaque_immatriculation, type_vehicule, energie) VALUES (%s, %s, %s)",
    vehicules
)
conn.commit()
print(f"  ✓ {len(vehicules)} véhicules insérés")

# ============================================================
# ÉTAPE 11 — TRAJETS (300 trajets)
# ============================================================
print("Insertion des trajets...")

points_ville = ['Gare Sousse', 'Aéroport', 'Port', 'Université', 'Marché Central',
                'Zone Industrielle', 'Hôpital', 'Centre Commercial', 'Plage', 'Stade']
trajets = []

for _ in range(300):
    origine, destination = random.sample(points_ville, 2)
    depart = date_debut + timedelta(days=random.uniform(0, 90), hours=random.uniform(6, 22))
    duree_min = random.randint(10, 90)
    arrivee = depart + timedelta(minutes=duree_min)

    trajets.append((
        origine,
        destination,
        depart,
        arrivee,
        duree_min,
        round(random.uniform(0.5, 8.0), 2),   # économie CO2 en kg
        random.randint(1, 20)                   # id_vehicule
    ))

cursor.executemany(
    "INSERT INTO TRAJET (origine, destination, date_heure_depart, date_heure_arrivee, duree, economie_co2, id_vehicule) VALUES (%s, %s, %s, %s, %s, %s, %s)",
    trajets
)
conn.commit()
print(f"  ✓ {len(trajets)} trajets insérés")

# ============================================================
# RÉSUMÉ FINAL
# ============================================================
cursor.close()
conn.close()

print("\n" + "="*50)
print("✅ BASE DE DONNÉES REMPLIE AVEC SUCCÈS !")
print("="*50)
print(f"  Propriétaires    : 20")
print(f"  Capteurs         : 100")
print(f"  Mesures          : {len(mesures)} (séries temporelles 90 jours)")
print(f"  Techniciens      : 15")
print(f"  Interventions    : 40")
print(f"  Citoyens         : 200")
print(f"  Consultations    : 10")
print(f"  Participations   : {len(participations)}")
print(f"  Véhicules        : 20")
print(f"  Trajets          : 300")
print(f"\n  TOTAL ~ {len(mesures) + 300 + 200 + 100 + 40} enregistrements")