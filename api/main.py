# api/main.py
# ============================================================
# BACKEND FASTAPI — Smart City Neo-Sousse 2030
# ============================================================

from fastapi import FastAPI
import mysql.connector
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from compiler.compiler import compile_nl_to_sql
from ia.report_generator import ReportGenerator
from automaton.manager import get_statut_global

# ── Charge le .env ───────────────────────────────────────────
load_dotenv()

# ── Initialise l'app FastAPI ─────────────────────────────────
app = FastAPI(title="Smart City Neo-Sousse 2030")

# ── Initialise le générateur IA avec protection ──────────────
# Si HuggingFace est indispo au démarrage → l'app continue quand même
try:
    report_gen = ReportGenerator()
    print("✅ ReportGenerator IA prêt")
except Exception as e:
    report_gen = None
    print(f"⚠️  ReportGenerator indisponible : {e}")


# ============================================================
# 🔌 CONNEXION MYSQL
# ============================================================
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Test de connexion au démarrage
try:
    conn = get_connection()
    if conn.is_connected():
        print("✅ Connexion MySQL OK")
        conn.close()
except Exception as e:
    print(f"⚠️  MySQL indisponible : {e} → mock data activé")


# ============================================================
# 📋 MODÈLES PYDANTIC
# ============================================================
class QueryBody(BaseModel):
    query: str

class RapportBody(BaseModel):
    type: str   # "general" | "capteurs" | "interventions"


# ============================================================
# 📡 MOCK DATA (fallback si DB absente)
# ============================================================
MOCK_CAPTEURS = [
    {"id_capteur": 1, "type_capteur": "pollution", "statut": "actif",         "zone": "A1"},
    {"id_capteur": 2, "type_capteur": "co2",       "statut": "hors_service",  "zone": "B3"},
    {"id_capteur": 3, "type_capteur": "bruit",     "statut": "en_maintenance","zone": "C2"},
]

MOCK_RESULTS = [
    {"id_capteur": 1, "type_capteur": "pollution", "statut": "actif",         "zone": "A1"},
    {"id_capteur": 2, "type_capteur": "co2",       "statut": "hors_service",  "zone": "B3"},
    {"id_capteur": 3, "type_capteur": "bruit",     "statut": "en_maintenance","zone": "C2"},
]

MOCK_STATS = {
    "nb_capteurs_actifs":        42,
    "nb_capteurs_total":         50,
    "nb_interventions_en_cours":  3,
    "nb_alertes":                 5,
    "zone_plus_polluee":         "Zone B3",
    "nb_vehicules_disponibles":  12
}


# ============================================================
# ❤️ GET /health
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# 📊 GET /capteurs
# ============================================================
@app.get("/capteurs")
def get_capteurs():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM CAPTEUR")
        return cursor.fetchall()
    except Exception as e:
        print(f"⚠️  /capteurs → mock activé : {e}")
        return MOCK_CAPTEURS
    finally:
        if conn:
            conn.close()


# ============================================================
# 🤖 GET /automates/status
# ============================================================
@app.get("/automates/status")
def get_automates_status():
    try:
        return get_statut_global()
    except Exception as e:
        print(f"⚠️  /automates/status → mock activé : {e}")
        return {
            "capteurs": [
                {"id": "C-001", "type": "pollution", "zone": "A1",
                 "etat": "ACTIF", "transitions_disponibles": ["detecter_anomalie", "desactiver"]}
            ],
            "interventions_en_cours": [
                {"id": 1, "capteur_id": "C-001", "nature": "CALIBRATION",
                 "debut": "2026-05-01 08:00", "etat_fsm": "DEMANDE", "nb_techniciens": 0}
            ],
            "vehicules": [
                {"id": 1, "plaque": "NS-001-AUTO", "type": "BUS",
                 "etat": "STATIONNE", "destination": None,
                 "transitions_disponibles": ["demarrer"]}
            ]
        }


# ============================================================
# 🧠 POST /compile
# ============================================================
@app.post("/compile")
def compile_query(body: QueryBody):
    conn = None
    try:
        # Étape 1 : NL → SQL via le compilateur
        result = compile_nl_to_sql(body.query)

        if result.get("error"):
            return {
                "sql":     None,
                "results": [],
                "error":   result["error"]
            }

        sql = result["sql"]

        # Étape 2 : Exécute le SQL sur la DB
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            return {
                "sql":     sql,
                "results": rows,
                "error":   None
            }
        except Exception as db_error:
            print(f"⚠️  /compile DB indispo → mock : {db_error}")
            return {
                "sql":     sql,
                "results": MOCK_RESULTS,
                "error":   None
            }

    except Exception as e:
        return {
            "sql":     None,
            "results": [],
            "error":   str(e)
        }
    finally:
        if conn:
            conn.close()

class TransitionBody(BaseModel):
    evenement: str

@app.post("/automates/{entite_type}/{entite_id}/transition")
def appliquer_transition(entite_type: str, entite_id: str, body: TransitionBody):
    try:
        from automaton.manager import appliquer_evenement_capteur
        if entite_type == "capteur":
            return appliquer_evenement_capteur(entite_id, body.evenement)
        else:
            return {"succes": False, "erreur": f"Type '{entite_type}' non supporté encore"}
    except Exception as e:
        return {"succes": False, "erreur": str(e)}
# ============================================================
# 📝 POST /rapport  ← compatible HuggingFace
# ============================================================
@app.post("/rapport")
def generer_rapport(body: RapportBody):

    if report_gen is None:
        return {
            "rapport": (
                "⚠️ Module IA indisponible. "
                "Vérifiez HUGGINGFACE_API_KEY dans le fichier .env"
            )
        }

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # ── Rapport général ───────────────────────────────────
        if body.type == "general":
            cursor.execute("SELECT COUNT(*) as total FROM CAPTEUR WHERE statut='ACTIF'")
            nb_actifs = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM CAPTEUR")
            nb_total = cursor.fetchone()["total"]

            # Interventions en cours = date_heure_fin IS NULL
            cursor.execute("SELECT COUNT(*) as total FROM INTERVENTION WHERE date_heure_fin IS NULL")
            nb_interventions = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM CAPTEUR WHERE statut='SIGNALE'")
            nb_alertes = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM VEHICULE_AUTONOME")
            nb_vehicules = cursor.fetchone()["total"]

            stats = {
                "nb_capteurs_actifs":        nb_actifs,
                "nb_capteurs_total":         nb_total,
                "nb_interventions_en_cours": nb_interventions,
                "nb_alertes":                nb_alertes,
                "zone_plus_polluee":         "Calculée depuis DB",
                "nb_vehicules_disponibles":  nb_vehicules
            }
            rapport = report_gen.generate_general_report(stats)

        # ── Rapport capteurs ──────────────────────────────────
        elif body.type == "capteurs":
            cursor.execute("SELECT * FROM CAPTEUR WHERE statut != 'ACTIF' LIMIT 1")
            capteur = cursor.fetchone()
            if capteur:
                rapport = report_gen.generate_capteur_alert(capteur)
            else:
                rapport = "✅ Tous les capteurs sont opérationnels."

        # ── Rapport interventions ─────────────────────────────
        elif body.type == "interventions":
            cursor.execute("SELECT zone FROM CAPTEUR LIMIT 1")
            row  = cursor.fetchone()
            zone = row["zone"] if row else "ZONE_NORD"

            # ✅ Correction : timestamp_mesure (pas date_heure)
            cursor.execute("""
                SELECT mc.valeur, c.zone, mc.timestamp_mesure
                FROM MESURE_CAPTEUR mc
                JOIN CAPTEUR c USING(id_capteur)
                WHERE c.zone = %s
                ORDER BY mc.timestamp_mesure DESC
                LIMIT 5
            """, (zone,))
            mesures_raw = cursor.fetchall()

            mesures = [
                {
                    "type":       "mesure",
                    "valeur":     m["valeur"],
                    "date_heure": str(m["timestamp_mesure"]),
                    "seuil_max":  200
                }
                for m in mesures_raw
            ]
            rapport = report_gen.suggest_intervention(zone, mesures)

        else:
            return {"rapport": "❌ Type non reconnu. Utilisez : general | capteurs | interventions"}

        return {"rapport": rapport}

    except Exception as e:
        print(f"⚠️  /rapport DB indispo → mock stats : {e}")
        try:
            rapport = report_gen.generate_general_report(MOCK_STATS)
            return {"rapport": rapport}
        except Exception as ia_error:
            return {"rapport": f"⚠️ IA et DB indisponibles : {ia_error}"}

    finally:
        if conn:
            conn.close()