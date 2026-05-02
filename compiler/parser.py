# compiler/parser.py
# ============================================================
# PARSER — Analyse syntaxique et construction de l'AST
# ============================================================

import ply.yacc as yacc
from compiler.lexer import tokens, lexer

# ============================================================
# GRAMMAIRE COMPLÈTE
# ============================================================
#
# requete → verbe_aff  entite
# requete → verbe_aff  entite  filtre_statut
# requete → verbe_aff  LES NUMBER entite  ordre_pollution
# requete → verbe_aff  LES NUMBER DERNIERES entite
# requete → verbe_aff  LE  entite  ordre_eco
# requete → verbe_cnt  DE  entite
# requete → verbe_cnt  DE  entite  filtre_statut
# requete → verbe_cnt  DE  entite  filtre_statut  CETTE SEMAINE
# requete → verbe_sel  entite  condition_score
#
# verbe_aff  → AFFICHE LES | MONTRE LES | LISTE LES | DONNE MOI LES | DONNE MOI LE
# verbe_cnt  → COMBIEN
# verbe_sel  → QUELS | QUELLES
# ============================================================


# ── RÈGLE 1 : SELECT simple ──────────────────────────────────
# "Liste les interventions" / "Affiche les capteurs"
def p_requete_simple(p):
    """requete : verbe_aff entite"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[2],
        "filter": None,
        "limit":  None,
        "order":  None,
        "count":  False
    }

# ── RÈGLE 2 : SELECT avec filtre statut ──────────────────────
# "Montre les capteurs actifs" / "Liste les interventions en cours"
def p_requete_filtre(p):
    """requete : verbe_aff entite filtre_statut"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[2],
        "filter": p[3],
        "limit":  None,
        "order":  None,
        "count":  False
    }

# ── RÈGLE 3 : SELECT top N avec ordre ────────────────────────
# "Affiche les 5 zones les plus polluées"
def p_requete_top_n(p):
    """requete : verbe_aff LES NUMBER entite ordre_pollution"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[4],
        "filter": None,
        "limit":  p[3],        # le nombre N
        "order":  p[5],        # colonne + direction
        "count":  False
    }

# ── RÈGLE 4 : SELECT N dernières ─────────────────────────────
# "Affiche les 10 dernières mesures"
def p_requete_dernieres(p):
    """requete : verbe_aff LES NUMBER DERNIERES entite"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[5],
        "filter": None,
        "limit":  p[3],
        "order":  {"column": "date_heure", "direction": "DESC"},
        "count":  False
    }

# ── RÈGLE 5 : SELECT le plus économique ──────────────────────
# "Donne-moi le trajet le plus économique en CO2"
def p_requete_eco(p):
    """requete : verbe_aff LE entite ordre_eco"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[3],
        "filter": None,
        "limit":  1,
        "order":  p[4],
        "count":  False
    }

# ── RÈGLE 6 : COUNT simple ───────────────────────────────────
# "Combien de capteurs ?"
def p_requete_count_simple(p):
    """requete : verbe_cnt DE entite"""
    p[0] = {
        "type":   "COUNT",
        "entity": p[3],
        "filter": None,
        "limit":  None,
        "order":  None,
        "count":  True
    }

# ── RÈGLE 7 : COUNT avec filtre ──────────────────────────────
# "Combien de capteurs sont hors service ?"
def p_requete_count_filtre(p):
    """requete : verbe_cnt DE entite filtre_statut"""
    p[0] = {
        "type":   "COUNT",
        "entity": p[3],
        "filter": p[4],
        "limit":  None,
        "order":  None,
        "count":  True
    }

# ── RÈGLE 8 : COUNT cette semaine ────────────────────────────
# "Combien d'interventions ont eu lieu cette semaine ?"
def p_requete_count_semaine(p):
    """requete : verbe_cnt DE entite filtre_statut CETTE SEMAINE"""
    p[0] = {
        "type":   "COUNT",
        "entity": p[3],
        "filter": p[4],
        "limit":  None,
        "order":  None,
        "count":  True,
        "period": "semaine"
    }

# ── RÈGLE 9 : SELECT avec condition numérique ────────────────
# "Quels citoyens ont un score supérieur à 80 ?"
def p_requete_condition(p):
    """requete : verbe_sel entite condition_score"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[2],
        "filter": p[3],
        "limit":  None,
        "order":  p[3].get("order"),
        "count":  False
    }

# ── RÈGLE 10 : SELECT statut direct (sans verbe_aff complet) ─
# "Quels capteurs sont en maintenance ?"
def p_requete_quels_statut(p):
    """requete : verbe_sel entite filtre_statut"""
    p[0] = {
        "type":   "SELECT",
        "entity": p[2],
        "filter": p[3],
        "limit":  None,
        "order":  None,
        "count":  False
    }


# ── VERBES ───────────────────────────────────────────────────

def p_verbe_aff_affiche(p):
    """verbe_aff : AFFICHE LES"""
    p[0] = "affiche"

def p_verbe_aff_montre(p):
    """verbe_aff : MONTRE LES"""
    p[0] = "montre"

def p_verbe_aff_liste(p):
    """verbe_aff : LISTE LES"""
    p[0] = "liste"

def p_verbe_aff_donne_les(p):
    """verbe_aff : DONNE MOI LES"""
    p[0] = "donne"

def p_verbe_aff_donne_le(p):
    """verbe_aff : DONNE MOI LE"""
    p[0] = "donne"

def p_verbe_cnt(p):
    """verbe_cnt : COMBIEN"""
    p[0] = "combien"

def p_verbe_sel_quels(p):
    """verbe_sel : QUELS"""
    p[0] = "quels"

def p_verbe_sel_quelles(p):
    """verbe_sel : QUELLES"""
    p[0] = "quelles"


# ── ENTITÉS ──────────────────────────────────────────────────

def p_entite(p):
    """entite : CAPTEURS
              | INTERVENTIONS
              | CITOYENS
              | VEHICULES
              | TRAJETS
              | MESURES
              | ZONES"""
    p[0] = p[1].lower()


# ── FILTRES STATUT ───────────────────────────────────────────

def p_filtre_statut_sont(p):
    """filtre_statut : SONT statut"""
    # "sont hors service" / "sont actifs"
    p[0] = {"column": "statut", "operator": "=", "value": p[2]}

def p_filtre_statut_direct(p):
    """filtre_statut : statut"""
    # "actifs" / "en maintenance" (sans "sont")
    p[0] = {"column": "statut", "operator": "=", "value": p[1]}

def p_statut_hors_service(p):
    """statut : HORS_SERVICE"""
    p[0] = "hors_service"

def p_statut_actif(p):
    """statut : ACTIF"""
    p[0] = "actif"

def p_statut_signale(p):
    """statut : SIGNALE"""
    p[0] = "signale"

def p_statut_maintenance(p):
    """statut : EN_MAINTENANCE"""
    p[0] = "en_maintenance"

def p_statut_en_cours(p):
    """statut : EN_COURS"""
    p[0] = "en_cours"

def p_statut_disponible(p):
    """statut : DISPONIBLE"""
    p[0] = "disponible"


# ── ORDRES ───────────────────────────────────────────────────

def p_ordre_pollution(p):
    """ordre_pollution : LES PLUS POLLUTION"""
    # "les plus polluées"
    p[0] = {"column": "AVG(valeur)", "direction": "DESC"}

def p_ordre_eco(p):
    """ordre_eco : LES PLUS ECONOMIQUE EN CO2"""
    # "le plus économique en CO2"
    p[0] = {"column": "economie_co2", "direction": "DESC"}


# ── CONDITIONS NUMÉRIQUES ────────────────────────────────────

def p_condition_superieur(p):
    """condition_score : ONT UN SCORE SUPERIEUR A NUMBER"""
    # "ont un score supérieur à 80"
    p[0] = {
        "column":   "score_engagement",
        "operator": ">",
        "value":    p[7],
        "order":    {"column": "score_engagement", "direction": "DESC"}
    }

def p_condition_inferieur(p):
    """condition_score : ONT UN SCORE INFERIEUR A NUMBER"""
    # "ont un score inférieur à 50"
    p[0] = {
        "column":   "score_engagement",
        "operator": "<",
        "value":    p[7],
        "order":    {"column": "score_engagement", "direction": "ASC"}
    }


# ── GESTION D'ERREUR ─────────────────────────────────────────

def p_error(p):
    # Ne pas afficher d'erreur ici — le fallback prendra le relais
    pass


# ── CONSTRUCTION DU PARSER ───────────────────────────────────
parser = yacc.yacc(debug=False, errorlog=yacc.NullLogger())


# ── FONCTION PRINCIPALE ──────────────────────────────────────
def parse_query(text: str) -> dict | None:
    """
    Parse une requête NL → AST.
    Retourne un dict AST ou None si non reconnue par PLY.
    """
    try:
        result = parser.parse(text, lexer=lexer.clone())
        return result
    except Exception:
        return None


# ── TEST AUTONOME ────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score supérieur à 80 ?",
        "Donne-moi le trajet le plus économique en CO2",
        "Liste les interventions en cours",
        "Montre les capteurs actifs",
        "Affiche les 10 dernières mesures",
        "Quels capteurs sont en maintenance ?",
        "Liste les véhicules autonomes disponibles",
    ]
    for texte in tests:
        print(f"\n📝 '{texte}'")
        ast = parse_query(texte)
        if ast:
            print(f"   ✅ AST : {ast}")
        else:
            print(f"   ❌ PLY n'a pas reconnu → fallback nécessaire")