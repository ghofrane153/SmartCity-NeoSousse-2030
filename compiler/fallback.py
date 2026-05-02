# compiler/fallback.py
# ============================================================
# FALLBACK REGEX — Filet de sécurité quand PLY échoue
# ============================================================

import re

def normalise(text: str) -> str:
    text = text.lower()
    replacements = {
        'é':'e','è':'e','ê':'e','ë':'e',
        'à':'a','â':'a','ä':'a',
        'ù':'u','û':'u','ü':'u',
        'î':'i','ï':'i','ô':'o','ö':'o','ç':'c',
    }
    for accent, sans in replacements.items():
        text = text.replace(accent, sans)
    text = re.sub(r"[?!.,\-'\"]", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ── Statuts en minuscules ici — codegen les convertit en MAJUSCULES
STATUTS = {
    r'hors.?service':   'hors_service',
    r'actifs?':         'actif',
    r'signales?':       'signale',
    r'en.?maintenance': 'en_maintenance',
    r'en.?cours':       'en_cours',
    r'disponibles?':    'disponible',
    r'inactifs?':       'inactif',
}

ENTITES = {
    r'capteurs?':      'capteurs',
    r'interventions?': 'interventions',
    r'citoyens?':      'citoyens',
    r'vehicules?':     'vehicules',
    r'trajets?':       'trajets',
    r'mesures?':       'mesures',
    r'zones?':         'zones',
}

def detecte_statut(text):
    for pattern, valeur in STATUTS.items():
        if re.search(pattern, text):
            return valeur
    return None

def detecte_entite(text):
    for pattern, valeur in ENTITES.items():
        if re.search(pattern, text):
            return valeur
    return None

def pattern_zones_polluees(text):
    m = re.search(r'(\d+)\s+zones?.*(pollu)', text)
    if m:
        return {"type":"SELECT","entity":"zones","filter":None,
                "limit":int(m.group(1)),
                "order":{"column":"AVG(valeur)","direction":"DESC"},"count":False}
    if re.search(r'zones?.*(pollu|pollution)', text):
        return {"type":"SELECT","entity":"zones","filter":None,
                "limit":5,
                "order":{"column":"AVG(valeur)","direction":"DESC"},"count":False}
    return None

def pattern_score_superieur(text):
    if not re.search(r'citoyens?', text):
        return None
    m_nb = re.search(r'\d+', text)
    if not m_nb:
        return None
    valeur = int(m_nb.group())
    if re.search(r'superieur|>|depasse|plus grand', text):
        op, dir_ = ">", "DESC"
    elif re.search(r'inferieur|<|plus petit', text):
        op, dir_ = "<", "ASC"
    else:
        op, dir_ = ">", "DESC"
    return {
        "type":"SELECT","entity":"citoyens",
        "filter":{"column":"score_engagement","operator":op,"value":valeur,
                  "order":{"column":"score_engagement","direction":dir_}},
        "limit":None,"order":None,"count":False
    }

def pattern_trajet_economique(text):
    if not re.search(r'trajets?', text):
        return None
    if re.search(r'economique|co2|carbone|moins|meilleur', text):
        return {"type":"SELECT","entity":"trajets","filter":None,
                "limit":1,
                "order":{"column":"economie_co2","direction":"DESC"},"count":False}
    return None

def pattern_dernieres_mesures(text):
    if not re.search(r'mesures?', text):
        return None
    m = re.search(r'(\d+)', text)
    limit = int(m.group(1)) if m else 10
    if re.search(r'derni|recent', text) or m:
        return {"type":"SELECT","entity":"mesures","filter":None,
                "limit":limit,
                # ✅ Correction : timestamp_mesure (pas date_heure)
                "order":{"column":"timestamp_mesure","direction":"DESC"},"count":False}
    return None

def pattern_interventions_semaine(text):
    if not re.search(r'interventions?', text):
        return None
    if re.search(r'semaine|7.?jours|derniers?.?jours|jours', text):
        return {"type":"COUNT","entity":"interventions","filter":None,
                "limit":None,"order":None,"count":True,"period":"semaine"}
    return None

def pattern_vehicules(text):
    if not re.search(r'vehicules?', text):
        return None
    statut = detecte_statut(text)
    filtre = {"column":"statut","operator":"=","value":statut} if statut else None
    return {"type":"SELECT","entity":"vehicules","filter":filtre,
            "limit":None,"order":None,"count":False}

def pattern_count_entite_statut(text):
    if not re.search(r'combien|nombre', text):
        return None
    entite = detecte_entite(text)
    if not entite:
        return None
    statut = detecte_statut(text)
    filtre = {"column":"statut","operator":"=","value":statut} if statut else None
    return {"type":"COUNT","entity":entite,"filter":filtre,
            "limit":None,"order":None,"count":True}

def pattern_quels_entite_statut(text):
    if not re.search(r'quels?|quelles?', text):
        return None
    entite = detecte_entite(text)
    if not entite:
        return None
    statut = detecte_statut(text)
    filtre = {"column":"statut","operator":"=","value":statut} if statut else None
    return {"type":"SELECT","entity":entite,"filter":filtre,
            "limit":None,"order":None,"count":False}

def pattern_select_entite_statut(text):
    if not re.search(r'affiche|montre|liste|donne|voir|veux', text):
        return None
    entite = detecte_entite(text)
    if not entite:
        return None
    statut = detecte_statut(text)
    filtre = {"column":"statut","operator":"=","value":statut} if statut else None
    m = re.search(r'(\d+)', text)
    limit = int(m.group(1)) if m else None
    return {"type":"SELECT","entity":entite,"filter":filtre,
            "limit":limit,"order":None,"count":False}


PATTERNS = [
    pattern_zones_polluees,
    pattern_score_superieur,
    pattern_trajet_economique,
    pattern_dernieres_mesures,
    pattern_interventions_semaine,
    pattern_vehicules,
    pattern_count_entite_statut,
    pattern_quels_entite_statut,
    pattern_select_entite_statut,
]

def fallback_parse(text: str) -> dict | None:
    texte_normalise = normalise(text)
    for pattern_fn in PATTERNS:
        resultat = pattern_fn(texte_normalise)
        if resultat is not None:
            return resultat
    return None


if __name__ == "__main__":
    tests = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score supérieur à 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
        "Liste les interventions en cours",
        "Montre les capteurs actifs",
        "Combien d'interventions ont eu lieu cette semaine ?",
        "Affiche les 10 dernières mesures",
        "Quels capteurs sont en maintenance ?",
        "Liste les véhicules autonomes disponibles",
        "Blabla incompréhensible",
    ]
    print("=" * 65)
    for texte in tests:
        print(f"\n📝 '{texte}'")
        ast = fallback_parse(texte)
        print(f"   {'✅' if ast else '❌'} {ast if ast else 'Non reconnue'}")
    print("=" * 65)