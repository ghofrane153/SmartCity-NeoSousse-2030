# compiler/lexer.py
# ============================================================
# LEXER — Découpe le texte en tokens avec PLY
# ============================================================

import ply.lex as lex

# ── LISTE DE TOUS LES TOKENS ────────────────────────────────
# Chaque token doit apparaître ici avant d'être défini
tokens = (
    # Verbes d'affichage
    'AFFICHE', 'MONTRE', 'DONNE', 'LISTE',
    # Verbes de comptage
    'COMBIEN',
    # Verbes de sélection
    'QUELS', 'QUELLES',
    # Entités (tables de la DB)
    'CAPTEURS', 'INTERVENTIONS', 'CITOYENS',
    'VEHICULES', 'TRAJETS', 'MESURES', 'ZONES',
    # Statuts
    'HORS_SERVICE', 'ACTIF', 'SIGNALE',
    'EN_MAINTENANCE', 'EN_COURS', 'DISPONIBLE',
    # Attributs
    'POLLUTION', 'CO2', 'SCORE', 'ECONOMIQUE', 'DERNIERES',
    # Quantificateurs
    'PLUS', 'MOINS', 'MAXIMUM', 'MINIMUM',
    # Mots structurels
    'LES', 'DE', 'UN', 'LA', 'MOI', 'LE',
    'SONT', 'AVEC', 'QUI', 'EN', 'ETAT',
    'CETTE', 'SEMAINE', 'AUTONOMES', 'ONT', 'A',
    # Conditions
    'SUPERIEUR', 'INFERIEUR', 'EGAL',
    # Nombre
    'NUMBER',
)

# ── RÈGLES POUR CHAQUE TOKEN ────────────────────────────────
# Règle = fonction Python dont le nom commence par t_
# La docstring contient la regex qui reconnaît le token
# IMPORTANT : les fonctions sont prioritaires sur les variables

# --- Verbes ---
def t_AFFICHE(t):
    r'[Aa]ffiche'
    return t

def t_MONTRE(t):
    r'[Mm]ontre'
    return t

def t_DONNE(t):
    r'[Dd]onne'
    return t

def t_LISTE(t):
    r'[Ll]iste'
    return t

def t_COMBIEN(t):
    r'[Cc]ombien'
    return t

def t_QUELLES(t):
    r'[Qq]uelles'
    return t

def t_QUELS(t):
    r'[Qq]uels'
    return t

# --- Entités ---
def t_INTERVENTIONS(t):
    r'interventions?'
    return t

def t_CAPTEURS(t):
    r'capteurs?'
    return t

def t_CITOYENS(t):
    r'citoyens?'
    return t

def t_VEHICULES(t):
    r'v[eé]hicules?'
    return t

def t_TRAJETS(t):
    r'trajets?'
    return t

def t_MESURES(t):
    r'mesures?'
    return t

def t_ZONES(t):
    r'zones?'
    return t

# --- Statuts (attention : "hors service" = 2 mots, géré avec regex) ---
def t_HORS_SERVICE(t):
    r'hors[\s_-]?service'
    return t

def t_EN_MAINTENANCE(t):
    r'en[\s_-]?maintenance'
    return t

def t_EN_COURS(t):
    r'en[\s_-]?cours'
    return t

def t_ACTIF(t):
    r'actifs?'
    return t

def t_SIGNALE(t):
    r'signal[eé]s?'
    return t

def t_DISPONIBLE(t):
    r'disponibles?'
    return t

# --- Attributs ---
def t_POLLUTION(t):
    r'pollu[eé]es?|pollution'
    return t

def t_ECONOMIQUE(t):
    r'[eé]conomiques?'
    return t

def t_CO2(t):
    r'[Cc][Oo]2'
    return t

def t_SCORE(t):
    r'score'
    return t

def t_DERNIERES(t):
    r'derni[eè]res?'
    return t

# --- Quantificateurs ---
def t_MAXIMUM(t):
    r'maximum|max'
    return t

def t_MINIMUM(t):
    r'minimum|min'
    return t

def t_PLUS(t):
    r'plus'
    return t

def t_MOINS(t):
    r'moins'
    return t

# --- Conditions ---
def t_SUPERIEUR(t):
    r'sup[eé]rieur'
    return t

def t_INFERIEUR(t):
    r'inf[eé]rieur'
    return t

def t_EGAL(t):
    r'[eé]gal'
    return t

# --- Mots structurels ---
def t_AUTONOMES(t):
    r'autonomes?'
    return t

def t_SEMAINE(t):
    r'semaine'
    return t

def t_CETTE(t):
    r'cette'
    return t

def t_SONT(t):
    r'sont'
    return t

def t_AVEC(t):
    r'avec'
    return t

def t_ETAT(t):
    r'[eé]tat'
    return t

def t_QUI(t):
    r'qui'
    return t

def t_ONT(t):
    r'ont'
    return t

def t_LES(t):
    r'les'
    return t

def t_MOI(t):
    r'moi'
    return t

def t_DE(t):
    r"d[e']"
    return t

def t_UN(t):
    r'un'
    return t

def t_LA(t):
    r'la'
    return t

def t_LE(t):
    r'le'
    return t

def t_EN(t):
    r'en'
    return t

def t_A(t):
    r'[aà]'
    return t

# --- Nombres : convertit automatiquement en int ---
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# ── CARACTÈRES IGNORÉS ───────────────────────────────────────
# Ces caractères sont silencieusement ignorés par le lexer
t_ignore = ' \t\n\r'

def t_ignore_PONCTUATION(t):
    r"[?!.,\-'\"\(\)àáâãäèêëìíîïòóôùúûü]"
    pass  # ignore sans retourner de token

# ── GESTION D'ERREUR ─────────────────────────────────────────
def t_error(t):
    # Caractère non reconnu → on l'ignore et on continue
    t.lexer.skip(1)

# ── CONSTRUCTION DU LEXER ────────────────────────────────────
lexer = lex.lex()

# ── FONCTION UTILITAIRE ──────────────────────────────────────
def tokenize(text: str) -> list:
    """
    Retourne la liste des tokens d'un texte.
    Utilisé par compiler.py pour afficher les tokens dans le résultat.
    """
    lexer.input(text)
    result = []
    for tok in lexer:
        result.append({"type": tok.type, "value": tok.value})
    return result


# ── TEST AUTONOME ────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "Affiche les 5 zones les plus polluées",
        "Combien de capteurs sont hors service ?",
        "Quels citoyens ont un score supérieur à 80 ?",
        "Liste les interventions en cours",
        "Montre les capteurs actifs",
    ]
    for texte in tests:
        print(f"\n📝 '{texte}'")
        for tok in tokenize(texte):
            print(f"   {tok['type']:20} → {tok['value']}")