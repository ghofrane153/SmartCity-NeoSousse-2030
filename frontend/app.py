"""
app.py — Frontend Smart City Neo-Sousse 2030
=============================================
COMMENT LANCER :
    streamlit run app.py

COMMENT ÇA MARCHE (Streamlit en résumé) :
    - Chaque fois que l'utilisateur clique ou tape quelque chose,
      Python ré-exécute tout le fichier du début à la fin.
    - st.write("texte")     → affiche du texte
    - st.button("click")    → crée un bouton, retourne True si cliqué
    - st.text_input("...")  → crée un champ de saisie
    - st.dataframe(df)      → affiche un tableau pandas
    - st.plotly_chart(fig)  → affiche un graphique

LIEN AVEC TON AMI :
    Ce fichier appelle les endpoints FastAPI de ton ami.
    URL de base : http://localhost:8000
    Endpoints utilisés :
        POST /compile          → compilateur NL→SQL
        GET  /capteurs         → liste des capteurs
        GET  /automates/status → état de tous les automates
        POST /rapport          → génération rapport IA
        GET  /health           → vérifier si l'API tourne
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Configuration globale ────────────────────────────────────────────
API_URL = "http://localhost:8000"   # ← l'URL du serveur FastAPI de ton ami

# Configuration de la page (doit être la PREMIÈRE commande st.)
st.set_page_config(
    page_title="Smart City Neo-Sousse 2030",
    page_icon="🏙️",
    layout="wide",                  # Utilise toute la largeur de l'écran
    initial_sidebar_state="expanded"
)

# ── Styles CSS personnalisés ─────────────────────────────────────────
# st.markdown avec unsafe_allow_html permet d'injecter du CSS
st.markdown("""
<style>
    /* Police principale */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&family=JetBrains+Mono&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    
    /* Fond général sombre */
    .stApp { background-color: #ffffff; color: #1a1a2e; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #ffffff; color: #1a1a2e; }
    
    /* Cartes métriques */
    .metric-card {
        background: linear-gradient(135deg, #1c2128, #21262d);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 8px 0;
    }
    
    /* Badges de statut */
    .badge-actif        { background:#1a4731; color:#3fb950; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-signale      { background:#3d2a00; color:#f0883e; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-hors_service { background:#3d1c1c; color:#f85149; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-maintenance  { background:#1c2d54; color:#58a6ff; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-inactif      { background:#21262d; color:#8b949e; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    
    /* Boîte SQL générée */
    .sql-box {
        background:#0d1117; border:1px solid #388bfd;
        border-left: 4px solid #388bfd;
        border-radius:8px; padding:16px;
        font-family:'JetBrains Mono', monospace;
        font-size:14px; color:#79c0ff;
    }
    
    /* Titre principal */
    .main-title { font-size:2.2rem; font-weight:700; color:#e6edf3; margin-bottom:0; }
    .sub-title   { font-size:1rem; color:#8b949e; margin-top:0; }
</style>
""", unsafe_allow_html=True)


# ── Fonctions utilitaires ────────────────────────────────────────────

def appeler_api(methode: str, endpoint: str, data: dict = None) -> dict | None:
    """
    Appelle l'API de ton ami et retourne la réponse.
    Si l'API n'est pas encore lancée, retourne None et affiche un warning.
    """
    try:
        url = f"{API_URL}{endpoint}"
        if methode == "GET":
            response = requests.get(url, timeout=60)
        else:
            response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.warning("⚠️ API non disponible — lance `uvicorn main:app` dans le dossier api/", icon="🔌")
        return None
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None


def badge_statut(statut: str) -> str:
    """Génère le HTML d'un badge coloré selon le statut"""
    css_class = f"badge-{statut.lower().replace(' ', '_').replace('é', 'e')}"
    return f'<span class="{css_class}">{statut}</span>'


# Données mock (utilisées si l'API n'est pas encore prête)
# Ton ami peut les remplacer progressivement
MOCK_CAPTEURS = [
    {"id": "C-001", "type": "POLLUTION", "zone": "CENTRE_VILLE",     "statut": "ACTIF"},
    {"id": "C-002", "type": "BRUIT",     "zone": "ZONE_NORD",        "statut": "SIGNALE"},
    {"id": "C-003", "type": "TRAFIC",    "zone": "ZONE_INDUSTRIELLE","statut": "HORS_SERVICE"},
    {"id": "C-004", "type": "TEMPERATURE","zone": "ZONE_SUD",        "statut": "EN_MAINTENANCE"},
    {"id": "C-005", "type": "HUMIDITE",  "zone": "ZONE_PORTUAIRE",   "statut": "ACTIF"},
]


# ── SIDEBAR — Navigation ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-title">🏙️ Neo-Sousse</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Smart City 2030</div>', unsafe_allow_html=True)
    st.divider()

    # Vérification connexion API (petit indicateur vert/rouge)
    health = appeler_api("GET", "/health")
    if health:
        st.success("API connectée ✓", icon="🟢")
    else:
        st.error("API hors ligne", icon="🔴")

    st.divider()

    # Menu de navigation
    # st.radio retourne la valeur sélectionnée
    page = st.radio(
    "Navigation",
    ["🏠 Accueil", "🔍 Requêtes NL", "📡 Capteurs", "⚙️ Automates", "🤖 Rapport IA"],
    label_visibility="collapsed"
)

    st.divider()
    st.caption(f"Dernière mise à jour : {datetime.now().strftime('%H:%M:%S')}")
    # Bouton pour forcer le rechargement des données
    if st.button("🔄 Actualiser", use_container_width=True):
        st.rerun()   # Rerun = ré-exécute tout le script = rafraîchit

# ════════════════════════════════════════════════════════════════════
# PAGE 0 — Accueil / Dashboard
# ════════════════════════════════════════════════════════════════════
if page == "🏠 Accueil":

    # ── Hero ─────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border-radius: 16px;
        padding: 48px 40px;
        margin-bottom: 32px;
        text-align: center;
    ">
        <div style="font-size: 3.5rem;">🏙️</div>
        <h1 style="color:#e6edf3; font-size:2.5rem; margin:8px 0 4px;">Neo-Sousse 2030</h1>
        <p style="color:#8b949e; font-size:1.1rem; margin:0;">
            Plateforme de gestion intelligente de la ville · Smart City Dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs en temps réel ────────────────────────────────────────
    st.markdown("### 📊 Vue d'ensemble en temps réel")

    data_capteurs = appeler_api("GET", "/capteurs")
    capteurs = data_capteurs if data_capteurs else MOCK_CAPTEURS
    df_kpi = pd.DataFrame(capteurs)

    total     = len(df_kpi)
    actifs    = len(df_kpi[df_kpi['statut'] == 'ACTIF'])    if 'statut' in df_kpi.columns else 0
    alertes   = len(df_kpi[df_kpi['statut'] == 'SIGNALE'])  if 'statut' in df_kpi.columns else 0
    hs        = len(df_kpi[df_kpi['statut'] == 'HORS_SERVICE']) if 'statut' in df_kpi.columns else 0
    taux      = round((actifs / total * 100), 1) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#1a4731,#0d2818);border:1px solid #3fb950;
            border-radius:12px;padding:24px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#3fb950;">{actifs}</div>
            <div style="color:#8b949e;font-size:0.85rem;margin-top:4px;">✅ Capteurs actifs</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#3d2a00,#1f1500);border:1px solid #f0883e;
            border-radius:12px;padding:24px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#f0883e;">{alertes}</div>
            <div style="color:#8b949e;font-size:0.85rem;margin-top:4px;">⚠️ Alertes actives</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#3d1c1c,#1f0e0e);border:1px solid #f85149;
            border-radius:12px;padding:24px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:#f85149;">{hs}</div>
            <div style="color:#8b949e;font-size:0.85rem;margin-top:4px;">🔴 Hors service</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        couleur = "#3fb950" if taux >= 80 else "#f0883e" if taux >= 50 else "#f85149"
        bg      = "#1a4731" if taux >= 80 else "#3d2a00" if taux >= 50 else "#3d1c1c"
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{bg},#0d0d0d);border:1px solid {couleur};
            border-radius:12px;padding:24px;text-align:center;">
            <div style="font-size:2rem;font-weight:700;color:{couleur};">{taux}%</div>
            <div style="color:#8b949e;font-size:0.85rem;margin-top:4px;">📈 Taux de disponibilité</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Graphique mini + Modules ──────────────────────────────────
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown("### 🗺️ Répartition par zone")
        if 'zone' in df_kpi.columns:
            df_zone = df_kpi.groupby('zone').size().reset_index(name='Capteurs')
            fig = px.bar(
                df_zone, x='zone', y='Capteurs',
                color='Capteurs',
                color_continuous_scale=['#388bfd', '#3fb950'],
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e6edf3',
                xaxis=dict(gridcolor='#21262d', title=""),
                yaxis=dict(gridcolor='#21262d'),
                coloraxis_showscale=False,
                margin=dict(t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### 🚀 Accès rapide")
        st.markdown("<br>", unsafe_allow_html=True)

        modules = [
            ("🔍", "Requêtes NL",  "Interroge la base en français", "#388bfd"),
            ("📡", "Capteurs",     "Surveille tous les capteurs",   "#3fb950"),
            ("⚙️", "Automates",    "Gère les transitions d'état",   "#f0883e"),
            ("🤖", "Rapport IA",   "Génère des analyses IA",        "#bc8cff"),
        ]

        for icon, titre, desc, couleur in modules:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-left:4px solid {couleur};
                border-radius:10px;padding:14px 16px;margin-bottom:10px;cursor:pointer;">
                <span style="font-size:1.2rem;">{icon}</span>
                <span style="font-weight:600;color:#e6edf3;margin-left:8px;">{titre}</span>
                <div style="color:#8b949e;font-size:0.8rem;margin-top:2px;margin-left:28px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Statut API ────────────────────────────────────────────────
    st.markdown("### 🔌 Statut des services")
    c1, c2, c3 = st.columns(3)
    with c1:
        if health:
            st.success("✅ API FastAPI — En ligne")
        else:
            st.error("❌ API FastAPI — Hors ligne")
    with c2:
        st.info(f"🕐 Dernière vérification : {datetime.now().strftime('%H:%M:%S')}")
    with c3:
        st.info(f"📍 Endpoint : `{API_URL}`")
# ════════════════════════════════════════════════════════════════════
# PAGE 1 — Requêtes en Langage Naturel
# ════════════════════════════════════════════════════════════════════
if page == "🔍 Requêtes NL":
    st.markdown('<h1 class="main-title">🔍 Requêtes en Langage Naturel</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Tapez une question en français → le compilateur génère le SQL</p>', unsafe_allow_html=True)
    st.divider()

    # Exemples cliquables pour aider l'utilisateur
    st.markdown("**Exemples de requêtes :**")
    col1, col2, col3 = st.columns(3)

    # st.session_state permet de mémoriser des valeurs entre les reruns
    if "requete_exemple" not in st.session_state:
        st.session_state.requete_exemple = ""

    with col1:
        if st.button("Zones polluées", use_container_width=True):
            st.session_state.requete_exemple = "Affiche les 5 zones les plus polluées"
    with col2:
        if st.button("Capteurs hors service", use_container_width=True):
            st.session_state.requete_exemple = "Combien de capteurs sont hors service ?"
    with col3:
        if st.button("Citoyens engagés", use_container_width=True):
            st.session_state.requete_exemple = "Quels citoyens ont un score écologique supérieur à 80 ?"

    # Champ de saisie principal
    requete = st.text_input(
        "Votre requête",
        value=st.session_state.requete_exemple,
        placeholder="Ex: Affiche les 5 zones les plus polluées...",
        label_visibility="collapsed"
    )

    # Bouton d'envoi
    if st.button("▶ Compiler & Exécuter", type="primary", use_container_width=True):
        if not requete.strip():
            st.warning("Entrez une requête d'abord !")
        else:
            with st.spinner("Compilation en cours..."):
                resultat = appeler_api("POST", "/compile", {"query": requete})

            if resultat:
                if resultat.get("error"):
                    st.error(f"Erreur de compilation : {resultat['error']}")
                else:
                    # Affichage du SQL généré
                    st.markdown("**SQL généré :**")
                    st.markdown(
                        f'<div class="sql-box">{resultat.get("sql", "")}</div>',
                        unsafe_allow_html=True
                    )
                    st.caption(f"Tokens détectés : {resultat.get('tokens', [])}")

                    # Affichage des résultats
                    if resultat.get("results"):
                        st.markdown("**Résultats :**")
                        df = pd.DataFrame(resultat["results"])
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"{len(df)} ligne(s) retournée(s)")
                    else:
                        st.info("Requête exécutée, aucun résultat retourné.")
            else:
                # Mode démo si API hors ligne
                st.info("Mode démo — API non disponible")
                st.markdown('<div class="sql-box">SELECT zone, AVG(valeur) as moy_pollution FROM MESURE_CAPTEUR mc JOIN CAPTEUR c ON mc.id_capteur = c.id_capteur WHERE c.type_capteur = \'POLLUTION\' GROUP BY zone ORDER BY moy_pollution DESC LIMIT 5</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# PAGE 2 — État des Capteurs
# ════════════════════════════════════════════════════════════════════
elif page == "📡 Capteurs":
    st.markdown('<h1 class="main-title">📡 État des Capteurs</h1>', unsafe_allow_html=True)
    st.divider()

    # Récupère les données (vrai API ou mock)
    data = appeler_api("GET", "/capteurs")
    capteurs = data if data else MOCK_CAPTEURS

    df = pd.DataFrame(capteurs)

    # ── Métriques résumé ──────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    comptes = df['statut'].value_counts() if 'statut' in df.columns else {}

    with col1:
        st.metric("✅ Actifs",          comptes.get('ACTIF', 0))
    with col2:
        st.metric("⚠️ Signalés",        comptes.get('SIGNALE', 0))
    with col3:
        st.metric("🔧 Maintenance",     comptes.get('EN_MAINTENANCE', 0))
    with col4:
        st.metric("🔴 Hors service",    comptes.get('HORS_SERVICE', 0))
    with col5:
        st.metric("⚪ Inactifs",        comptes.get('INACTIF', 0))

    st.divider()

    # ── Graphiques ────────────────────────────────────────────────
    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        st.markdown("**Distribution des statuts**")
        # Graphique donut (camembert avec trou)
        fig_donut = px.pie(
            df, names='statut',
            hole=0.5,
            color='statut',
            color_discrete_map={
                'ACTIF': '#3fb950',
                'SIGNALE': '#f0883e',
                'EN_MAINTENANCE': '#58a6ff',
                'HORS_SERVICE': '#f85149',
                'INACTIF': '#8b949e'
            }
        )
        fig_donut.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#e6edf3',
            legend=dict(bgcolor='rgba(0,0,0,0)')
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_droite:
        st.markdown("**Capteurs par zone**")
        if 'zone' in df.columns:
            df_zone = df.groupby(['zone', 'statut']).size().reset_index(name='count')
            fig_bar = px.bar(
                df_zone, x='zone', y='count', color='statut',
                color_discrete_map={
                    'ACTIF': '#3fb950', 'SIGNALE': '#f0883e',
                    'EN_MAINTENANCE': '#58a6ff', 'HORS_SERVICE': '#f85149',
                    'INACTIF': '#8b949e'
                }
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#e6edf3',
                xaxis=dict(gridcolor='#21262d'),
                yaxis=dict(gridcolor='#21262d')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Carte géographique des capteurs ──────────────────────────
    if 'latitude' in df.columns and 'longitude' in df.columns:
        st.markdown("**Carte des capteurs (Sousse)**")
        couleurs = {'ACTIF': 'green', 'SIGNALE': 'orange', 'EN_MAINTENANCE': 'blue',
                    'HORS_SERVICE': 'red', 'INACTIF': 'gray'}
        df['couleur'] = df['statut'].map(couleurs).fillna('gray')
        fig_map = px.scatter_mapbox(
            df, lat='latitude', lon='longitude',
            color='statut', hover_name='id' if 'id' in df.columns else None,
            hover_data=['type', 'zone'] if 'type' in df.columns else None,
            mapbox_style="carto-darkmatter",
            zoom=12, color_discrete_map={
                'ACTIF': '#3fb950', 'SIGNALE': '#f0883e',
                'EN_MAINTENANCE': '#58a6ff', 'HORS_SERVICE': '#f85149',
                'INACTIF': '#8b949e'
            }
        )
        fig_map.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e6edf3', height=400)
        st.plotly_chart(fig_map, use_container_width=True)

    # ── Tableau détaillé avec filtres ────────────────────────────
    st.markdown("**Tableau détaillé**")

    # Filtre par statut (multiselect = cases à cocher multiples)
    filtres = st.multiselect(
        "Filtrer par statut",
        options=df['statut'].unique().tolist() if 'statut' in df.columns else [],
        default=df['statut'].unique().tolist() if 'statut' in df.columns else []
    )

    df_filtre = df[df['statut'].isin(filtres)] if filtres else df
    st.dataframe(df_filtre, use_container_width=True, height=300)


# ════════════════════════════════════════════════════════════════════
# PAGE 3 — Automates
# ════════════════════════════════════════════════════════════════════
elif page == "⚙️ Automates":
    st.markdown('<h1 class="main-title">⚙️ État des Automates</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Surveillance en temps réel des transitions d\'état</p>', unsafe_allow_html=True)
    st.divider()

    data = appeler_api("GET", "/automates/status")

    # ── Onglets pour chaque type d'automate ──────────────────────
    # st.tabs crée des onglets cliquables
    tab_capteurs, tab_interventions, tab_vehicules = st.tabs([
        "📡 Capteurs", "🔧 Interventions", "🚗 Véhicules"
    ])

    with tab_capteurs:
        capteurs_data = data.get("capteurs", []) if data else []
        if capteurs_data:
            df_c = pd.DataFrame(capteurs_data)
            # Affichage avec badges HTML
            st.markdown("**États actuels des capteurs :**")
            for _, row in df_c.head(20).iterrows():
                col_id, col_type, col_zone, col_etat, col_trans = st.columns([1, 1.5, 1.5, 1.5, 3])
                with col_id:   st.code(row.get('id', ''))
                with col_type: st.caption(row.get('type', ''))
                with col_zone: st.caption(row.get('zone', ''))
                with col_etat:
                    st.markdown(badge_statut(row.get('etat', '')), unsafe_allow_html=True)
                with col_trans:
                    trans = row.get('transitions_disponibles', [])
                    st.caption(f"→ {', '.join(trans)}" if trans else "aucune")
        else:
            st.info("Données automates non disponibles — API hors ligne ?")
            st.markdown("""
            **Transitions disponibles pour un capteur ACTIF :**
            - `detecter_anomalie` → SIGNALÉ  
            - `desactiver` → INACTIF
            """)

    with tab_interventions:
        interventions_data = data.get("interventions_en_cours", []) if data else []
        if interventions_data:
            for inter in interventions_data:
                with st.expander(f"🔧 Intervention #{inter['id']} — {inter.get('nature', '')}"):
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("Capteur", inter.get('capteur_id', ''))
                    with c2: st.metric("État FSM", inter.get('etat_fsm', ''))
                    with c3: st.metric("Techniciens", inter.get('nb_techniciens', 0))
                    st.caption(f"Début : {inter.get('debut', '')}")
        else:
            st.info("Aucune intervention en cours actuellement")

    with tab_vehicules:
        vehicules_data = data.get("vehicules", []) if data else []
        if vehicules_data:
            df_v = pd.DataFrame(vehicules_data)
            for _, row in df_v.iterrows():
                col_plaque, col_type, col_etat, col_dest = st.columns([2, 1.5, 1.5, 3])
                with col_plaque: st.code(row.get('plaque', ''))
                with col_type:   st.caption(row.get('type', ''))
                with col_etat:   st.markdown(badge_statut(row.get('etat', '')), unsafe_allow_html=True)
                with col_dest:
                    dest = row.get('destination')
                    st.caption(f"→ {dest}" if dest else "En attente")
        else:
            st.info("Données véhicules non disponibles")

    st.divider()

    # ── Simulateur de transition ──────────────────────────────────
    st.markdown("**🎮 Simuler une transition**")
    st.caption("Teste une transition sans modifier la DB réelle")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        entite_type = st.selectbox("Type", ["capteur", "intervention", "vehicule"])
    with col_b:
        entite_id = st.text_input("ID", placeholder="Ex: C-001")
    with col_c:
        evenement = st.text_input("Événement", placeholder="Ex: detecter_anomalie")

    if st.button("▶ Simuler", type="primary"):
        if entite_id and evenement:
            result = appeler_api("POST", f"/automates/{entite_type}/{entite_id}/transition", {"evenement": evenement})
            if result:
                if result.get("succes"):
                    st.success(f"✓ {result['ancien_etat']} → **{result['nouvel_etat']}**")
                else:
                    st.error(f"✗ {result.get('erreur', 'Transition invalide')}")
        else:
            st.warning("Remplis tous les champs")


# ════════════════════════════════════════════════════════════════════
# PAGE 4 — Rapport IA
# ════════════════════════════════════════════════════════════════════
elif page == "🤖 Rapport IA":
    st.markdown('<h1 class="main-title">🤖 Rapports IA Générés</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Analyse automatique des données urbaines par intelligence artificielle</p>', unsafe_allow_html=True)
    st.divider()

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        type_rapport = st.selectbox(
            "Type de rapport",
            ["general", "capteurs", "interventions"],
            format_func=lambda x: {
                "general": "📊 Rapport général de la ville",
                "capteurs": "📡 Analyse des capteurs",
                "interventions": "🔧 Bilan des interventions"
            }[x]
        )
    with col_opt2:
        st.markdown("<br>", unsafe_allow_html=True)   # Espace vertical
        generer = st.button("🤖 Générer le rapport", type="primary", use_container_width=True)

    if generer:
        with st.spinner("L'IA analyse les données urbaines..."):
            resultat = appeler_api("POST", "/rapport", {"type": type_rapport})

        if resultat and resultat.get("rapport"):
            st.divider()
            # En-tête du rapport
            st.markdown(f"""
            <div style='background:#161b22; border:1px solid #30363d; border-radius:12px; padding:20px; margin-bottom:16px;'>
                <div style='color:#8b949e; font-size:12px;'>RAPPORT GÉNÉRÉ LE {datetime.now().strftime("%d/%m/%Y à %H:%M")}</div>
                <div style='font-size:1.3rem; font-weight:600; margin-top:4px;'>
                    Neo-Sousse 2030 — {'Rapport Général' if type_rapport == 'general' else 'Analyse ' + type_rapport.capitalize()}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Contenu du rapport
            st.markdown(resultat["rapport"])

            # Bouton de téléchargement
            st.download_button(
                label="⬇️ Télécharger le rapport (.txt)",
                data=resultat["rapport"],
                file_name=f"rapport_{type_rapport}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        else:
            # Mode démo si API hors ligne
            st.info("Mode démo — voici un exemple de rapport généré :")
            st.markdown("""
            ---
            **Rapport Général — Neo-Sousse 2030**  
            *Généré le 01/05/2026 à 14:30*

            La ville de Neo-Sousse présente un état globalement satisfaisant avec **72% des capteurs actifs** 
            et fonctionnels. Cependant, la zone industrielle concentre 4 des 6 capteurs en état "Signalé", 
            indiquant une dégradation de la qualité de l'air nécessitant une intervention prioritaire.

            **Interventions recommandées :** Le capteur C-042 affiche un taux d'erreur de 18% sur les 
            dernières 48 heures. Une maintenance préventive est conseillée avant la fin de semaine.

            **Mobilité :** Les véhicules autonomes ont effectué 47 trajets aujourd'hui, économisant 
            en moyenne 3.2 kg de CO₂ par trajet par rapport aux véhicules thermiques.
            """)