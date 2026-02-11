import streamlit as st
import os
import base64

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="US x Winamax | Research Hub",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SESSION STATE ---
if 'current_app' not in st.session_state:
    st.session_state['current_app'] = 'home'

# --- NAVIGATION FUNCTIONS ---
def go_home():
    st.session_state['current_app'] = 'home'
    st.rerun()

def go_premier():
    st.session_state['current_app'] = 'premier'
    st.rerun()

def go_laliga():
    st.session_state['current_app'] = 'laliga'
    st.rerun()

# --- UTILS: LOAD ASSETS ---
def get_img_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# Load assets
ASSETS_DIR = "assets"
logo_us = get_img_base64(os.path.join(ASSETS_DIR, "logo_us.png"))
logo_pl = get_img_base64(os.path.join(ASSETS_DIR, "logo_pl.png"))
logo_laliga = get_img_base64(os.path.join(ASSETS_DIR, "logo_laliga.png"))
logo_winamax = get_img_base64(os.path.join(ASSETS_DIR, "logo_winamax.png"))

# Fallback URLs
URL_US = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Logotipo_de_la_Universidad_de_Sevilla.svg/1200px-Logotipo_de_la_Universidad_de_Sevilla.svg.png"
URL_PL = "https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1200px-Premier_League_Logo.svg.png"
URL_LL = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/LaLiga_logo_2023.svg/2048px-LaLiga_logo_2023.svg.png"
URL_WINA = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Winamax_logo.svg/2560px-Winamax_logo.svg.png"

src_us = f"data:image/png;base64,{logo_us}" if logo_us else URL_US
src_pl = f"data:image/png;base64,{logo_pl}" if logo_pl else URL_PL
src_laliga = f"data:image/png;base64,{logo_laliga}" if logo_laliga else URL_LL
src_winamax = f"data:image/png;base64,{logo_winamax}" if logo_winamax else URL_WINA

# --- CSS STYLING (High Fidelity Academic) ---
def load_landing_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap');

    /* VARS */
    :root {
        --us-red: #a91818;
        --us-gold: #c5a059;
        --us-dark: #2c2c2c;
        --us-bg: #fdfbf7;
        --text-main: #212529;
    }

    /* GLOBAL */
    .stApp {
        background-color: var(--us-bg);
        font-family: 'Inter', sans-serif;
        color: var(--text-main);
    }
    
    /* HEADER / NAVBAR */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 40px;
        background: white;
        border-bottom: 4px solid var(--us-red);
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    
    .header-logo-group {
        display: flex;
        align-items: center;
        gap: 30px;
    }
    
    .us-logo-img { height: 90px; object-fit: contain; }
    /* Winamax Logo Tweaks: Ensure red visibility */
    .wina-logo-img { height: 50px; object-fit: contain; opacity: 1.0; } 
    
    .divider-v { height: 60px; width: 1px; background: #e0e0e0; margin: 0 10px; }
    
    .header-title-group {
        text-align: right;
    }
    
    .dept-title {
        font-family: 'Inter', sans-serif;
        font-size: 15px; 
        text-transform: uppercase;
        color: #555;
        letter-spacing: 0.5px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .project-title {
        font-family: 'Playfair Display', serif;
        font-size: 14px;
        font-style: italic;
        color: var(--us-red);
    }

    /* HERO CONTENT */
    .hero-section {
        text-align: center;
        padding: 60px 20px 40px 20px;
        max-width: 900px;
        margin: 0 auto;
    }
    
    .main-headline {
        font-family: 'Playfair Display', serif;
        font-size: 46px;
        font-weight: 900;
        color: var(--us-dark);
        line-height: 1.15;
        margin-bottom: 25px;
        letter-spacing: -0.5px;
    }
    
    .main-subheadline {
        font-size: 17px;
        color: #555;
        line-height: 1.6;
        max-width: 750px;
        margin: 0 auto 50px auto;
        font-weight: 300;
    }

    /* MODULES */
    .module-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(0,0,0,0.04);
        display: flex;
        flex-direction: column;
        height: 100%;
        position: relative;
    }
    
    .module-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 50px rgba(0,0,0,0.12);
        border-color: var(--us-red);
    }
    
    .card-header-bg {
        height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }
    .bg-pl { background: #3d195b; }
    .bg-ll { background: #111111; }
    
    /* PL Logo Tweak: Invert color to white if using purple bg */
    .card-logo-pl {
        height: 100px;
        object-fit: contain;
        filter: brightness(0) invert(1) drop-shadow(0 4px 10px rgba(0,0,0,0.3));
    }
    .card-logo-ll {
        height: 100px;
        object-fit: contain;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3));
    }
    
    .card-body {
        padding: 30px 30px 80px 30px; /* Extra bottom padding for button overlay */
        text-align: center;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    
    .card-title {
        font-family: 'Playfair Display', serif;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 15px;
        color: var(--us-dark);
    }
    
    .card-desc {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
        line-height: 1.5;
        flex-grow: 1;
    }

    /* CLICKABLE CARD TRICK: Make button cover bottom area or full width */
    div.stButton > button {
        width: 100%;
        background-color: var(--us-red);
        color: white;
        border: none;
        padding: 16px 20px; /* Larger click area */
        font-weight: 600;
        border-radius: 8px; /* Slightly more rounded */
        transition: background 0.2s;
        text-transform: uppercase;
        font-size: 14px;
        letter-spacing: 1px;
        cursor: pointer;
    }
    div.stButton > button:hover {
        background-color: #801212;
        box-shadow: 0 6px 16px rgba(169, 24, 24, 0.3);
        transform: translateY(-2px);
    }
    
    /* FOOTER */
    .footer-section {
        text-align: center;
        margin-top: 100px;
        padding: 40px;
        font-size: 12px;
        color: #999;
        background: #fff;
        border-top: 1px solid #eaeaea;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LANDING PAGE ---
def render_landing():
    load_landing_css()
    
    # Custom HTML Layout
    st.markdown(f"""
    <!-- HEADER -->
    <div class="header-container">
        <div class="header-logo-group">
            <img src="{src_us}" class="us-logo-img">
            <div class="divider-v"></div>
            <img src="{src_winamax}" class="wina-logo-img">
        </div>
        <div class="header-title-group">
            <div class="dept-title">Escuela Técnica Superior de<br>Ingeniería Informática</div>
            <div class="project-title">Trabajo de Fin de Grado • Curso 2024/25</div>
        </div>
    </div>
    
    <!-- HERO -->
    <div class="hero-section">
        <h1 class="main-headline">Advanced Predictive Modeling<br>in Sports Betting Markets</h1>
        <p class="main-subheadline">
            Algorithmic Trading & Machine Learning implementation for value detection in Premier League & LaLiga markets. 
            Powered by <strong>XGBoost</strong> and <strong>Optuna</strong> hyperparameter optimization.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # MODULES 
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        col_A, col_B = st.columns(2, gap="large")
        
        with col_A:
            st.markdown(f"""
            <div class="module-card">
                <div class="card-header-bg bg-pl">
                    <img src="{src_pl}" class="card-logo-pl">
                </div>
                <div class="card-body">
                    <div class="card-title">Premier League</div>
                    <div class="card-desc">
                        Specific model trained on 15 years of English data. 
                        Live integration with <strong>Winamax Odds</strong>.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Button is outside the HTML div but visually acts as the "Action"
            if st.button("OPEN DASHBOARD", key="btn_pl"):
                go_premier()

        with col_B:
            st.markdown(f"""
            <div class="module-card">
                <div class="card-header-bg bg-ll">
                     <img src="{src_laliga}" class="card-logo-ll">
                </div>
                <div class="card-body">
                    <div class="card-title">LaLiga EA Sports</div>
                    <div class="card-desc">
                        Advanced tactical analysis engine for Spanish clubs. 
                        <strong>Radar Charts</strong> & Historical Performance Audit.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("OPEN DASHBOARD", key="btn_ll"):
                go_laliga()

    # FOOTER
    st.markdown("""
    <div class="footer-section">
        <strong>Universidad de Sevilla</strong> © 2025 • Escuela Técnica Superior de Ingeniería Informática (ETSII)<br>
        <em>Grado en Ingeniería Informática - Tecnologías Informáticas</em>
    </div>
    """, unsafe_allow_html=True)

# --- APP ROUTER ---
if st.session_state['current_app'] == 'premier':
    import app_premier
    with st.sidebar:
        st.markdown("---")
        if st.button("⬅ RETURN TO HUB"):
            go_home()
    app_premier.main()

elif st.session_state['current_app'] == 'laliga':
    import app_dashboard
    with st.sidebar:
        st.markdown("---")
        if st.button("⬅ RETURN TO HUB"):
            go_home()
    app_dashboard.main()

else:
    render_landing()
