# compiler/codegen.py
# ============================================================
# CODE GENERATOR — Génère du SQL depuis un AST
# Adapté au schéma réel de la DB de ton binôme
# ============================================================

# ── MAPPING : entité NL → vraie table SQL ───────────────────
ENTITY_TABLE = {
    "capteurs":      "CAPTEUR",
    "interventions": "INTERVENTION",
    "citoyens":      "CITOYEN",
    "vehicules":     "VEHICULE_AUTONOME",
    "véhicules":     "VEHICULE_AUTONOME",
    "trajets":       "TRAJET",
    "mesures":       "MESURE_CAPTEUR JOIN CAPTEUR USING(id_capteur)",
    "zones":         "MESURE_CAPTEUR JOIN CAPTEUR USING(id_capteur)",
}

# ── MAPPING : entité → colonnes réelles dans la DB ──────────
ENTITY_COLUMNS = {
    "capteurs":      "id_capteur, type_capteur, statut, zone",
    "interventions": "id_intervention, nature, date_heure_debut, date_heure_fin, impact_co2, commentaire",
    "citoyens":      "id_citoyen, nom, prenom, score_engagement, preferences_mobilite",
    "vehicules":     "id_vehicule, plaque_immatriculation, type_vehicule, energie",
    "véhicules":     "id_vehicule, plaque_immatriculation, type_vehicule, energie",
    "trajets":       "id_trajet, origine, destination, date_heure_depart, economie_co2",
    "mesures":       "MESURE_CAPTEUR.id_mesure, CAPTEUR.zone, valeur, unite, timestamp_mesure",
    "zones":         "CAPTEUR.zone, AVG(valeur) as pollution_moyenne",
}

# ── MAPPING : statuts minuscules → valeurs DB en MAJUSCULES ─
# IMPORTANT : dans la DB de ton binôme, les statuts sont en MAJUSCULES
STATUT_VALUES = {
    "hors_service":   "HORS_SERVICE",
    "actif":          "ACTIF",
    "signale":        "SIGNALE",
    "en_maintenance": "EN_MAINTENANCE",
    "en_cours":       "EN_COURS",
    "disponible":     "DISPONIBLE",
    "inactif":        "INACTIF",
}


def generate_sql(ast: dict) -> str:
    """
    Génère une requête SQL depuis un AST.
    """

    entity   = str(ast.get("entity", "")).lower()
    filtre   = ast.get("filter")
    limit    = ast.get("limit")
    order    = ast.get("order")
    period   = ast.get("period")
    is_count = ast.get("count", False)

    # ── Récupère la table et les colonnes ────────────────────
    table   = ENTITY_TABLE.get(entity)
    columns = ENTITY_COLUMNS.get(entity, "*")

    if not table:
        raise ValueError(f"Entité inconnue : '{entity}'")

    # ── SELECT ou COUNT ──────────────────────────────────────
    if is_count:
        sql = f"SELECT COUNT(*) as total FROM {table}"
    else:
        sql = f"SELECT {columns} FROM {table}"

    # ── WHERE ────────────────────────────────────────────────
    where_parts = []

    if filtre:
        col      = filtre.get("column")
        operator = filtre.get("operator", "=")
        value    = filtre.get("value")

        if col == "statut":
            # Convertit vers MAJUSCULES pour la DB
            db_value = STATUT_VALUES.get(str(value), str(value).upper())
            where_parts.append(f"statut = '{db_value}'")

        elif col == "score_engagement":
            where_parts.append(f"score_engagement {operator} {value}")

    # Filtre "interventions en cours" = date_heure_fin IS NULL
    # car INTERVENTION n'a pas de colonne statut dans le schéma
    if entity == "interventions" and filtre and filtre.get("value") == "en_cours":
        where_parts = ["date_heure_fin IS NULL"]

    # Filtre temporel : "cette semaine"
    if period == "semaine":
        where_parts.append(
            "date_heure_debut >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
        )

    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    # ── GROUP BY pour les zones ──────────────────────────────
    if entity == "zones":
        sql += " GROUP BY CAPTEUR.zone"

    # ── ORDER BY ─────────────────────────────────────────────
    order_final = order or (filtre.get("order") if filtre else None)
    if order_final:
        col_ord = order_final.get("column", "id")
        dir_ord = order_final.get("direction", "DESC")
        sql += f" ORDER BY {col_ord} {dir_ord}"

    # ── LIMIT ────────────────────────────────────────────────
    if limit:
        sql += f" LIMIT {limit}"

    return sql


# ── TEST AUTONOME ────────────────────────────────────────────
if __name__ == "__main__":

    asts = [
        ("1. Zones polluées",
         {"type": "SELECT", "entity": "zones", "filter": None,
          "limit": 5, "order": {"column": "AVG(valeur)", "direction": "DESC"}, "count": False}),

        ("2. Capteurs hors service",
         {"type": "COUNT", "entity": "capteurs",
          "filter": {"column": "statut", "operator": "=", "value": "hors_service"},
          "limit": None, "order": None, "count": True}),

        ("3. Citoyens score > 80",
         {"type": "SELECT", "entity": "citoyens",
          "filter": {"column": "score_engagement", "operator": ">", "value": 80,
                     "order": {"column": "score_engagement", "direction": "DESC"}},
          "limit": None, "order": None, "count": False}),

        ("4. Trajet économique",
         {"type": "SELECT", "entity": "trajets", "filter": None,
          "limit": 1, "order": {"column": "economie_co2", "direction": "DESC"}, "count": False}),

        ("5. Interventions en cours",
         {"type": "SELECT", "entity": "interventions",
          "filter": {"column": "statut", "operator": "=", "value": "en_cours"},
          "limit": None, "order": None, "count": False}),

        ("6. Capteurs actifs",
         {"type": "SELECT", "entity": "capteurs",
          "filter": {"column": "statut", "operator": "=", "value": "actif"},
          "limit": None, "order": None, "count": False}),

        ("7. Interventions cette semaine",
         {"type": "COUNT", "entity": "interventions",
          "filter": None, "limit": None, "order": None,
          "count": True, "period": "semaine"}),

        ("8. 10 dernières mesures",
         {"type": "SELECT", "entity": "mesures", "filter": None,
          "limit": 10, "order": {"column": "timestamp_mesure", "direction": "DESC"}, "count": False}),

        ("9. Capteurs en maintenance",
         {"type": "SELECT", "entity": "capteurs",
          "filter": {"column": "statut", "operator": "=", "value": "en_maintenance"},
          "limit": None, "order": None, "count": False}),

        ("10. Véhicules",
         {"type": "SELECT", "entity": "vehicules",
          "filter": None, "limit": None, "order": None, "count": False}),
    ]

    print("=" * 70)
    for label, ast in asts:
        print(f"\n📝 {label}")
        try:
            print(f"   ✅ {generate_sql(ast)}")
        except Exception as e:
            print(f"   ❌ {e}")
    print("=" * 70)