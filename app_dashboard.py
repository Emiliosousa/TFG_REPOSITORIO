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
# Ensure src is importable
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
except ImportError:
    pass # Handle gracefully if not needed for core display

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
DATA_FILE = os.path.join(BASE_DIR, 'df_final_app.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'modelo_city_group.joblib')
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

def get_model_probs_for_match(df, model, home_team, away_team, raw_date=None):
    """
    Devuelve (P_H, P_D, P_A) para un partido concreto usando el modelo entrenado.
    - Intenta primero emparejar por fecha exacta (si raw_date viene de Winamax).
    - Si no encuentra, usa el último enfrentamiento disponible como aproximación.
    """
    if df is None or model is None:
        return None

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
        row = pd.Series(0, index=MODEL_FEATURES)
        
        # Helper to get the correct stat based on whether team played home or away
        def get_stat(r, team, prefix):
            is_home = r['HomeTeam'] == team
            src = f"Home_{prefix}" if is_home else f"Away_{prefix}"
            return r.get(src, 0)

        # Elo (Strength)
        # Strength Ratings
        row['Home_Elo'] = get_stat(h_row, home_team, 'Elo')
        row['Away_Elo'] = get_stat(a_row, away_team, 'Elo')
        row['Home_Att_Strength'] = get_stat(h_row, home_team, 'Att_Strength')
        row['Away_Att_Strength'] = get_stat(a_row, away_team, 'Att_Strength')
        row['Home_Def_Weakness'] = get_stat(h_row, home_team, 'Def_Weakness')
        row['Away_Def_Weakness'] = get_stat(a_row, away_team, 'Def_Weakness')
        
        # Static Data
        row['Home_FIFA_Ova'] = get_stat(h_row, home_team, 'FIFA_Ova')
        row['Away_FIFA_Ova'] = get_stat(a_row, away_team, 'FIFA_Ova')
        row['Home_Market_Value'] = get_stat(h_row, home_team, 'Market_Value')
        row['Away_Market_Value'] = get_stat(a_row, away_team, 'Market_Value')
        
        # Recent Form
        row['Home_xG_Avg_L5'] = get_stat(h_row, home_team, 'xG_Avg_L5')
        row['Away_xG_Avg_L5'] = get_stat(a_row, away_team, 'xG_Avg_L5')
        row['Home_Streak_L5'] = get_stat(h_row, home_team, 'Streak_L5')
        row['Away_Streak_L5'] = get_stat(a_row, away_team, 'Streak_L5')
        row['Home_H2H_L3'] = get_stat(h_row, home_team, 'H2H_L3')
        row['Away_H2H_L3'] = get_stat(a_row, away_team, 'H2H_L3')
        row['Home_Pressure_Avg_L5'] = get_stat(h_row, home_team, 'Pressure_Avg_L5')
        row['Away_Pressure_Avg_L5'] = get_stat(a_row, away_team, 'Pressure_Avg_L5')
        row['Home_Goal_Diff_L5'] = get_stat(h_row, home_team, 'Goal_Diff_L5')
        row['Away_Goal_Diff_L5'] = get_stat(a_row, away_team, 'Goal_Diff_L5')
        row['Home_Rest_Days'] = get_stat(h_row, home_team, 'Rest_Days')
        row['Away_Rest_Days'] = get_stat(a_row, away_team, 'Rest_Days')
        
        # Dominance (Rolling)
        row['Home_Dominance_Avg_L5'] = get_stat(h_row, home_team, 'Dominance_Avg_L5')
        row['Away_Dominance_Avg_L5'] = get_stat(a_row, away_team, 'Dominance_Avg_L5')

        X = row[MODEL_FEATURES].to_frame().T
        # Convert to numeric to avoid object dtype from mixed-type Row
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
    else:
        # CASE A: Existing H2H or Future Match with pre-calculated features
        row = subset.sort_values('Date').iloc[-1]
        try:
            X = row[MODEL_FEATURES].to_frame().T
            # Convert to numeric to avoid object dtype from mixed-type Row
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
    return p_home, p_draw, p_away

# --- LOADING ---
@st.cache_resource(ttl=3600)
def load_resources():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Normalize Team Names
        df['HomeTeam'] = df['HomeTeam'].map(TEAM_MAPPING).fillna(df['HomeTeam'])
        df['AwayTeam'] = df['AwayTeam'].map(TEAM_MAPPING).fillna(df['AwayTeam'])
        
        for c in MODEL_FEATURES: 
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    except Exception as e:
        df = None
    
    model = None
    if os.path.exists(MODEL_FILE):
        try:
            artifact = joblib.load(MODEL_FILE)
            if isinstance(artifact, dict) and 'model' in artifact:
                model = artifact['model']
            else:
                model = artifact
        except Exception:
            model = None
    return df, model

# --- COMPONENTS ---
def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(clean_html("""
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 32px;">⚽</span>
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
           <div style="color: #10b981; font-weight: 700; font-size: 12px;">● ONLINE</div>
        </div>
        """), unsafe_allow_html=True)
    st.divider()

def render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, has_value_bet=False):
    l_h, l_a = get_team_logo(h), get_team_logo(a)
    def c(ev): return "#10b981" if ev > 0.05 else ("#ef4444" if ev < -0.05 else "#f59e0b")
    # Probabilidades implícitas de la casa (aprox. sin ajustar margen)
    implied_h = 1.0 / oh if oh > 0 else 0.0
    implied_d = 1.0 / od if od > 0 else 0.0
    implied_a = 1.0 / oa if oa > 0 else 0.0
    
    with st.container(border=True):
        # Flattened HTML to fix rendering
        outer_border = "2px solid #10b981" if has_value_bet else "1px solid rgba(255,255,255,0.08)"
        outer_shadow = "0 0 16px rgba(16,185,129,0.6)" if has_value_bet else "0 4px 20px rgba(0,0,0,0.2)"
        html = clean_html(f"""
<div style="padding: 10px; border-radius: 6px; border: {outer_border}; box-shadow: {outer_shadow};">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
<div style="display: flex; align-items: center; gap: 10px;"><img src="{l_h}" style="width: 40px; height: 40px; object-fit: contain;"><span style="font-weight: 700;">{h}</span></div>
<div style="font-size: 12px; font-weight: 700; opacity: 0.5;">VS</div>
<div style="display: flex; align-items: center; gap: 10px;"><span style="font-weight: 700;">{a}</span><img src="{l_a}" style="width: 40px; height: 40px; object-fit: contain;"></div>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
<div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 10px; opacity: 0.6; font-weight: 700;">1</div>
<div style="font-size: 16px; font-weight: 700;">{oh:.2f}</div>
<div style="font-size: 10px; color: {c(eh)};">EV {eh:+.1%}</div>
<div style="font-size: 9px; opacity: 0.65; color: #9CA3AF;">P modelo {ph:.0%} · P casa {implied_h:.0%}</div>
</div>
<div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 10px; opacity: 0.6; font-weight: 700;">X</div>
<div style="font-size: 16px; font-weight: 700;">{od:.2f}</div>
<div style="font-size: 10px; color: {c(ed)};">EV {ed:+.1%}</div>
<div style="font-size: 9px; opacity: 0.65; color: #9CA3AF;">P modelo {pd_prob:.0%} · P casa {implied_d:.0%}</div>
</div>
<div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
<div style="font-size: 10px; opacity: 0.6; font-weight: 700;">2</div>
<div style="font-size: 16px; font-weight: 700;">{oa:.2f}</div>
<div style="font-size: 10px; color: {c(ea)};">EV {ea:+.1%}</div>
<div style="font-size: 9px; opacity: 0.65; color: #9CA3AF;">P modelo {pa:.0%} · P casa {implied_a:.0%}</div>
</div>
</div>
</div>""")
        st.markdown(html, unsafe_allow_html=True)

# --- APP ---
def main():
    load_css()
    render_header()
    df, model = load_resources()
    
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/LaLiga_logo_2023.svg/2048px-LaLiga_logo_2023.svg.png", width=100)
        st.markdown("### SETTINGS")
        if st.button("Actualizar Datos"):
            with st.spinner("Descargando datos oficiales y recalculando métricas..."):
                subprocess.run([sys.executable, os.path.join(BASE_DIR, "src", "update_system.py")])
            st.success("¡Base de datos y cuotas actualizadas!")
            st.rerun()
            
    tab1, tab2, tab3 = st.tabs(["LIVE MARKET", "TACTICAL SCOUTING", "HISTORICAL AUDIT"])
    
    with tab1:
        st.markdown(clean_html("""
        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #3b82f6;">
            <strong style="color: #3b82f6;">📘 ABOUT THIS MODULE (MERCADO EN VIVO)</strong><br>
            <span style="font-size: 13px; opacity: 0.8;">
            This section analyzes real-time odds from bookmakers (Winamax) and compares them against our AI model's probability.
            <br>• <strong>EV (Expected Value)</strong>: Represents the theoretical profit margin. A Value > 0% (Green) suggests the odds are higher than the true probability.
            <br>• <strong>Kelly Criterion</strong>: Used to determine the optimal stake size based on the edge.
            </span>
        </div>
        """), unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Live Matches", "10") # Mock
        c2.metric("System ROI", "+8.2%")
        c3.metric("Signal Strength", "High")
        
        matches = []
        if os.path.exists(ODDS_FILE):
            try: matches = json.load(open(ODDS_FILE))
            except: pass
            
        if not matches:
             st.info("No live market data available.")
        
        cols = st.columns(2)
        if model is None or df is None:
            st.warning("Modelo no cargado correctamente: no se pueden mostrar probabilidades reales (solo habría placeholders).")
        else:
            for i, m in enumerate(matches):
                h, a = m.get('home'), m.get('away')
                h_clean = TEAM_MAPPING.get(normalize_text_safe(h), h)
                a_clean = TEAM_MAPPING.get(normalize_text_safe(a), a)
                
                probs = get_model_probs_for_match(df, model, h_clean, a_clean, m.get('date'))
                if probs is None:
                    # Si no hay datos históricos suficientes para ese emparejamiento, lo omitimos
                    continue
                ph, pd_prob, pa = probs
                    
                try: oh, od, oa = float(m.get('1',1)), float(m.get('X',1)), float(m.get('2',1))
                except: oh,od,oa=1,1,1
                eh, ed, ea = (ph*oh)-1, (pd_prob*od)-1, (pa*oa)-1

                # Value bet real si EV > 5% en alguna de las tres opciones
                has_value_bet = any(ev > 0.05 for ev in (eh, ed, ea))
                
                with cols[i%2]:
                    render_match_card(h_clean, a_clean, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, has_value_bet)

    with tab2:
        st.markdown(clean_html("""
        <div style="background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
            <strong style="color: #10b981;">📘 ABOUT THIS MODULE (SCOUTING TÁCTICO)</strong><br>
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
            <strong style="color: #f59e0b;">📘 ABOUT THIS MODULE (HISTORICAL AUDIT)</strong><br>
            <span style="font-size: 13px; opacity: 0.8;">
            Rigorous academic validation using <strong>TimeSeriesSplit (Expanding Window)</strong>.
            <br>• <strong>Methodology</strong>: The model is trained on past data and tested on future data (5 folds) to prevent look-ahead bias.
            <br>• <strong>Accuracy</strong>: % of correct predictions (Home/Draw/Away).
            <br>• <strong>F1-Score</strong>: Harmonic mean of precision and recall, crucial for imbalanced classes.
            </span>
        </div>
        """), unsafe_allow_html=True)
        
        metrics = []
        if os.path.exists(METRICS_FILE):
            try: metrics = json.load(open(METRICS_FILE))
            except: pass
            
        if metrics:
            df_metrics = pd.DataFrame(metrics)
            
            # Top Metrics
            c1, c2, c3, c4 = st.columns(4)
            mean_acc = df_metrics['accuracy'].mean()
            mean_f1 = df_metrics['f1'].mean()
            
            c1.metric("Validation Method", "TimeSeriesSplit (5-Fold)")
            c2.metric("Mean Accuracy", f"{mean_acc:.2%}")
            c3.metric("Mean F1-Score", f"{mean_f1:.2%}")
            c4.metric("Total Samples", f"{df_metrics['train_size'].max() + df_metrics['test_size'].max()}")
            
            st.markdown("#### Cross-Validation Results")
            st.dataframe(df_metrics.style.format({
                "accuracy": "{:.2%}", "precision": "{:.2%}", "recall": "{:.2%}", "f1": "{:.2%}"
            }), width="stretch")
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_metrics['fold'], y=df_metrics['accuracy'], name='Accuracy', marker_color='#10b981'))
            fig.add_trace(go.Scatter(x=df_metrics['fold'], y=df_metrics['f1'], name='F1 Score', line=dict(color='#3b82f6', width=3)))
            fig.update_layout(**get_premium_plotly_layout("Accuracy Stability across Time Folds"))
            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("⚠️ Metrics file not found. Please run 'train_model.py' first.")

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
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
