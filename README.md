# Smart City Neo-Sousse 2030

Plateforme de supervision pour une ville intelligente fictive, **Neo-Sousse 2030**. Elle permet aux gestionnaires urbains de suivre les capteurs de la ville, les interventions techniques, les véhicules autonomes et la participation citoyenne, d'**interroger la base de données en français** et de **générer des rapports d'analyse par IA**.

<!-- Ajouter une capture du tableau de bord : docs/dashboard.png -->

## Fonctionnalités

| Module | Rôle |
|---|---|
| **Compilateur NL → SQL** | Traduit une question en français en requête SQL (analyse lexicale, syntaxique, génération de code) |
| **Automates à états finis** | Modélisent et valident le cycle de vie des capteurs, des interventions et des véhicules autonomes |
| **Base de données** | Schéma relationnel MySQL de 11 tables + génération de données réalistes sur 90 jours |
| **IA générative** | Génère des rapports d'analyse urbaine en français à partir des données |
| **API REST** | Expose tous les modules via FastAPI |
| **Tableau de bord** | Interface Streamlit avec graphiques Plotly |

## Architecture

```
                    ┌──────────────────────────────┐
                    │  Tableau de bord Streamlit   │
                    │  (frontend/app.py)           │
                    └──────────────┬───────────────┘
                                   │ HTTP
                    ┌──────────────▼───────────────┐
                    │        API FastAPI           │
                    │        (api/main.py)         │
                    └──┬────────────┬───────────┬──┘
                       │            │           │
          ┌────────────▼──┐  ┌──────▼──────┐  ┌─▼────────────────┐
          │ Compilateur   │  │ Automates   │  │ Générateur de    │
          │ NL → SQL      │  │ (transitions)│  │ rapports IA      │
          │ (PLY + regex) │  │             │  │ (LangChain + HF) │
          └───────┬───────┘  └──────┬──────┘  └────────┬─────────┘
                  └─────────────────┼──────────────────┘
                           ┌────────▼────────┐
                           │  MySQL          │
                           │  smart_city     │
                           └─────────────────┘
```

## 1. Compilateur langage naturel → SQL

Le compilateur suit les étapes classiques d'un compilateur :

```
"Combien de capteurs sont hors service ?"
        │
        ▼  Lexer (PLY)       → COMBIEN DE CAPTEURS SONT HORS_SERVICE
        ▼  Parser (PLY)      → arbre syntaxique {action: count, entite: capteurs, statut: HORS_SERVICE}
        ▼  Génération SQL    → SELECT COUNT(*) FROM CAPTEUR WHERE statut = 'HORS_SERVICE';
```

- **Lexer** (`compiler/lexer.py`) : découpe la phrase en tokens (verbes, entités, statuts, attributs, quantificateurs, nombres).
- **Parser** (`compiler/parser.py`) : grammaire formelle qui reconnaît une dizaine de formes de requêtes (affichage, filtre par statut, top N, comptage, comptage sur la semaine, conditions sur un score…).
- **Fallback regex** (`compiler/fallback.py`) : si la phrase sort de la grammaire, un analyseur par expressions régulières (insensible aux accents et à la ponctuation) prend le relais.
- **Génération de code** (`compiler/codegen.py`) : produit la requête SQL à partir de l'arbre, quel que soit l'analyseur utilisé.

**Exemples de requêtes :**
- *Affiche les 5 zones les plus polluées*
- *Combien de capteurs sont hors service ?*
- *Quels citoyens ont un score écologique supérieur à 80 ?*

## 2. Automates à états finis

Implémentés avec la bibliothèque [`transitions`](https://github.com/pytransitions/transitions) : toute transition non autorisée est refusée, ce qui garantit la cohérence des états.

**Cycle de vie d'un capteur** (`automaton/capteur_fsm.py`)
```
INACTIF ──installer──► ACTIF ──detecter_anomalie──► SIGNALE ──assigner_technicien──► EN_MAINTENANCE
           ◄──desactiver──┘  ◄────────────────────── reparer ─────────────────────────────┘
                                                                     panne_critique │
                                                                                    ▼
                                                                              HORS_SERVICE
```

**Validation d'une intervention** (`automaton/intervention_fsm.py`) — double validation humaine puis validation par l'IA
```
DEMANDE ──► TECH1_ASSIGNE ──► TECH2_VALIDE ──► IA_VALIDE ──► TERMINE
   └──────────────┴────────────────┴──────────────┴──annuler──► ANNULE
```

**Trajet d'un véhicule autonome** (`automaton/vehicule_fsm.py`)
```
STATIONNE ──demarrer──► EN_ROUTE ──arriver──► ARRIVE ──stationner──► STATIONNE
                           │ panne
                           ▼
                        EN_PANNE ──reparer──► STATIONNE
```

## 3. Base de données

Schéma MySQL (`database/schema.sql`) de 11 tables :

- **Entités** : `CAPTEUR`, `MESURE_CAPTEUR`, `INTERVENTION`, `TECHNICIEN`, `VEHICULE_AUTONOME`, `TRAJET`, `CITOYEN`, `PROPRIETAIRE`, `CONSULTATION_CITOYENNE`
- **Tables de liaison** : `INTERVENTION_TECHNICIEN`, `PARTICIPATION`

Le script `database/generate_data.py` remplit la base avec des données réalistes (Faker) et des séries temporelles de mesures sur 90 jours.

## 4. Rapports par IA générative

`ia/report_generator.py` utilise **LangChain** et un LLM hébergé sur **Hugging Face** (`openai/gpt-oss-20b`) pour produire des rapports professionnels en français, orientés vers des actions concrètes pour les gestionnaires urbains.

## API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | Vérifie que l'API fonctionne |
| `GET` | `/capteurs` | Liste des capteurs |
| `POST` | `/compile` | Compile une question en SQL et renvoie les résultats |
| `GET` | `/automates/status` | État de tous les automates |
| `POST` | `/automates/{type}/{id}/transition` | Applique un événement à un automate |
| `POST` | `/rapport` | Génère un rapport d'analyse par IA |

La documentation interactive est disponible sur `http://localhost:8000/docs` une fois l'API lancée.

## Structure du projet

```
SmartCity-NeoSousse-2030/
├── api/main.py              # API FastAPI
├── automaton/               # Automates : capteur, intervention, véhicule + gestionnaire
├── compiler/                # Lexer, parser, fallback regex, génération SQL
├── database/                # Schéma SQL et génération de données
├── frontend/app.py          # Tableau de bord Streamlit
├── ia/report_generator.py   # Génération de rapports par LLM
├── requirements.txt
└── .env.exemple
```

## Installation et lancement

**Prérequis :** Python 3.10+, MySQL 8, une clé API Hugging Face.

```bash
# 1. Cloner le projet
git clone https://github.com/ghofrane153/SmartCity-NeoSousse-2030.git
cd SmartCity-NeoSousse-2030

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'environnement
cp .env.exemple .env      # puis renseigner le mot de passe MySQL et HUGGINGFACE_API_KEY

# 4. Créer et remplir la base
mysql -u root -p < database/schema.sql
python database/generate_data.py

# 5. Lancer l'API (depuis la racine du projet)
uvicorn api.main:app --reload

# 6. Lancer le tableau de bord (dans un second terminal)
streamlit run frontend/app.py
```

## Technologies

Python · PLY · transitions · FastAPI · MySQL · LangChain · Hugging Face · Streamlit · Plotly · Pandas · Faker

## Auteurs

Projet réalisé en binôme.

- **Ghofrane Kerkeni** — [LinkedIn](https://www.linkedin.com/in/VOTRE-PROFIL) · [GitHub](https://github.com/ghofrane153)

