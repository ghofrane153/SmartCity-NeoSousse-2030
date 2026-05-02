# compiler/compiler.py
# ============================================================
# PIPELINE COMPLET — NL → Tokens → AST → SQL
# Étape 1 : PLY (grammaire formelle)
# Étape 2 : Regex fallback (si PLY échoue)
# Étape 3 : Codegen SQL (identique pour les deux)
# ============================================================

from compiler.lexer    import tokenize
from compiler.parser   import parse_query
from compiler.fallback import fallback_parse
from compiler.codegen  import generate_sql


def compile_nl_to_sql(text: str) -> dict:
    """
    Pipeline complet : texte naturel → SQL.

    Retourne toujours un dict avec :
    {
        "sql"     : str | None,
        "ast"     : dict | None,
        "tokens"  : list,
        "method"  : "ply" | "regex" | None,
        "error"   : str | None
    }
    """

    result = {
        "sql":    None,
        "ast":    None,
        "tokens": [],
        "method": None,
        "error":  None
    }

    # ── ÉTAPE 1 : Tokenisation ───────────────────────────────
    # On tokenise toujours, même si le parsing échoue
    # (utile pour afficher les tokens dans le dashboard)
    try:
        result["tokens"] = tokenize(text)
    except Exception as e:
        result["error"] = f"Erreur de tokenisation : {e}"
        return result

    # ── ÉTAPE 2A : Parsing PLY ───────────────────────────────
    ast = None
    try:
        ast = parse_query(text)
        if ast:
            result["method"] = "ply"
    except Exception:
        pass  # PLY a échoué → on tente le fallback

    # ── ÉTAPE 2B : Fallback Regex ────────────────────────────
    if ast is None:
        try:
            ast = fallback_parse(text)
            if ast:
                result["method"] = "regex"
        except Exception as e:
            result["error"] = f"Erreur fallback : {e}"
            return result

    # ── Aucune méthode n'a reconnu la requête ────────────────
    if ast is None:
        result["error"] = (
            "Requête non reconnue : impossible d'identifier "
            "l'entité cible ou la structure de la requête."
        )
        return result

    result["ast"] = ast

    # ── ÉTAPE 3 : Génération SQL ─────────────────────────────
    try:
        result["sql"] = generate_sql(ast)
    except ValueError as e:
        result["error"] = f"Erreur sémantique : {e}"
    except Exception as e:
        result["error"] = f"Erreur génération SQL : {e}"

    return result


# ── TEST AUTONOME ────────────────────────────────────────────
if __name__ == "__main__":

    tests = [
        # ── Les 10 requêtes du sujet ──
        ("Requête 1  - sujet",    "Affiche les 5 zones les plus polluées"),
        ("Requête 2  - sujet",    "Combien de capteurs sont hors service ?"),
        ("Requête 3  - sujet",    "Quels citoyens ont un score supérieur à 80 ?"),
        ("Requête 4  - sujet",    "Donne-moi le trajet le plus économique en CO2"),
        ("Requête 5  - sujet",    "Liste les interventions en cours"),
        ("Requête 6  - sujet",    "Montre les capteurs actifs"),
        ("Requête 7  - sujet",    "Combien d'interventions ont eu lieu cette semaine ?"),
        ("Requête 8  - sujet",    "Affiche les 10 dernières mesures"),
        ("Requête 9  - sujet",    "Quels capteurs sont en maintenance ?"),
        ("Requête 10 - sujet",    "Liste les véhicules autonomes disponibles"),
        # ── Variantes (fallback regex) ──
        ("Variante 1 - fallback", "Montre-moi les capteurs qui sont actifs"),
        ("Variante 2 - fallback", "Je veux voir les interventions en cours"),
        ("Variante 3 - fallback", "Citoyens avec un score > 70"),
        ("Variante 4 - fallback", "Les 3 zones avec le plus de pollution"),
        ("Variante 5 - fallback", "Interventions des 7 derniers jours"),
        # ── Requête inconnue ──
        ("Inconnue",              "Blabla incompréhensible xyz"),
    ]

    print("=" * 70)
    print("   PIPELINE COMPLET — NL → SQL   (PLY + Regex Fallback)")
    print("=" * 70)

    ply_count   = 0
    regex_count = 0
    error_count = 0

    for label, texte in tests:
        print(f"\n{'─'*70}")
        print(f"  [{label}]")
        print(f"  📝 {texte}")

        res = compile_nl_to_sql(texte)

        if res["error"]:
            print(f"  ❌ Erreur  : {res['error']}")
            error_count += 1
        else:
            methode = "🔵 PLY" if res["method"] == "ply" else "🟡 REGEX"
            print(f"  {methode}")
            print(f"  ✅ SQL    : {res['sql']}")
            print(f"  🌿 Tokens : {[t['type'] for t in res['tokens']]}")
            if res["method"] == "ply":
                ply_count += 1
            else:
                regex_count += 1

    print(f"\n{'='*70}")
    print(f"  📊 RÉSUMÉ : PLY={ply_count} | Regex={regex_count} | Erreurs={error_count}")
    print(f"{'='*70}")