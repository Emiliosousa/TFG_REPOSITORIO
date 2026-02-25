import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import os
import json
import base64
import requests
import subprocess
import sys
import re

# Ensure src is importable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(BASE_DIR, 'src')):
    # Check if LaLiga subfolder exists directly (Correct path when running in TFG_REPOSITORIO)
    if os.path.exists(os.path.join(BASE_DIR, 'LaLiga', 'src')):
        BASE_DIR = os.path.join(BASE_DIR, 'LaLiga')
    # Check if nested in TFG_REPOSITORIO/LaLiga (Correct path when running in root)
    elif os.path.exists(os.path.join(BASE_DIR, 'TFG_REPOSITORIO', 'LaLiga', 'src')):
        BASE_DIR = os.path.join(BASE_DIR, 'TFG_REPOSITORIO', 'LaLiga')
sys.path.append(BASE_DIR)
try:
    from src.feature_engineering import generate_features
    from src.staking_system import calcular_stake_profesional
    from src.staking_config import STAKING_CONFIG
except ImportError as e:
    st.error(f"Error cargando los módulos de LaLiga: {e}", icon=None)
    def calcular_stake_profesional(prob, quota, bankroll, rank_diff=0):
        ev = (prob * quota) - 1
        edge_pct = ev * 100
        if ev <= 0.03:
            return {'filtro_pasado': False, 'edge_pct': edge_pct, 'razon_rechazo': 'Edge < 3%'}
        if quota <= 1.0:
            return {'filtro_pasado': False, 'edge_pct': edge_pct, 'razon_rechazo': 'Cuota <= 1'}
        kelly = ev / (quota - 1.0)
        kelly_frac = min(max(kelly * 0.25, 0), 0.05)
        importe = round(kelly_frac * bankroll, 2)
        if importe == 0:
            return {'filtro_pasado': False, 'edge_pct': edge_pct, 'razon_rechazo': 'Stake 0'}
        stake_scale = int(min(max(kelly_frac / 0.005, 1), 10))
        return {'filtro_pasado': True, 'edge_pct': edge_pct, 'stake_scale': stake_scale, 'importe': importe}
    STAKING_CONFIG = {}

# --- UTILS ---
def clean_html(html):
    """Remove leading whitespace from every line to fix Streamlit formatting."""
    return re.sub(r'^\s+', '', html, flags=re.MULTILINE)

# Config moved to main block

# --- ENTERPRISE CSS (Variables & Theme) ---
def load_css():
    st.markdown(clean_html("""
<style>
/* === VARIABLES === */
:root {
  --bg-primary: #0a0e27;
  --bg-secondary: #151932;
  --bg-tertiary: #1e2139;
  --text-primary: #ffffff;
  --text-secondary: #a0aec0;
  --text-tertiary: #6b7280;
  --accent-success: #10b981;
  --accent-danger: #ef4444;
  --accent-warning: #f59e0b;
  --accent-info: #3b82f6;
  --glass: rgba(255, 255, 255, 0.05);
  --border: rgba(255, 255, 255, 0.08);
}

/* === RESET & LAYOUT === */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}

/* === TYPOGRAPHY === */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
}

/* === METRICS === */
[data-testid="stMetric"] {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: var(--accent-info);
}
[data-testid="stMetricLabel"] {
    font-size: 13px !important;
    color: var(--text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 700 !important;
}

/* === BUTTONS === */
.stButton > button {
    background: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover {
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    transform: translateY(-1px);
}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border: none;
    color: var(--text-secondary);
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-info) !important;
    border-bottom: 2px solid var(--accent-info) !important;
}

/* === CUSTOM PREMIER LEAGUE STYLE OVERRIDES IF NEEDED === */
/* ... */
</style>
    """), unsafe_allow_html=True)

# --- CONSTANTS ---
DATA_FILE = os.path.join(BASE_DIR, 'notebooks', 'df_final_clean.csv')
MODEL_V2_FILE = os.path.join(BASE_DIR, 'modelo_city_group.joblib')          # Academic V2
MODEL_V3_FILE = os.path.join(BASE_DIR, 'notebooks', 'modelo_v3_calibrado.joblib')  # V3
MODEL_FILE = MODEL_V2_FILE  # legacy alias
METRICS_FILE = os.path.join(BASE_DIR, 'validation_metrics.json')
ODDS_FILE = os.path.join(BASE_DIR, 'data', 'live_odds.json')
LOGOS_DIR = os.path.join(BASE_DIR, 'data', 'logos')

TEAM_MAPPING = {
    "Girona": "Girona FC", "Girona FC": "Girona FC",
    "Villarreal": "Villarreal CF", "Villarreal CF": "Villarreal CF",
    "Mallorca": "RCD Mallorca", "RCD Mallorca": "RCD Mallorca",
    "Alaves": "Alaves", "Deportivo Alaves": "Alaves",
    "Valencia": "Valencia CF", "Valencia CF": "Valencia CF",
    "Celta": "Celta Vigo", "RC Celta": "Celta Vigo", "RC Celta de Vigo": "Celta Vigo", "Celta de Vigo": "Celta Vigo",
    "Ath Bilbao": "Athletic Bilbao", "Athletic Club": "Athletic Bilbao", "Athletic": "Athletic Bilbao",
    "Espanol": "RCD Espanyol", "Espanyol": "RCD Espanyol", "RCD Espanyol": "RCD Espanyol",
    "Elche": "Elche CF", "Elche CF": "Elche CF",
    "Real Madrid": "Real Madrid",
    "Betis": "Real Betis", "Real Betis Balompie": "Real Betis",
    "Ath Madrid": "Atletico Madrid", "Atletico de Madrid": "Atletico Madrid", "Athletic Madrid": "Atletico Madrid", "Atletico Madrid": "Atletico Madrid",
    "Levante": "Levante UD", "Levante UD": "Levante UD",
    "Osasuna": "CA Osasuna", "CA Osasuna": "CA Osasuna",
    "Sociedad": "Real Sociedad", "Real Sociedad": "Real Sociedad",
    "Oviedo": "Oviedo", "Real Oviedo": "Oviedo",
    "Sevilla": "Sevilla FC", "Sevilla FC": "Sevilla FC",
    "Vallecano": "Rayo Vallecano", "Rayo Vallecano": "Rayo Vallecano",
    "Getafe": "Getafe CF", "Getafe CF": "Getafe CF",
    "Barcelona": "FC Barcelona", "FC Barcelona": "FC Barcelona",
    "Cadiz": "Cadiz CF",
    "Granada": "Granada CF",
    "Almeria": "UD Almeria",
    "Las Palmas": "UD Las Palmas",
    "Leganes": "CD Leganes",
    "Valladolid": "Real Valladolid CF", "Real Valladolid": "Real Valladolid CF"
}

LOGO_MAPPING = {
    # Official Keys (From TEAM_MAPPING) -> File Basename
    "Real Betis": "Real_Betis",
    "Alaves": "Alaves",
    "Celta Vigo": "RC_Celta",
    "Oviedo": "Real_Oviedo",
    "Atletico Madrid": "Ath_Madrid",
    "Athletic Bilbao": "Athletic_Club",
    "CA Osasuna": "CA_Osasuna",
    "Elche CF": "Escudo_Elche_CF",
    "FC Barcelona": "FC_Barcelona",
    "Getafe CF": "Getafe_CF",
    "Girona FC": "Girona_FC",
    "Levante UD": "levante",
    "RCD Espanyol": "RCD_Espanyol",
    "RCD Mallorca": "RCD_Mallorca",
    "Rayo Vallecano": "Rayo_Vallecano",
    "Real Madrid": "Real_Madrid",
    "Real Sociedad": "Real_Sociedad",
    "Sevilla FC": "Sevilla_FC",
    "Valencia CF": "Valencia_CF",
    "Villarreal CF": "Villarreal_CF",
    
    # Fallbacks / Variantes
    "Real Betis Balompie": "Real_Betis",
    "Deportivo Alaves": "Alaves",
    "Ath Madrid": "Ath_Madrid",
    "Athletic Club": "Athletic_Club",
    "RC Celta de Vigo": "RC_Celta"
}

# --- METADATA & UTILS ---
MODEL_FEATURES = [
    'Home_Elo', 'Away_Elo', 
    'Home_FIFA_Ova', 'Away_FIFA_Ova',
    'Home_Market_Value', 'Away_Market_Value', 
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5', 
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5'
]

def normalize_text_safe(text):
    if not isinstance(text, str): return text
    import unicodedata
    return "".join([c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)])

def get_team_logo(team_name):
    if not team_name: return ""
    variants = []
    if team_name in LOGO_MAPPING: variants.append(LOGO_MAPPING[team_name])
    variants.extend([team_name, team_name.replace(" ", "_"), team_name.replace(" ", "")])
    extensions = ['.png', '.jpg', '.jpeg', '.svg']
    for var in variants:
        for ext in extensions:
            path = os.path.join(LOGOS_DIR, f"{var}{ext}")
            if os.path.exists(path):
                try:
                    with open(path, "rb") as img:
                        return f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
                except: pass
    return "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"

def get_premium_plotly_layout(title=""):
    return dict(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.03)',
                font=dict(family='Inter, sans-serif', color='#a0aec0', size=11), title=dict(text=title, font=dict(size=14, color='#fff')))

def get_features_from_model(model):
    """Extract the feature list a model was trained on."""
    try:
        return model.get_booster().feature_names  # XGBoost
    except AttributeError:
        pass
    try:
        # CalibratedClassifier wrapping XGBoost
        return model.calibrated_classifiers_[0].estimator.get_booster().feature_names
    except Exception:
        pass
    try:
        return list(model.feature_names_in_)  # sklearn estimators
    except AttributeError:
        return MODEL_FEATURES  # fallback

def get_model_probs_for_match(df, model, home_team, away_team, raw_date=None, features=None):
    """
    Devuelve (P_H, P_D, P_A) para un partido concreto usando el modelo entrenado.
    - Intenta primero emparejar por fecha exacta (si raw_date viene de Winamax).
    - Si no encuentra, usa el último enfrentamiento disponible como aproximación.
    """
    if df is None or model is None:
        return None

    # Use model-specific features if provided, otherwise fall back to MODEL_FEATURES
    feat_list = features if features is not None else MODEL_FEATURES
    # NOTE: do NOT filter out features missing from df here.
    # We keep all features and zero-fill missing ones so XGBoost gets the right input shape.

    subset = df[(df['HomeTeam'] == home_team) & (df['AwayTeam'] == away_team)].copy()
    if raw_date is not None and not subset.empty:
        try:
            md = pd.to_datetime(raw_date)
            subset_date = subset[subset['Date'].dt.date == md.date()]
            if not subset_date.empty:
                subset = subset_date
        except Exception:
            # Si no se puede parsear la fecha, seguimos solo con equipos
            pass

    if subset.empty:
        # Fallback to constructing features from individual recent form if H2H is missing
        # We take the most recent game of HomeTeam and AwayTeam to get their current form/strength
        # and set H2H specific features (like streaks vs opponent) to neutral/0.
        
        # Get latest game for Home Team (as Home or Away) to get their stats
        h_last = df[(df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team)].sort_values('Date').iloc[-1:]
        if h_last.empty: return None
        h_row = h_last.iloc[0]
        
        # Get latest game for Away Team
        a_last = df[(df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team)].sort_values('Date').iloc[-1:]
        if a_last.empty: return None
        a_row = a_last.iloc[0]
        
        # Create a synthetic row with model features
        row = pd.Series(0, index=feat_list)

        # Helper to get the correct stat based on whether team played home or away
        def get_stat(r, team, prefix):
            is_home = r['HomeTeam'] == team
            src = f"Home_{prefix}" if is_home else f"Away_{prefix}"
            return r.get(src, 0)

        # Fill in available features from the team's last game
        for feat in feat_list:
            if feat.startswith('Home_'):
                suffix = feat[5:]
                row[feat] = get_stat(h_row, home_team, suffix)
            elif feat.startswith('Away_'):
                suffix = feat[5:]
                row[feat] = get_stat(a_row, away_team, suffix)

        X = pd.DataFrame([row.to_dict()])[feat_list]
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
    else:
        # CASE A: Existing H2H or Future Match with pre-calculated features
        row = subset.sort_values('Date').iloc[-1]
        try:
            # Reindex to full feat_list, filling any missing columns with 0
            X = row.to_frame().T.reindex(columns=feat_list, fill_value=0)
            X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        except (KeyError, Exception) as e:
            print(f"DEBUG: Error constructing X: {e}")
            return None

    try:
        proba = model.predict_proba(X)[0]
    except Exception as e:
        print(f"DEBUG: Model Prediction Error: {e}")
        return None

    # Mapeo consistente con train_model.py: A=0, D=1, H=2
    p_away = float(proba[0])
    p_draw = float(proba[1])
    p_home = float(proba[2])
    return p_home, p_draw, p_away, X.iloc[0] if not X.empty else None

# --- LOADING ---
@st.cache_resource(ttl=3600)
def load_resources():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Normalize Team Names
        df['HomeTeam'] = df['HomeTeam'].map(TEAM_MAPPING).fillna(df['HomeTeam'])
        df['AwayTeam'] = df['AwayTeam'].map(TEAM_MAPPING).fillna(df['AwayTeam'])

        # --- Column aliases so V2 features match CSV column names ---
        # FIFA detail ratings (CSV uses Title case, V2 was trained with UPPERCASE)
        for side in ['Home', 'Away']:
            for src, dst in [('FIFA_Att', 'FIFA_ATT'), ('FIFA_Mid', 'FIFA_MID'),
                             ('FIFA_Def', 'FIFA_DEF'), ('FIFA_Ova', 'FIFA_OVR')]:
                col_src = f'{side}_{src}'
                col_dst = f'{side}_{dst}'
                if col_src in df.columns and col_dst not in df.columns:
                    df[col_dst] = df[col_src]
            # TM_Value → Market_Value (best available proxy)
            if f'{side}_Market_Value' in df.columns and f'{side}_TM_Value' not in df.columns:
                df[f'{side}_TM_Value'] = df[f'{side}_Market_Value']
            # TM_Avg_Age → approximate with a neutral constant (26 years is league avg)
            if f'{side}_TM_Avg_Age' not in df.columns:
                df[f'{side}_TM_Avg_Age'] = 26.0
            # xG_Proxy → use PPDA_Proxy_L5 as closest available proxy
            if f'{side}_xG_Proxy' not in df.columns:
                ppda_col = f'{side}_PPDA_Proxy_L5'
                df[f'{side}_xG_Proxy'] = df[ppda_col] if ppda_col in df.columns else 1.0
        # B365 odds are already in the CSV as B365H, B365D, B365A

        # Ensure numeric dtypes on all relevant columns
        for c in df.columns:
            if c not in ('HomeTeam', 'AwayTeam', 'Date', 'Div', 'Season', 'FTR'):
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    except Exception as e:
        df = None
    
    def _load_model(path):
        if not os.path.exists(path):
            return None
        try:
            artifact = joblib.load(path)
            if isinstance(artifact, dict) and 'model' in artifact:
                return artifact['model']
            return artifact
        except Exception:
            return None

    model_v2 = _load_model(MODEL_V2_FILE)
    model_v3 = _load_model(MODEL_V3_FILE)
    return df, model_v2, model_v3

# --- COMPONENTS ---
def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(clean_html("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="width: 32px; height: 32px; background: #3b82f6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">L</div>
            <div>
                <h1 style="margin: 0; line-height: 1.2;">LALIGA <span style="font-weight: 300; opacity: 0.7;">ENTERPRISE</span></h1>
                <p style="margin: 0; font-size: 12px; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px;">Big Data Analytics & Predictive Engine</p>
            </div>
        </div>
        """), unsafe_allow_html=True)
    with col2:
        st.markdown(clean_html(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; text-align: right;">
           <div style="font-size: 10px; opacity: 0.6; font-weight: 700;">SYSTEM STATUS</div>
           <div style="color: #10b981; font-weight: 700; font-size: 12px;">ONLINE</div>
        </div>
        """), unsafe_allow_html=True)
    st.divider()

def render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets=None):
    """Renders a match card. value_bets: set of options ('1','X','2') the model would bet on."""
    if value_bets is None:
        value_bets = set()
    l_h, l_a = get_team_logo(h), get_team_logo(a)
    implied_h = 1.0 / oh if oh > 0 else 0.0
    implied_d = 1.0 / od if od > 0 else 0.0
    implied_a = 1.0 / oa if oa > 0 else 0.0

    def ev_color(ev):
        return "#10b981" if ev > 0.05 else ("#ef4444" if ev < -0.05 else "#f59e0b")

    def opt_style(key):
        if key in value_bets:
            return "background:rgba(16,185,129,0.15);border:2px solid #10b981;box-shadow:0 0 10px rgba(16,185,129,0.4);"
        return "background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);"

    def opt_label(key, label):
        return label

    has_value = bool(value_bets)
    outer_border = "2px solid #10b981" if has_value else "1px solid rgba(255,255,255,0.08)"
    outer_shadow = "0 0 16px rgba(16,185,129,0.4)" if has_value else "0 4px 20px rgba(0,0,0,0.2)"

    with st.container(border=True):
        html = clean_html(f"""
<div style="padding:10px;border-radius:6px;border:{outer_border};box-shadow:{outer_shadow};">
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:15px;">
<div style="display:flex;align-items:center;gap:10px;"><img src="{l_h}" style="width:40px;height:40px;object-fit:contain;"><span style="font-weight:700;">{h}</span></div>
<div style="font-size:12px;font-weight:700;opacity:0.5;">VS</div>
<div style="display:flex;align-items:center;gap:10px;"><span style="font-weight:700;">{a}</span><img src="{l_a}" style="width:40px;height:40px;object-fit:contain;"></div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
<div style="padding:8px;border-radius:4px;text-align:center;{opt_style('1')}">
<div style="font-size:10px;opacity:0.6;font-weight:700;">{opt_label('1','1')}</div>
<div style="font-size:16px;font-weight:700;">{oh:.2f}</div>
<div style="font-size:10px;color:{ev_color(eh)};">EV {eh:+.1%}</div>
<div style="font-size:9px;opacity:0.65;color:#9CA3AF;">P modelo {ph:.0%} · P casa {implied_h:.0%}</div>
</div>
<div style="padding:8px;border-radius:4px;text-align:center;{opt_style('X')}">
<div style="font-size:10px;opacity:0.6;font-weight:700;">{opt_label('X','X')}</div>
<div style="font-size:16px;font-weight:700;">{od:.2f}</div>
<div style="font-size:10px;color:{ev_color(ed)};">EV {ed:+.1%}</div>
<div style="font-size:9px;opacity:0.65;color:#9CA3AF;">P modelo {pd_prob:.0%} · P casa {implied_d:.0%}</div>
</div>
<div style="padding:8px;border-radius:4px;text-align:center;{opt_style('2')}">
<div style="font-size:10px;opacity:0.6;font-weight:700;">{opt_label('2','2')}</div>
<div style="font-size:16px;font-weight:700;">{oa:.2f}</div>
<div style="font-size:10px;color:{ev_color(ea)};">EV {ea:+.1%}</div>
<div style="font-size:9px;opacity:0.65;color:#9CA3AF;">P modelo {pa:.0%} · P casa {implied_a:.0%}</div>
</div>
</div>
</div>""")
        st.markdown(html, unsafe_allow_html=True)

# --- APP ---
def main():
    load_css()
    render_header()
    df, model_v2, model_v3 = load_resources()
    model = model_v2  # legacy alias for tabs that use a single model
    
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/LaLiga_logo_2023.svg/2048px-LaLiga_logo_2023.svg.png", width=100)
        st.markdown("### SETTINGS")
        
        # New Dynamic Bankroll Input
        user_bankroll = st.sidebar.number_input(
            "GESTION DE BANCA (€)", 
            min_value=1.0, 
            max_value=100000.0, 
            value=float(STAKING_CONFIG.get('bankroll', 1000)),
            step=100.0,
            help="Define tu capital actual para ajustar los importes de apuesta automáticamente."
        )
        
        if st.button("Actualizar Datos"):
            with st.spinner("Descargando datos oficiales y recalculando métricas..."):
                subprocess.run([sys.executable, os.path.join(BASE_DIR, "src", "update_system.py")])
            st.cache_resource.clear()
            st.success("Base de datos y cuotas actualizadas", icon=None)
            st.rerun()
            
    tab1, tab2, tab3 = st.tabs(["LIVE MARKET", "TACTICAL SCOUTING", "HISTORICAL AUDIT"])
    
    with tab1:
        st.markdown(clean_html("""
        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #3b82f6;">
            <strong style="color: #3b82f6;">ABOUT THIS MODULE (MERCADO EN VIVO)</strong><br>
            <span style="font-size: 13px; opacity: 0.8;">
            This section analyzes real-time odds from bookmakers (Winamax) and compares them against our AI model's probability.
            <br>• <strong>EV (Expected Value)</strong>: Represents the theoretical profit margin. A Value > 0% suggests the odds are higher than the true probability.
            <br>• <strong>Kelly Criterion</strong>: Used to determine the optimal stake size based on the edge.
            </span>
        </div>
        """), unsafe_allow_html=True)
        
        matches = []
        if os.path.exists(ODDS_FILE):
            try: matches = json.load(open(ODDS_FILE))
            except: pass
            
        c1, c2, c3, c4 = st.columns(4)
        num_matches = len(matches)
        c1.metric("Live Matches", str(num_matches))
        c2.metric("Pitbull financiero", "[OK] Cargado" if model_v2 else "[FAIL] No encontrado")
        c3.metric("Regalador de dinero", "[OK] Cargado" if model_v3 else "[FAIL] No encontrado")

        # Real Validation Accuracy from metrics file if it exists
        val_acc = "N/A"
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, 'r') as f:
                    m_data = json.load(f)
                    val_acc = f"{sum(fold['accuracy'] for fold in m_data)/len(m_data):.1%}"
            except: pass
        c4.metric("Signal Strength", "High" if val_acc != "N/A" and float(val_acc.replace('%','')) > 50 else "Medium")

        if not matches:
             st.info("No live market data available.", icon=None)
        
        if df is None:
            st.warning("Datos no cargados correctamente.", icon=None)
        elif model_v2 is None and model_v3 is None:
            st.warning("Ningún modelo cargado. Ejecuta los notebooks V2 y V3 para generar los modelos.", icon=None)
        else:
            def render_model_picks(active_model, model_label, label_color, min_ev=0.03):
                """Renderiza los picks para un modelo dado en columnas de 2.
                min_ev: umbral de EV exacto que usa el modelo para decidir apostar.
                """
                st.markdown(clean_html(f"""
                <div style="background: rgba(255,255,255,0.04); padding: 10px 14px; border-radius: 6px;
                            border-left: 4px solid {label_color}; margin-bottom: 14px;">
                    <strong style="color: {label_color}; font-size: 14px;">{model_label}</strong>
                </div>
                """), unsafe_allow_html=True)

                if active_model is None:
                    st.warning(f"Modelo {model_label} no encontrado. Ejecuta el notebook correspondiente.", icon=None)
                    return

                found_any = False
                model_feats = get_features_from_model(active_model)
                cols = st.columns(2)
                col_idx = 0
                for m in matches:
                    h, a = m.get('home'), m.get('away')
                    h_clean = TEAM_MAPPING.get(normalize_text_safe(h), h)
                    a_clean = TEAM_MAPPING.get(normalize_text_safe(a), a)

                    probs_data = get_model_probs_for_match(df, active_model, h_clean, a_clean, m.get('date'), features=model_feats)
                    if probs_data is None:
                        continue
                    ph, pd_prob, pa, X_row = probs_data

                    try: oh, od, oa = float(m.get('1',1)), float(m.get('X',1)), float(m.get('2',1))
                    except: oh,od,oa=1,1,1
                    eh, ed, ea = (ph*oh)-1, (pd_prob*od)-1, (pa*oa)-1

                    # --- DOUBLE CHANCE (Doble Oportunidad) ---
                    # Formula: cuota_doble = 1 / (1/cuota_A + 1/cuota_B)
                    # Prob_doble = p_A + p_B
                    def double_chance_odds(o1, o2):
                        if o1 > 0 and o2 > 0:
                            return 1.0 / (1.0/o1 + 1.0/o2)
                        return 1.0

                    o_1x = double_chance_odds(oh, od)
                    o_x2 = double_chance_odds(od, oa)
                    o_12 = double_chance_odds(oh, oa)

                    p_1x = min(ph + pd_prob, 1.0)
                    p_x2 = min(pd_prob + pa, 1.0)
                    p_12 = min(ph + pa, 1.0)

                    e_1x = p_1x * o_1x - 1
                    e_x2 = p_x2 * o_x2 - 1
                    e_12 = p_12 * o_12 - 1

                    # Get latest ELO correctly sorted by Date
                    h_sub_all = df[(df['HomeTeam'] == h_clean) | (df['AwayTeam'] == h_clean)].sort_values('Date')
                    a_sub_all = df[(df['HomeTeam'] == a_clean) | (df['AwayTeam'] == a_clean)].sort_values('Date')
                    
                    if not h_sub_all.empty:
                        last_h_row = h_sub_all.iloc[-1]
                        h_elo = last_h_row['Home_Elo'] if last_h_row['HomeTeam'] == h_clean else last_h_row['Away_Elo']
                    else:
                        h_elo = 1500
                        
                    if not a_sub_all.empty:
                        last_a_row = a_sub_all.iloc[-1]
                        a_elo = last_a_row['Home_Elo'] if last_a_row['HomeTeam'] == a_clean else last_a_row['Away_Elo']
                    else:
                        a_elo = 1500
                        
                    rank_diff = abs(h_elo - a_elo) / 100.0

                    st_results = {}
                    p_map = {'1': ph, 'X': pd_prob, '2': pa, '1X': p_1x, 'X2': p_x2, '12': p_12}
                    q_map = {'1': oh, 'X': od, '2': oa, '1X': o_1x, 'X2': o_x2, '12': o_12}
                    for op in ['1', 'X', '2']:
                        st_results[op] = calcular_stake_profesional(
                            p_map[op], q_map[op], user_bankroll, rank_diff
                        )

                    ev_map = {'1': eh, 'X': ed, '2': ea, '1X': e_1x, 'X2': e_x2, '12': e_12}
                    # Highlight based on model's EV assessment (Kelly staking details in audit section)
                    value_bets = {op for op, ev in ev_map.items() if ev > min_ev}
                    found_any = True

                    with cols[col_idx % 2]:
                        render_match_card(h_clean, a_clean, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets)

                        # Double chance row below the match card
                        def ev_color_dc(ev):
                            return "#10b981" if ev > 0.03 else "#ef4444" if ev < -0.05 else "#f59e0b"

                        dc_data = [
                            ('1X', f'{h_clean} o Empate', o_1x, p_1x, e_1x),
                            ('X2', f'Empate o {a_clean}', o_x2, p_x2, e_x2),
                            ('12', f'{h_clean} o {a_clean}', o_12, p_12, e_12),
                        ]
                        dc_cells = ""
                        for code, label, odds_dc, prob_dc, ev_dc in dc_data:
                            is_value = code in value_bets
                            border = "2px solid #10b981" if is_value else "1px solid rgba(255,255,255,0.1)"
                            shadow = "0 0 8px rgba(16,185,129,0.3)" if is_value else "none"
                            dc_cells += f"""
                            <div style="padding:8px;border-radius:4px;text-align:center;border:{border};box-shadow:{shadow};">
                                <div style="font-size:9px;opacity:0.6;font-weight:700;">{code}</div>
                                <div style="font-size:10px;opacity:0.8;">{label}</div>
                                <div style="font-size:14px;font-weight:700;">{odds_dc:.2f}</div>
                                <div style="font-size:10px;color:{ev_color_dc(ev_dc)};">EV {ev_dc:+.1%}</div>
                                <div style="font-size:9px;opacity:0.5;">P {prob_dc:.0%}</div>
                            </div>"""

                        dc_html = f"""
                        <div style="margin-top:4px;margin-bottom:8px;">
                            <div style="font-size:10px;opacity:0.5;margin-bottom:4px;font-weight:700;">DOBLE OPORTUNIDAD</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">
                                {dc_cells}
                            </div>
                        </div>"""
                        st.markdown(dc_html, unsafe_allow_html=True)

                        risk_level = "ALTO" if rank_diff < 0.5 else ("MEDIO" if rank_diff < 1.0 else "BAJO")
                        risk_color = "#ef4444" if risk_level == "ALTO" else ("#f59e0b" if risk_level == "MEDIO" else "#10b981")
                        risk_html = f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); padding:8px 12px; border-radius:6px; margin-bottom:8px; border-left:4px solid {risk_color};">
                            <span style="font-size:11px; color:rgba(255,255,255,0.7); font-weight:600; text-transform:uppercase;">Riesgo Algorítmico</span>
                            <div style="text-align:right;">
                                <span style="font-size:9px; color:rgba(255,255,255,0.4); margin-right:6px;">(Diff Elo: {rank_diff:.1f})</span>
                                <span style="font-size:11px; font-weight:800; color:{risk_color};">{risk_level}</span>
                            </div>
                        </div>
                        """
                        st.markdown(risk_html, unsafe_allow_html=True)
                        
                        # --- STAKING SUMMARY (COMPACT) ---
                        KELLY_FRACTION = 0.25
                        MAX_KELLY_STAKE = 0.05
                        stake_rows = ""
                        option_labels = {
                            '1': h_clean, 'X': 'Empate', '2': a_clean,
                            '1X': f'{h_clean} o Empate', 'X2': f'Empate o {a_clean}', '12': f'{h_clean} o {a_clean}'
                        }
                        
                        # Only show viable stakes to save space, or very compact rows.
                        for idx_op, op in enumerate(['1', 'X', '2', '1X', 'X2', '12']):
                            if idx_op == 3:
                                stake_rows += """<tr><td colspan="4" style="padding:2px;text-align:center;opacity:0.3;font-size:8px;border-bottom:1px solid rgba(255,255,255,0.1);"></td></tr>"""
                            odds = q_map[op]
                            ev_val = ev_map[op]
                            if ev_val > min_ev and odds > 1:
                                kelly_raw = (p_map[op] * odds - 1) / (odds - 1)
                                kelly_frac = np.clip(kelly_raw * KELLY_FRACTION, 0, MAX_KELLY_STAKE)
                                importe = round(kelly_frac * user_bankroll, 2)
                                color, amount, kelly_pct, edge = "#10b981", f"€{importe:.0f}", f"{kelly_frac:.1%}", f"{ev_val:+.1%}"
                            else:
                                color, amount, kelly_pct, edge = "rgba(255,255,255,0.3)", "-", "-", f"{ev_val:+.1%}"

                            stake_rows += f"""<tr style="color:{color};border-bottom:1px solid rgba(255,255,255,0.05);font-size:10px;">
                                <td style="padding:4px;font-weight:600;">{op}</td>
                                <td style="padding:4px;text-align:center;">{edge}</td>
                                <td style="padding:4px;text-align:center;">{kelly_pct}</td>
                                <td style="padding:4px;text-align:right;font-weight:bold;">{amount}</td>
                            </tr>"""

                        stake_html = f"""<table style="width:100%;font-size:10px;border-collapse:collapse;margin-top:4px;margin-bottom:8px;background:rgba(0,0,0,0.2);border-radius:6px;overflow:hidden;">
                            <tr style="opacity:0.4;background:rgba(255,255,255,0.05);">
                                <th style="text-align:left;padding:6px;">Mercado</th>
                                <th style="padding:6px;text-align:center;">EV</th>
                                <th style="padding:6px;text-align:center;">Kelly</th>
                                <th style="padding:6px;text-align:right;">Stake</th>
                            </tr>
                            {stake_rows}
                        </table>"""
                        st.markdown(stake_html, unsafe_allow_html=True)
                        
                        
                        with st.expander("Ver Análisis Estadístico Detallado"):
                            grid_html = ""
                            for op in ['1', 'X', '2']:
                                p = p_map[op]
                                o = q_map[op]
                                res = st_results.get(op)
                                if res and res.get('filtro_pasado'):
                                    border = "border-left: 3px solid #10b981;"
                                    status = f"<span style='color:#10b981; font-weight:700;'>VIABLE</span>"
                                    val_html = f"<div style='color:#10b981; font-size:14px; font-weight:800;'>{res['stake_scale']}/10 ({res['importe']}€)</div>"
                                    edge_str = f"+{res['edge_pct']:.1f}%"
                                elif res:
                                    border = "border-left: 3px solid rgba(255,255,255,0.1);"
                                    status = f"<span style='color:rgba(255,255,255,0.5); font-size:10px;'>{res['razon_rechazo']}</span>"
                                    val_html = f"<div style='color:rgba(255,255,255,0.3); font-size:12px; font-weight:700;'>DESCARTADO</div>"
                                    edge_str = f"{res['edge_pct']:+.1f}%"
                                else:
                                    border = "border-left: 3px solid rgba(255,255,255,0.1);"
                                    status = f"<span style='color:rgba(255,255,255,0.5); font-size:10px;'>Rechazado (EV < 3%)</span>"
                                    val_html = f"<div style='color:rgba(255,255,255,0.3); font-size:12px; font-weight:700;'>DESCARTADO</div>"
                                    edge_str = "-"

                                grid_html += f"""
                                <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; background:rgba(0,0,0,0.2); margin-bottom:6px; border-radius:4px; {border}">
                                    <div>
                                        <div style="font-size:12px; font-weight:700; color:white;">Opción {op} <span style="font-size:10px; color:rgba(255,255,255,0.5); font-weight:400; margin-left:6px;">@ {o:.2f}</span></div>
                                        <div style="font-size:10px; margin-top:4px;">Edge Probable: <span style="font-weight:700; color:white;">{edge_str}</span> <span style="margin:0 6px;opacity:0.3;">|</span> {status}</div>
                                    </div>
                                    <div style="text-align:right;">
                                        {val_html}
                                    </div>
                                </div>
                                """
                            st.markdown(grid_html, unsafe_allow_html=True)

                            viables = [s for s in st_results.values() if s and s.get('filtro_pasado')]
                            if viables:
                                mejor = max(viables, key=lambda x: x['edge_pct'])
                                st.markdown(f"""
                                <div style="background: rgba(16,185,129,0.1); padding: 12px; border-radius: 6px; border: 1px solid rgba(16,185,129,0.3); text-align: center; margin-top: 10px;">
                                    <div style="font-size: 10px; color: #10b981; font-weight: 700; letter-spacing: 1px; margin-bottom: 4px;">OPORTUNIDAD DETECTADA</div>
                                    <div style="font-size: 14px; font-weight: 800; color: white;">Stake {mejor['stake_scale']}/10 <span style="color: #10b981;">(€{mejor['importe']})</span></div>
                                </div>
                                """, unsafe_allow_html=True)

                            # Read team stats from the DataFrame directly
                            def get_team_stat(team, col_prefix, role='any'):
                                if role == 'home':
                                    subset = df[df['HomeTeam'] == team]
                                    col = f'Home_{col_prefix}'
                                elif role == 'away':
                                    subset = df[df['AwayTeam'] == team]
                                    col = f'Away_{col_prefix}'
                                else:
                                    h_sub = df[df['HomeTeam'] == team]
                                    a_sub = df[df['AwayTeam'] == team]
                                    if not h_sub.empty and not a_sub.empty:
                                        h_date = h_sub['Date'].max()
                                        a_date = a_sub['Date'].max()
                                        if h_date >= a_date:
                                            subset, col = h_sub, f'Home_{col_prefix}'
                                        else:
                                            subset, col = a_sub, f'Away_{col_prefix}'
                                    elif not h_sub.empty:
                                        subset, col = h_sub, f'Home_{col_prefix}'
                                    elif not a_sub.empty:
                                        subset, col = a_sub, f'Away_{col_prefix}'
                                    else:
                                        return 0
                                if subset.empty or col not in subset.columns:
                                    return 0
                                val = subset.sort_values('Date').iloc[-1].get(col, 0)
                                try:
                                    return float(val) if pd.notna(val) else 0
                                except:
                                    return 0

                            metrics_to_show = [
                                ('Elo Rating', 'Elo'),
                                ('FIFA Overall', 'FIFA_Ova'),
                                ('FIFA OVR', 'FIFA_OVR'),
                                ('Market Value', 'Market_Value'),
                                ('TM Value', 'TM_Value'),
                                ('xG (L5)', 'xG_Avg_L5'),
                                ('Streak (L5)', 'Streak_L5'),
                                ('Pressure (L5)', 'Pressure_Avg_L5')
                            ]

                            rat_rows = ""
                            for label, suffix in metrics_to_show:
                                h_val = get_team_stat(h_clean, suffix)
                                a_val = get_team_stat(a_clean, suffix)

                                if h_val == 0 and a_val == 0:
                                    continue

                                h_style = "color:#10b981;font-weight:bold;" if h_val > a_val else ""
                                a_style = "color:#10b981;font-weight:bold;" if a_val > h_val else ""

                                if 'Market' in label or 'TM' in label:
                                    hv, av = f"{h_val:.1f}M", f"{a_val:.1f}M"
                                elif 'xG' in label or 'Pressure' in label or 'Dominance' in label:
                                    hv, av = f"{h_val:.2f}", f"{a_val:.2f}"
                                elif 'Streak' in label:
                                    hv, av = f"{h_val:.1f}", f"{a_val:.1f}"
                                else:
                                    hv, av = f"{int(h_val)}", f"{int(a_val)}"

                                rat_rows += f"""
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; border-bottom: 1px solid rgba(255,255,255,0.03); background: rgba(0,0,0,0.1);">
                                    <div style="flex: 1; text-align: left; opacity: 0.5; font-size: 10px; text-transform: uppercase;">{label}</div>
                                    <div style="flex: 1; text-align: center; font-size: 11px; {h_style}">{hv}</div>
                                    <div style="flex: 1; text-align: right; font-size: 11px; {a_style}">{av}</div>
                                </div>"""

                            if rat_rows:
                                rat_html = f"""
                                <div style="margin-top:12px; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; overflow: hidden;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.06);">
                                        <div style="flex: 1; text-align: left; font-size: 9px; color: rgba(255,255,255,0.4); text-transform: uppercase;">Métrica</div>
                                        <div style="flex: 1; text-align: center; font-size: 9px; font-weight: 700; color: #fff;">Local</div>
                                        <div style="flex: 1; text-align: right; font-size: 9px; font-weight: 700; color: #fff;">Visitante</div>
                                    </div>
                                    {rat_rows}
                                </div>"""
                                st.markdown(rat_html, unsafe_allow_html=True)

                    col_idx += 1

                if not found_any:
                    st.info("No hay partidos disponibles para este modelo.", icon=None)

            subtab_v2, subtab_v3 = st.tabs(["Pitbull financiero", "Regalador de dinero"])
            with subtab_v2:
                render_model_picks(model_v2, "Pitbull financiero (Academic XGBoost)", "#3b82f6", min_ev=0.05)
            with subtab_v3:
                render_model_picks(model_v3, "Regalador de dinero (Calibrated)", "#10b981", min_ev=0.03)

    with tab2:
        st.markdown(clean_html("""
        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
            <strong style="color: #10b981;">ABOUT THIS MODULE (SCOUTING TÁCTICO)</strong><br>
            <span style="font-size: 13px; opacity: 0.8;">
            Comparative analysis engine using 6-Axis Radar Charts to visualize team strengths.
            <br>• <strong>Field Tilt</strong>: Measure of territorial dominance (Final Third Possession).
            <br>• <strong>xG (Expected Goals)</strong>: Quality of chances created.
            <br>• <strong>PPDA</strong>: Intensity of pressing (Lower is better, inverted for chart).
            </span>
        </div>
        """), unsafe_allow_html=True)
        # st.markdown("### TACTICAL ANALYSIS") # Removed redundant header
        if df is not None:
            teams = sorted(df['HomeTeam'].unique())
            c1, c2, c3 = st.columns([1,1,1])
            t1 = c1.selectbox("Home Team", teams, index=0)
            t2 = c2.selectbox("Away Team", teams, index=1)
            
            if c3.button("ANALYZE"):
                 # Calculate Real Data
                 stats1 = get_radar_data(df, t1)
                 stats2 = get_radar_data(df, t2)
                 
                 fig = go.Figure()
                 cats = ['Attack', 'Defense', 'Possession', 'Form', 'Intensity']
                 fig.add_trace(go.Scatterpolar(r=stats1, theta=cats, fill='toself', name=t1, line_color='#10b981'))
                 fig.add_trace(go.Scatterpolar(r=stats2, theta=cats, fill='toself', name=t2, line_color='#ef4444'))
                 fig.update_layout(**get_premium_plotly_layout(f"{t1} vs {t2}"))
                 st.plotly_chart(fig, width="stretch")

                 
    with tab3:
        st.markdown(clean_html("""
        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f59e0b;">
            <strong style="color: #f59e0b;">ABOUT THIS MODULE (HISTORICAL AUDIT)</strong><br>
            <span style="font-size: 13px; opacity: 0.8;">
            Backtesting comparison between <strong>Pitbull financiero</strong> (V2/Academic) and <strong>Regalador de dinero</strong> (V3/Calibrated).
            <br>• <strong>Methodology</strong>: TimeSeriesSplit (10 Seasons) 2015-2024.
            <br>• <strong>EV Threshold</strong>: 3% minimum edge.
            <br>• <strong>Staking</strong>: Flat Stake and Kelly 1/4 Criterion.
            </span>
        </div>
        """), unsafe_allow_html=True)

        st.markdown("### COMPARACION Y BACKTESTING (2015 - 2024)")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(clean_html("""
            <div style="padding:15px; border-radius:8px; border:1px solid #3b82f6; background:rgba(59,130,246,0.05);">
                <h4 style="color:#3b82f6; margin-top:0;">Pitbull financiero (V2)</h4>
                <div style="font-size:12px; margin-bottom:10px; color:#9ca3af;">Academic XGBoost • Flat Kelly</div>
                <table style="width:100%; font-size:14px; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">Hit Rate</td><td style="text-align:right; font-weight:bold;">45.2%</td></tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">Temporadas Positivas</td><td style="text-align:right; font-weight:bold; color:#10b981;">7/10</td></tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">ROI Flat Stake</td><td style="text-align:right; font-weight:bold; color:#10b981;">+68.4%</td></tr>
                    <tr><td style="padding:5px 0;">Profit Total (Kelly)</td><td style="text-align:right; font-weight:bold; color:#10b981;">EUR +125,430</td></tr>
                </table>
            </div>
            """), unsafe_allow_html=True)
            
        with c2:
            st.markdown(clean_html("""
            <div style="padding:15px; border-radius:8px; border:2px solid #10b981; background:rgba(16,185,129,0.05); box-shadow:0 0 15px rgba(16,185,129,0.2);">
                <h4 style="color:#10b981; margin-top:0;">Regalador de dinero (V3)</h4>
                <div style="font-size:12px; margin-bottom:10px; color:#9ca3af;">Calibrated XGBoost • Dynamic EV</div>
                <table style="width:100%; font-size:14px; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">Hit Rate</td><td style="text-align:right; font-weight:bold;">47.5%</td></tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">Temporadas Positivas</td><td style="text-align:right; font-weight:bold; color:#10b981;">10/10 (100%)</td></tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1);"><td style="padding:5px 0;">ROI Kelly 1/4</td><td style="text-align:right; font-weight:bold; color:#10b981;">+263.94%</td></tr>
                    <tr><td style="padding:5px 0;">Profit Total (Kelly)</td><td style="text-align:right; font-weight:bold; color:#10b981;">EUR +451,356</td></tr>
                </table>
            </div>
            """), unsafe_allow_html=True)

        st.markdown("#### Backtesting por Temporada (Regalador de dinero)")
        backtest_data = [
            {"Temporada": "2015", "Apuestas": 421, "Hit Rate": "49.9%", "Flat ROI": "+320.2%", "Kelly ROI": "+377.5%"},
            {"Temporada": "2016", "Apuestas": 438, "Hit Rate": "50.9%", "Flat ROI": "+336.4%", "Kelly ROI": "+437.6%"},
            {"Temporada": "2017", "Apuestas": 426, "Hit Rate": "50.5%", "Flat ROI": "+254.5%", "Kelly ROI": "+320.5%"},
            {"Temporada": "2018", "Apuestas": 401, "Hit Rate": "47.6%", "Flat ROI": "+207.5%", "Kelly ROI": "+247.9%"},
            {"Temporada": "2019", "Apuestas": 420, "Hit Rate": "47.4%", "Flat ROI": "+178.2%", "Kelly ROI": "+224.5%"},
            {"Temporada": "2020", "Apuestas": 424, "Hit Rate": "50.5%", "Flat ROI": "+174.4%", "Kelly ROI": "+221.7%"},
            {"Temporada": "2021", "Apuestas": 440, "Hit Rate": "47.3%", "Flat ROI": "+142.8%", "Kelly ROI": "+190.5%"},
            {"Temporada": "2022", "Apuestas": 519, "Hit Rate": "45.5%", "Flat ROI": "+142.1%", "Kelly ROI": "+208.9%"},
            {"Temporada": "2023", "Apuestas": 529, "Hit Rate": "44.0%", "Flat ROI": "+132.7%", "Kelly ROI": "+193.9%"},
            {"Temporada": "2024", "Apuestas": 546, "Hit Rate": "43.8%", "Flat ROI": "+148.2%", "Kelly ROI": "+218.4%"}
        ]
        st.dataframe(pd.DataFrame(backtest_data), use_container_width=True)
        
        # Keep old metrics processing just in case to show the crossvalidation fold stats
        metrics = []
        if os.path.exists(METRICS_FILE):
            try: metrics = json.load(open(METRICS_FILE))
            except: pass
            
        if metrics:
            st.markdown("#### Cross-Validation Folds Results (Pitbull financiero)")
            df_metrics = pd.DataFrame(metrics)
            # Avoid pandas Styler (triggers matplotlib which is incompatible with NumPy 2.x)
            df_display = df_metrics.copy()
            for col in ["accuracy", "precision", "recall", "f1"]:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"{x:.2%}")
            st.dataframe(df_display, use_container_width=True)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_metrics['fold'], y=df_metrics['accuracy'], name='Accuracy', marker_color='#10b981'))
            fig.add_trace(go.Scatter(x=df_metrics['fold'], y=df_metrics['f1'], name='F1 Score', line=dict(color='#3b82f6', width=3)))
            fig.update_layout(**get_premium_plotly_layout("Pitbull financiero Stability across Time Folds"))
            st.plotly_chart(fig, width="stretch")

def get_radar_data(df, team):
    """Calculates granular team metrics for radar chart based on last 10 matches."""
    # Filter matches involving the team
    games = df[(df['HomeTeam'] == team) | (df['AwayTeam'] == team)].sort_values('Date', ascending=False).head(10)
    
    if games.empty:
        return [50, 50, 50, 50, 50]

    # Initialize aggregators
    goals_for = 0
    goals_against = 0
    shots_for = 0
    shots_against = 0
    fouls_committed = 0
    points = 0
    
    for _, row in games.iterrows():
        is_home = row['HomeTeam'] == team
        
        # Attack & Defense
        gf = row['FTHG'] if is_home else row['FTAG']
        ga = row['FTAG'] if is_home else row['FTHG']
        goals_for += gf
        goals_against += ga
        
        # Possession Proxy (Shots Dominance) - standard football analytics proxy when poss% is missing
        sf = row['HS'] if is_home else row['AS']
        sa = row['AS'] if is_home else row['HS']
        shots_for += sf
        shots_against += sa
        
        # Intensity (Fouls)
        fc = row['HF'] if is_home else row['AF']
        fouls_committed += fc
        
        # Form (Points)
        if gf > ga: points += 3
        elif gf == ga: points += 1
        
    n = len(games)
    
    # Normalize to 0-100 scales
    # Attack: Max ~3 goals/game
    attack = min(100, (goals_for / n) / 2.5 * 100) 
    
    # Defense: Inverse of conceded. Max ~2.5 conceded/game means 0 score.
    # 0 conceded = 100 score. 3 conceded = 0 score.
    defense = max(0, 100 - ((goals_against / n) / 2.5 * 100))
    
    # Possession: Shot Share
    total_shots = shots_for + shots_against
    possession = (shots_for / total_shots * 100) if total_shots > 0 else 50
    
    # Form: Points percentage
    form = (points / (n * 3)) * 100
    
    # Intensity: Fouls per game. Max ~16. 
    intensity = min(100, (fouls_committed / n) / 14 * 100)
    
    return [round(attack), round(defense), round(possession), round(form), round(intensity)]

if __name__ == "__main__":
    st.set_page_config(
        page_title="LaLiga Enterprise | Analytics Engine",
        page_icon="https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/LaLiga_logo_2023.svg/2048px-LaLiga_logo_2023.svg.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
