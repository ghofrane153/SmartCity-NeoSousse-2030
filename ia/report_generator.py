# ia/report_generator.py
# ============================================================
# MODULE IA GÉNÉRATIVE — Génère des rapports avec HuggingFace
# ============================================================

import os
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import SystemMessage, HumanMessage

# Charge les variables d'environnement (.env)
load_dotenv()


class ReportGenerator:
    """
    Génère des rapports professionnels en français
    à partir des données urbaines de Neo-Sousse 2030.

    Utilise LangChain + HuggingFaceEndpoint (provider auto).
    """

    def __init__(self):
        """
        Initialise le client LangChain/HuggingFace avec :
        - La clé API depuis .env
        - Le prompt système fixe (contexte urbain)
        """

        # ── Clé API ──────────────────────────────────────────
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError(
                "HUGGINGFACE_API_KEY manquante dans le fichier .env"
            )

        # LangChain lit cette variable d'environnement automatiquement
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = api_key

        # ── Prompt système — utilisé pour TOUS les appels ────
        self.system_prompt = (
            "Tu es un système d'analyse urbaine pour la métropole "
            "Neo-Sousse 2030. Tu analyses des données de capteurs "
            "urbains et génères des rapports professionnels en français. "
            "Sois précis, concis, et oriente tes réponses vers des "
            "actions concrètes pour les gestionnaires urbains. "
            "Utilise un ton professionnel et structure tes réponses "
            "avec des points clés clairs."
        )

        # ── Endpoint HuggingFace ─────────────────────────────
        llm_endpoint = HuggingFaceEndpoint(
            repo_id="openai/gpt-oss-20b",
            task="text-generation",
            max_new_tokens=1024,
            do_sample=False,
            repetition_penalty=1.03,
            provider="auto",        # HF choisit le meilleur provider
        )

        # ── Wrapper Chat LangChain ───────────────────────────
        self.llm = ChatHuggingFace(llm=llm_endpoint)

        print("✅ ReportGenerator initialisé avec succès")


    # ══════════════════════════════════════════════════════════
    # MÉTHODE INTERNE — Appel unifié au modèle
    # ══════════════════════════════════════════════════════════

    def _call_api(self, prompt: str) -> str:
        """
        Envoie un prompt au modèle via LangChain.
        Utilise le format [SystemMessage, HumanMessage].
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content


    # ══════════════════════════════════════════════════════════
    # MÉTHODE 1 — Rapport général de la ville
    # ══════════════════════════════════════════════════════════

    def generate_general_report(self, stats: dict) -> str:
        """
        Génère un rapport général sur l'état de la ville.

        Paramètre stats (dict) attendu :
        {
            "nb_capteurs_actifs":       int,
            "nb_capteurs_total":        int,
            "nb_interventions_en_cours": int,
            "nb_alertes":               int,
            "zone_plus_polluee":        str,
            "nb_vehicules_disponibles": int
        }

        Retourne : str (rapport texte professionnel)
        """

        prompt = f"""
Génère un rapport exécutif complet pour les gestionnaires urbains
de Neo-Sousse 2030 basé sur ces données en temps réel :

ÉTAT DES CAPTEURS :
- Capteurs actifs    : {stats.get('nb_capteurs_actifs', 0)} / {stats.get('nb_capteurs_total', 0)}
- Alertes actives    : {stats.get('nb_alertes', 0)}

INTERVENTIONS :
- En cours           : {stats.get('nb_interventions_en_cours', 0)}

QUALITÉ DE L'AIR :
- Zone la plus polluée : {stats.get('zone_plus_polluee', 'Non disponible')}

MOBILITÉ :
- Véhicules disponibles : {stats.get('nb_vehicules_disponibles', 0)}

Le rapport doit inclure :
1. Résumé de la situation globale (2-3 phrases)
2. Points d'attention prioritaires
3. Actions recommandées pour les prochaines 24h
"""

        try:
            return self._call_api(prompt)
        except Exception as e:
            return (
                f"⚠️ Rapport de secours (API indisponible) :\n"
                f"Capteurs actifs : {stats.get('nb_capteurs_actifs', 0)}, "
                f"Interventions en cours : {stats.get('nb_interventions_en_cours', 0)}, "
                f"Alertes : {stats.get('nb_alertes', 0)}. "
                f"Erreur API : {str(e)}"
            )


    # ══════════════════════════════════════════════════════════
    # MÉTHODE 2 — Alerte pour un capteur problématique
    # ══════════════════════════════════════════════════════════

    def generate_capteur_alert(self, capteur_data: dict) -> str:
        """
        Génère une recommandation d'intervention pour un capteur
        problématique (en panne, signalé, hors service, etc.).

        Paramètre capteur_data (dict) attendu :
        {
            "id_capteur":   int,
            "type_capteur": str,   # "pollution", "co2", "bruit"
            "statut":       str,   # "signale", "hors_service", etc.
            "zone":         str,   # "A1", "B3", etc.
            "taux_erreur":  float,
            "derniere_val": float
        }

        Retourne : str (recommandation concrète)
        """

        prompt = f"""
Un capteur urbain nécessite une attention immédiate à Neo-Sousse 2030.

INFORMATIONS DU CAPTEUR :
- ID          : {capteur_data.get('id_capteur', 'Inconnu')}
- Type        : {capteur_data.get('type_capteur', 'Inconnu')}
- Statut      : {capteur_data.get('statut', 'Inconnu')}
- Zone        : {capteur_data.get('zone', 'Inconnue')}
- Taux erreur : {capteur_data.get('taux_erreur', 'N/A')} %
- Dernière valeur mesurée : {capteur_data.get('derniere_val', 'N/A')}

Génère une recommandation d'intervention qui inclut :
1. Diagnostic probable du problème
2. Niveau d'urgence (Faible / Moyen / Élevé / Critique)
3. Actions immédiates à effectuer
4. Délai d'intervention recommandé
"""

        try:
            return self._call_api(prompt)
        except Exception as e:
            return (
                f"⚠️ Alerte capteur {capteur_data.get('id_capteur')} "
                f"(zone {capteur_data.get('zone')}) : "
                f"statut '{capteur_data.get('statut')}'. "
                f"Intervention requise. Erreur API : {str(e)}"
            )


    # ══════════════════════════════════════════════════════════
    # MÉTHODE 3 — Suggestion d'intervention pour une zone
    # ══════════════════════════════════════════════════════════

    def suggest_intervention(self, zone: str, mesures: list) -> str:
        """
        Analyse les mesures d'une zone et suggère des actions.

        Paramètres :
        - zone    : str  → nom de la zone (ex: "A1", "B3")
        - mesures : list de dict avec type, valeur, date_heure, seuil_max

        Retourne : str (analyse + actions suggérées)
        """

        if not mesures:
            mesures_texte = "Aucune mesure disponible pour cette zone."
        else:
            lignes = []
            for m in mesures:
                seuil = m.get('seuil_max', 'N/A')
                ligne = (
                    f"  • {m.get('type','?'):12} : "
                    f"{m.get('valeur','?')} "
                    f"(seuil max: {seuil}) "
                    f"— {m.get('date_heure','?')}"
                )
                lignes.append(ligne)
            mesures_texte = "\n".join(lignes)

        prompt = f"""
Analyse des mesures environnementales pour la zone {zone}
de la métropole Neo-Sousse 2030 :

MESURES ENREGISTRÉES :
{mesures_texte}

Sur la base de ces données, génère :
1. Analyse de la situation environnementale de la zone
2. Identification des seuils dépassés (si applicable)
3. Risques pour les citoyens de la zone
4. Actions d'intervention recommandées (par ordre de priorité)
5. Mesures préventives pour éviter une dégradation future
"""

        try:
            return self._call_api(prompt)
        except Exception as e:
            return (
                f"⚠️ Analyse zone {zone} indisponible. "
                f"{len(mesures)} mesures enregistrées. "
                f"Erreur API : {str(e)}"
            )


# ── TEST AUTONOME ────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 60)
    print("   TEST MODULE IA — Neo-Sousse 2030")
    print("=" * 60)

    try:
        gen = ReportGenerator()
    except ValueError as e:
        print(f"❌ {e}")
        print("   → Vérifie que HUGGINGFACE_API_KEY est dans ton .env")
        exit(1)

    # ── TEST 1 : Rapport général ─────────────────────────────
    print("\n" + "─" * 60)
    print("TEST 1 — Rapport général")
    print("─" * 60)

    stats_mock = {
        "nb_capteurs_actifs":        42,
        "nb_capteurs_total":         50,
        "nb_interventions_en_cours":  3,
        "nb_alertes":                 5,
        "zone_plus_polluee":         "Zone B3",
        "nb_vehicules_disponibles":  12
    }

    rapport = gen.generate_general_report(stats_mock)
    print(rapport)

    # ── TEST 2 : Alerte capteur ──────────────────────────────
    print("\n" + "─" * 60)
    print("TEST 2 — Alerte capteur problématique")
    print("─" * 60)

    capteur_mock = {
        "id_capteur":   452,
        "type_capteur": "pollution",
        "statut":       "signale",
        "zone":         "B3",
        "taux_erreur":  15.3,
        "derniere_val": 287.5
    }

    alerte = gen.generate_capteur_alert(capteur_mock)
    print(alerte)

    # ── TEST 3 : Suggestion intervention zone ────────────────
    print("\n" + "─" * 60)
    print("TEST 3 — Suggestion intervention zone C2")
    print("─" * 60)

    mesures_mock = [
        {"type": "pollution", "valeur": 340.2, "seuil_max": 200.0, "date_heure": "2026-05-01 08:00"},
        {"type": "co2",       "valeur": 850.0, "seuil_max": 700.0, "date_heure": "2026-05-01 08:00"},
        {"type": "bruit",     "valeur":  72.0, "seuil_max":  65.0, "date_heure": "2026-05-01 08:05"},
    ]

    suggestion = gen.suggest_intervention("C2", mesures_mock)
    print(suggestion)

    print("\n" + "=" * 60)
    print("   ✅ Tous les tests terminés")
    print("=" * 60)