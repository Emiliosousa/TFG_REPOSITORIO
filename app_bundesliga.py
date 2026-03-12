import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import os
import json
import re
import unicodedata
import subprocess
import sys

# ══════════════════════════════════════════════════════════════════════════════
#  BUNDESLIGA ANALYTICS ENGINE  –  Official-Grade Dashboard
# ══════════════════════════════════════════════════════════════════════════════

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDESLIGA_DIR = os.path.join(BASE_DIR, 'BUNDESLIGA')
if not os.path.exists(BUNDESLIGA_DIR):
    BUNDESLIGA_DIR = BASE_DIR

DATA_FILE = os.path.join(BUNDESLIGA_DIR, 'data', 'processed', 'df_final_clean.csv')
# Try notebooks first, then root
_MODEL_NOTEBOOKS = os.path.join(BUNDESLIGA_DIR, 'modelo_v3_calibrado.joblib')
_MODEL_ROOT = os.path.join(BUNDESLIGA_DIR, 'modelo_v3_calibrado.joblib')
MODEL_FILE = _MODEL_NOTEBOOKS if os.path.exists(_MODEL_NOTEBOOKS) else _MODEL_ROOT
ODDS_FILE = os.path.join(BUNDESLIGA_DIR, 'data', 'live_odds.json')

# --- BUNDESLIGA OFFICIAL BRAND CSS ---
BL_LOGO = "https://upload.wikimedia.org/wikipedia/en/d/df/Bundesliga_logo_%282017%29.svg"

def load_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --bl-red: #d20515;
    --bl-red-dark: #a00410;
    --bl-dark: #111111;
    --bl-darker: #0a0a0a;
    --bl-card: #1a1a1a;
    --bl-surface: #222222;
    --bl-border: rgba(210, 5, 21, 0.15);
    --bl-text: #ffffff;
    --bl-text-muted: rgba(255, 255, 255, 0.45);
    --bl-green: #00e676;
    --bl-amber: #ffab00;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #111111 40%, #141414 100%) !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: var(--bl-text) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d0d 0%, #111111 100%) !important;
    border-right: 1px solid var(--bl-border) !important;
}
[data-testid="stSidebar"] * { color: #ccc !important; }

h1 {
    font-size: 26px !important; font-weight: 900 !important;
    letter-spacing: -0.3px !important; color: white !important;
    margin-bottom: 16px !important;
}
h2 { font-size: 17px !important; font-weight: 700 !important; color: #e0e0e0 !important; }
h3 {
    font-size: 12px !important; color: var(--bl-text-muted) !important;
    text-transform: uppercase !important; letter-spacing: 1.5px !important; font-weight: 700 !important;
}

/* Tabs */
div[data-testid="stTabs"] button {
    background: transparent !important; color: rgba(255,255,255,0.4) !important;
    border-bottom: 2px solid transparent !important; font-weight: 700 !important;
    font-size: 12px !important; letter-spacing: 1.2px !important; text-transform: uppercase !important;
    padding: 12px 24px !important; transition: all 0.2s !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--bl-red) !important;
    border-bottom: 2px solid var(--bl-red) !important;
}
div[data-testid="stTabs"] button:hover { color: white !important; }

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--bl-card) !important;
    border: 1px solid var(--bl-border) !important;
    border-radius: 10px !important; padding: 14px !important;
}
div[data-testid="stMetric"] label {
    color: var(--bl-text-muted) !important; font-size: 10px !important;
    text-transform: uppercase !important; letter-spacing: 1.2px !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: white !important; font-weight: 800 !important;
}

/* Buttons */
.stButton > button {
    background: var(--bl-red) !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-weight: 700 !important; letter-spacing: 0.5px !important;
    transition: all 0.25s !important;
}
.stButton > button:hover {
    background: var(--bl-red-dark) !important;
    box-shadow: 0 4px 16px rgba(210,5,21,0.35) !important;
    transform: translateY(-1px) !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: var(--bl-card) !important;
    border: 1px solid var(--bl-border) !important;
    border-radius: 8px !important; color: white !important;
}
</style>
    """, unsafe_allow_html=True)


# --- CONSTANTS ---
MODEL_FEATURES = [
    'Home_Elo', 'Away_Elo',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_FIFA_Ova', 'Away_FIFA_Ova',
    'Home_Market_Value', 'Away_Market_Value'
]

def get_features_from_model(model):
    """Extract the feature list a model was trained on."""
    try:
        return model.calibrated_classifiers_[0].estimator.get_booster().feature_names
    except Exception:
        pass
    try:
        return list(model.feature_names_in_)
    except AttributeError:
        return MODEL_FEATURES

# Winamax names → CSV names
TEAM_MAPPING = {
    'Bayern Munich': 'Bayern Munich', 'Bayern München': 'Bayern Munich', 'FC Bayern München': 'Bayern Munich', 'Bayern Múnich': 'Bayern Munich',
    'Borussia Dortmund': 'Borussia Dortmund', 'BV Borussia Dortmund': 'Borussia Dortmund', 'Dortmund': 'Borussia Dortmund',
    'RB Leipzig': 'RB Leipzig', 'Rasenballsport Leipzig': 'RB Leipzig',
    'Bayer Leverkusen': 'Bayer Leverkusen', 'Bayer 04 Leverkusen': 'Bayer Leverkusen',
    'Eintracht Frankfurt': 'Ein Frankfurt', 'Ein Frankfurt': 'Ein Frankfurt', 'SG Eintracht Frankfurt': 'Ein Frankfurt',
    'VfB Stuttgart': 'VfB Stuttgart',
    'SC Freiburg': 'SC Freiburg', 'Sport-Club Freiburg': 'SC Freiburg', 'Freiburg': 'SC Freiburg', 'Friburgo': 'SC Freiburg',
    'VfL Wolfsburg': 'VfL Wolfsburg', 'Wolfsburg': 'VfL Wolfsburg', 'Wolfsburgo': 'VfL Wolfsburg',
    'Borussia Mönchengladbach': 'Borussia Monchengladbach', "Borussia M'gladbach": 'Borussia Monchengladbach',
    'Borussia Monchengladbach': 'Borussia Monchengladbach', 'Monchengladbach': 'Borussia Monchengladbach',
    '1. FSV Mainz 05': 'FSV Mainz 05', 'FSV Mainz 05': 'FSV Mainz 05', 'Mainz': 'FSV Mainz 05', 'Mainz 05': 'FSV Mainz 05',
    'TSG 1899 Hoffenheim': 'TSG Hoffenheim', 'TSG Hoffenheim': 'TSG Hoffenheim', 'Hoffenheim': 'TSG Hoffenheim',
    'FC Augsburg': 'FC Augsburg', 'Augsburg': 'FC Augsburg', 'Augsburgo': 'FC Augsburg',
    'Werder Bremen': 'Werder Bremen', 'SV Werder Bremen': 'Werder Bremen',
    'Union Berlin': 'Union Berlin', '1. FC Union Berlin': 'Union Berlin',
    'VfL Bochum': 'VfL Bochum', 'VfL Bochum 1848': 'VfL Bochum', 'Bochum': 'VfL Bochum',
    '1. FC Heidenheim 1846': '1. FC Heidenheim', '1. FC Heidenheim': '1. FC Heidenheim', 'Heidenheim': '1. FC Heidenheim',
    'SV Darmstadt 98': 'SV Darmstadt 98', 'Darmstadt': 'SV Darmstadt 98',
    '1. FC Köln': 'FC Cologne', 'FC Cologne': 'FC Cologne', 'Cologne': 'FC Cologne', 'Koln': 'FC Cologne',
    'Hertha BSC': 'Hertha BSC', 'Hertha Berlin': 'Hertha BSC',
    'FC Schalke 04': 'FC Schalke 04', 'Schalke 04': 'FC Schalke 04', 'Schalke': 'FC Schalke 04',
    'Hannover 96': 'Hannover 96', 'Hannover': 'Hannover 96',
    'Fortuna Düsseldorf': 'Fortuna Dusseldorf', 'Fortuna Dusseldorf': 'Fortuna Dusseldorf',
    'Holstein Kiel': 'Holstein Kiel', 'Kiel': 'Holstein Kiel',
    'FC St. Pauli': 'FC St. Pauli', 'St. Pauli': 'FC St. Pauli',
    'Greuther Fürth': 'Greuther Furth', 'Greuther Furth': 'Greuther Furth',
    'SC Paderborn 07': 'SC Paderborn 07', 'Paderborn': 'SC Paderborn 07',
    'Arminia Bielefeld': 'Arminia Bielefeld', 'Bielefeld': 'Arminia Bielefeld',
    'FC Nürnberg': 'FC Nurnberg', 'FC Nurnberg': 'FC Nurnberg', 'Nurnberg': 'FC Nurnberg',
    'Hamburg': 'Hamburg', 'Hamburger SV': 'Hamburg',
}


# --- UTILS ---
def normalize_text(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')


def clean_html(html):
    return re.sub(r'^\s+', '', html, flags=re.MULTILINE)


def calcular_stake(prob, quota, bankroll, rank_diff=0):
    if prob * quota <= 1.0 or prob <= 0 or quota <= 1.0:
        return {'stake_pct': 0, 'importe': 0, 'filtro_pasado': False,
                'razon_rechazo': 'EV Negativo', 'edge_pct': (prob * quota - 1) * 100}
    kelly = (prob * quota - 1) / (quota - 1)
    kf = kelly * 0.25
    if rank_diff < 0.5:   cap = 0.05
    elif rank_diff < 1.0: cap = 0.035
    else:                 cap = 0.02
    sp = np.clip(kf, 0, cap)
    imp = sp * bankroll
    ok = sp > 0
    return {
        'stake_pct': sp,
        'importe': round(imp, 2) if imp >= 1 else 0,
        'stake_scale': int(min(max(sp / 0.05 * 10, 1), 10)) if sp > 0 else 0,
        'filtro_pasado': ok,
        'razon_rechazo': '' if ok else 'Stake ~0',
        'edge_pct': (prob * quota - 1) * 100
    }


def get_model_probs(df, model, home_team, away_team):
    if df is None or model is None:
        return None
    feats = get_features_from_model(model)

    subset = df[(df['HomeTeam'] == home_team) & (df['AwayTeam'] == away_team)]
    if not subset.empty:
        row = subset.sort_values('Date').iloc[-1]
    else:
        h_last = df[(df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team)].sort_values('Date').iloc[-1:]
        a_last = df[(df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team)].sort_values('Date').iloc[-1:]
        if h_last.empty or a_last.empty:
            return None
        hr, ar = h_last.iloc[0], a_last.iloc[0]
        row = pd.Series(0.0, index=feats)
        def gs(r, team, p):
            return r.get(f"Home_{p}", 0) if r['HomeTeam'] == team else r.get(f"Away_{p}", 0)
        for f in feats:
            if f.startswith('Home_'):
                row[f] = gs(hr, home_team, f[5:])
            elif f.startswith('Away_'):
                row[f] = gs(ar, away_team, f[5:])

    try:
        X = row.to_frame().T.reindex(columns=feats, fill_value=0)
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        proba = model.predict_proba(X)[0]
        return float(proba[2]), float(proba[1]), float(proba[0]), row
    except Exception as e:
        print(f"DEBUG BL get_model_probs error: {e}")
        return None


def get_radar_data(df, team):
    mask = (df['HomeTeam'] == team) | (df['AwayTeam'] == team)
    recent = df[mask].sort_values('Date').tail(10)
    if recent.empty:
        return None
    goals, xg, pressure, pts, dominance = [], [], [], [], []
    for _, r in recent.iterrows():
        is_h = r['HomeTeam'] == team
        p = 'Home' if is_h else 'Away'
        goals.append(r.get('FTHG' if is_h else 'FTAG', 0))
        xg.append(r.get(f'{p}_xG_Avg_L5', 0))
        pressure.append(r.get(f'{p}_Pressure_Avg_L5', 0))
        pts.append(r.get(f'{p}_Streak_L5', 0))
    gf = np.mean(goals) if goals else 0
    return {
        'Attack':   min(gf / 2.5 * 100, 100),
        'xG':       min(np.mean(xg) / 2 * 100, 100) if xg else 50,
        'Pressure': min(np.mean(pressure) / 2 * 100, 100) if pressure else 50,
        'Form':     min(np.mean(pts) / 3 * 100, 100) if pts else 50,
        'Defence':  max(0, 100 - gf / 2.5 * 100),
    }


# --- LOADING ---
@st.cache_resource(ttl=3600)
def load_resources():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        for c in df.columns:
            if c not in ('HomeTeam', 'AwayTeam', 'Date', 'Season', 'FTR', 'Target'):
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    except Exception:
        df = None
    model = None
    if os.path.exists(MODEL_FILE):
        try:
            artifact = joblib.load(MODEL_FILE)
            model = artifact['model'] if isinstance(artifact, dict) and 'model' in artifact else artifact
        except Exception:
            pass
    return df, model


# ══════════════════════════════════════════════════════════════════════════════
#  HEADER – Official Bundesliga Style
# ══════════════════════════════════════════════════════════════════════════════
def render_header():
    st.markdown(clean_html(f"""
<div style="text-align:center; padding:20px 0 8px 0;">
<img src="{BL_LOGO}" width="140" style="margin-bottom:8px; filter:drop-shadow(0 0 24px rgba(210,5,21,0.5));">
<h1 style="margin:4px 0 0 0; font-size:24px !important; letter-spacing:2px;">ANALYTICS ENGINE</h1>
<p style="font-size:10px; letter-spacing:3px; text-transform:uppercase; color:rgba(255,255,255,0.25); margin:6px 0 0 0;">
POWERED BY EA SPORTS FC  |  SAISON 2024/25
</p>
</div>
<div style="display:flex; justify-content:center; align-items:center; gap:32px; padding:10px; margin:16px auto; max-width:600px;
    background:rgba(210,5,21,0.06); border-radius:8px; border:1px solid rgba(210,5,21,0.12);">
<span style="font-size:10px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2); font-weight:600;">ADIDAS</span>
<span style="font-size:10px; color:rgba(255,255,255,0.1);">|</span>
<span style="font-size:10px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2); font-weight:600;">DERBYSTAR</span>
<span style="font-size:10px; color:rgba(255,255,255,0.1);">|</span>
<span style="font-size:10px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2); font-weight:600;">EA SPORTS FC</span>
<span style="font-size:10px; color:rgba(255,255,255,0.1);">|</span>
<span style="font-size:10px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.2); font-weight:600;">TOPPS</span>
</div>
    """), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MATCH CARD – Bundesliga Official Style
# ══════════════════════════════════════════════════════════════════════════════
def render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets=None):
    if value_bets is None: value_bets = set()
    has_value = any(op in value_bets for op in ['1', 'X', '2'])
    vb = '<span style="background:#00e676; color:#111; font-size:9px; font-weight:800; padding:3px 10px; border-radius:20px; letter-spacing:1px;">VALUE BET</span>' if has_value else ''

    def ev_c(v): return "#00e676" if v > 0.03 else ("rgba(255,255,255,0.25)" if v < -0.05 else "#ffab00")
    def cell_border(k): return "border:1px solid #00e676; background:rgba(0,230,118,0.06);" if k in value_bets else ""
    ih = 1/oh if oh>0 else 0
    id_ = 1/od if od>0 else 0
    ia = 1/oa if oa>0 else 0

    html = clean_html(f'''
<div style="background:#1a1a1a; border:1px solid rgba(210,5,21,0.12); border-radius:14px; padding:22px; margin:8px 0; transition:all 0.3s;
    border-bottom-left-radius:0; border-bottom-right-radius:0;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; padding-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05);">
<div style="font-size:9px; color:rgba(255,255,255,0.25); letter-spacing:2px; text-transform:uppercase; font-weight:600;">Bundesliga · Spieltag</div>
{vb}
</div>
<div style="display:flex; justify-content:space-between; align-items:center; font-size:15px; font-weight:700; color:white;">
<span>{h}</span>
<span style="color:#d20515; font-weight:900; font-size:11px; letter-spacing:3px; padding:0 14px;">VS</span>
<span>{a}</span>
</div>
<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-top:14px;">
<div style="text-align:center; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px 6px; border:1px solid rgba(255,255,255,0.04); {cell_border('1')}">
<div style="font-size:9px; text-transform:uppercase; letter-spacing:1px; color:rgba(255,255,255,0.3); margin-bottom:4px;">Heim (1)</div>
<div style="font-size:18px; font-weight:800; color:{ev_c(eh)};">{oh:.2f}</div>
<div style="font-size:9px; padding:2px 6px; border-radius:12px; margin-top:3px; display:inline-block; font-weight:700;
    background:{'rgba(0,230,118,0.12)' if eh > 0.03 else 'rgba(255,255,255,0.04)'}; color:{ev_c(eh)};">EV {eh:+.1%}</div>
<div style="font-size:7px; opacity:0.25; margin-top:3px;">AI:{ph:.0%} · Mkt:{ih:.0%}</div>
</div>
<div style="text-align:center; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px 6px; border:1px solid rgba(255,255,255,0.04); {cell_border('X')}">
<div style="font-size:9px; text-transform:uppercase; letter-spacing:1px; color:rgba(255,255,255,0.3); margin-bottom:4px;">Unent. (X)</div>
<div style="font-size:18px; font-weight:800; color:{ev_c(ed)};">{od:.2f}</div>
<div style="font-size:9px; padding:2px 6px; border-radius:12px; margin-top:3px; display:inline-block; font-weight:700;
    background:{'rgba(0,230,118,0.12)' if ed > 0.03 else 'rgba(255,255,255,0.04)'}; color:{ev_c(ed)};">EV {ed:+.1%}</div>
<div style="font-size:7px; opacity:0.25; margin-top:3px;">AI:{pd_prob:.0%} · Mkt:{id_:.0%}</div>
</div>
<div style="text-align:center; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px 6px; border:1px solid rgba(255,255,255,0.04); {cell_border('2')}">
<div style="font-size:9px; text-transform:uppercase; letter-spacing:1px; color:rgba(255,255,255,0.3); margin-bottom:4px;">Ausw. (2)</div>
<div style="font-size:18px; font-weight:800; color:{ev_c(ea)};">{oa:.2f}</div>
<div style="font-size:9px; padding:2px 6px; border-radius:12px; margin-top:3px; display:inline-block; font-weight:700;
    background:{'rgba(0,230,118,0.12)' if ea > 0.03 else 'rgba(255,255,255,0.04)'}; color:{ev_c(ea)};">EV {ea:+.1%}</div>
<div style="font-size:7px; opacity:0.25; margin-top:3px;">AI:{pa:.0%} · Mkt:{ia:.0%}</div>
</div>
</div>
</div>
    ''')
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    load_css()
    render_header()
    df, model = load_resources()

    with st.sidebar:
        st.markdown(f'<div style="text-align:center;"><img src="{BL_LOGO}" width="90" style="margin:10px auto;"></div>', unsafe_allow_html=True)
        st.markdown("### CONTROL PANEL")
        user_bankroll = st.sidebar.number_input(
            "BANKROLL (€)", min_value=1.0, max_value=100000.0, value=1000.0, step=100.0,
            help="Dein aktuelles Kapital für die automatische Stake-Berechnung."
        )
        st.markdown(f"<p style='font-size:10px; color:rgba(255,255,255,0.2);'>Official Analytics Platform</p>", unsafe_allow_html=True)
        if df is not None:
            st.markdown(f"<p style='font-size:10px; color:#00e676;'>{len(df)} Spiele geladen</p>", unsafe_allow_html=True)

        if st.button("Daten Aktualisieren"):
            with st.spinner("Lade aktuelle Daten und berechne Quoten neu..."):
                update_script = os.path.join(BUNDESLIGA_DIR, 'src', 'update_system.py')
                if os.path.exists(update_script):
                    subprocess.run([sys.executable, update_script])
                else:
                    # Fallback: run scraper + process_state directly
                    try:
                        scrape_js = os.path.join(BUNDESLIGA_DIR, 'src', 'scraper_winamax.js')
                        subprocess.run(['node', scrape_js], check=True, shell=True, cwd=BUNDESLIGA_DIR)
                        proc_py = os.path.join(BUNDESLIGA_DIR, 'src', 'process_state.py')
                        subprocess.run([sys.executable, proc_py], check=True, shell=True, cwd=BUNDESLIGA_DIR)
                    except Exception as e:
                        st.error(f"Error: {e}")
            st.cache_resource.clear()
            st.success("Daten und Quoten aktualisiert", icon=None)
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["LIVE MARKT", "TAKTIK-SCOUTING", "HISTORISCHE ANALYSE"])

    # ═══════════ TAB 1: LIVE MARKET ═══════════
    with tab1:
        st.markdown(clean_html("""
<div style="background:rgba(210,5,21,0.05); padding:14px; border-radius:10px; margin-bottom:18px; border-left:3px solid #d20515;">
<strong style="color:#d20515; font-size:12px; letter-spacing:0.5px;">LIVE ODDS SCANNER</strong><br>
<span style="font-size:11px; color:rgba(255,255,255,0.4);">
Echtzeit-Vergleich der Buchmacher-Quoten mit den AI-Modellwahrscheinlichkeiten. <strong style="color:#00e676;">Grünes EV = Value Bet erkannt.</strong>
</span>
</div>
        """), unsafe_allow_html=True)

        matches = []
        if os.path.exists(ODDS_FILE):
            try:
                matches = json.load(open(ODDS_FILE))
                if matches:
                    matches.sort(key=lambda x: x.get('date', 0))
            except: pass

        c1, c2, c3 = st.columns(3)
        c1.metric("Live Spiele", str(len(matches)))
        c2.metric("Modell V3", "[OK] Geladen" if model else "[FAIL] Nicht gefunden")
        c3.metric("Signalstärke", "Hoch" if model else "—")

        if not matches:
            st.info("Keine Live-Marktdaten verfügbar. Bitte 'Daten Aktualisieren' drücken.", icon=None)
        elif df is None or model is None:
            st.warning("Daten oder Modell nicht korrekt geladen.", icon=None)
        else:
            min_ev = 0.03
            cols = st.columns(2)

            for idx, m in enumerate(matches):
                h_raw, a_raw = m.get('home', ''), m.get('away', '')
                h = TEAM_MAPPING.get(normalize_text(h_raw), TEAM_MAPPING.get(h_raw, h_raw))
                a = TEAM_MAPPING.get(normalize_text(a_raw), TEAM_MAPPING.get(a_raw, a_raw))

                probs_data = get_model_probs(df, model, h, a)
                if probs_data is None: continue
                ph, pd_prob, pa = probs_data[:3]
                X_row = probs_data[3] if len(probs_data) > 3 else {}

                try: oh, od, oa = float(m.get('1',1)), float(m.get('X',1)), float(m.get('2',1))
                except: oh,od,oa = 1.0, 1.0, 1.0
                eh, ed, ea = (ph*oh)-1, (pd_prob*od)-1, (pa*oa)-1

                h_elo = X_row.get('Home_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
                a_elo = X_row.get('Away_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
                rank_diff = abs(h_elo - a_elo) / 100.0

                ev_map = {'1': eh, 'X': ed, '2': ea}
                p_map  = {'1': ph, 'X': pd_prob, '2': pa}
                q_map  = {'1': oh, 'X': od, '2': oa}

                ODDS_FILTER = [('1', 1.40, 1.70), ('1', 2.00, 2.50), ('2', 1.70, 2.00)]
                def passes_odds_filter(op, odds):
                    return any(op == bt and lo <= odds < hi for bt, lo, hi in ODDS_FILTER)

                candidates = [
                    op for op in ['1', '2']
                    if ev_map[op] > min_ev and passes_odds_filter(op, q_map[op])
                ]
                best_op = max(candidates, key=lambda op: ev_map[op]) if candidates else None
                value_bets = {best_op} if best_op else set()

                with cols[idx % 2]:
                    render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets)

                    # Risk
                    rl = "HOCH" if rank_diff < 0.5 else ("MITTEL" if rank_diff < 1.0 else "NIEDRIG")
                    rc = "#d20515" if rl == "HOCH" else ("#ffab00" if rl == "MITTEL" else "#00e676")
                    st.markdown(clean_html(f'<div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.15); padding:7px 12px; border-radius:6px; margin-bottom:8px; border-left:3px solid {rc};"><span style="font-size:9px; color:rgba(255,255,255,0.5); font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Algorithmisches Risiko</span><span style="font-size:10px; font-weight:900; color:{rc};">{rl}</span></div>'), unsafe_allow_html=True)

                    # Stake Table
                    rows = ""
                    for op_s in ["1", "X", "2"]:
                        o_s, e_s = q_map[op_s], ev_map[op_s]
                        if op_s == best_op:
                            kr = (p_map[op_s]*o_s-1)/(o_s-1)
                            kf = np.clip(kr*0.25, 0, 0.05)
                            imp = round(kf*user_bankroll, 2)
                            c_s, a_s, k_s = "#00e676", f"€{imp:.0f}", f"{kf:.1%}"
                        else:
                            c_s, a_s, k_s = "rgba(255,255,255,0.15)", "—", "—"
                        rows += f"<tr style='color:{c_s}; font-size:9px; border-bottom:1px solid rgba(255,255,255,0.02);'><td style='padding:3px 4px; font-weight:600;'>{op_s}</td><td style='text-align:center;'>{e_s:+.1%}</td><td style='text-align:center;'>{k_s}</td><td style='text-align:right; font-weight:800; padding:3px 4px;'>{a_s}</td></tr>"
                    st.markdown(clean_html(f"<table style='width:100%; border-collapse:collapse; background:rgba(0,0,0,0.1); border-radius:6px; overflow:hidden; margin-bottom:12px;'><tr style='font-size:8px; opacity:0.3; background:rgba(255,255,255,0.02);'><th style='padding:5px; text-align:left;'>Auswahl</th><th style='text-align:center;'>EV</th><th style='text-align:center;'>Kelly</th><th style='text-align:right; padding:5px;'>Einsatz</th></tr>{rows}</table>"), unsafe_allow_html=True)

    # ═══════════ TAB 2: TACTICAL SCOUTING ═══════════
    with tab2:
        st.markdown(clean_html("""
<div style="background:rgba(0,230,118,0.05); padding:14px; border-radius:10px; margin-bottom:18px; border-left:3px solid #00e676;">
<strong style="color:#00e676; font-size:12px;">TAKTISCHER RADAR-VERGLEICH</strong><br>
<span style="font-size:11px; color:rgba(255,255,255,0.4);">
5-Achsen-Leistungsprofil basierend auf den letzten 10 Spielen. Vergleiche zwei Bundesliga-Vereine.
</span>
</div>
        """), unsafe_allow_html=True)

        if df is not None:
            teams = sorted(df['HomeTeam'].unique())
            c1, c2 = st.columns(2)
            t1 = c1.selectbox("Heimverein", teams, index=teams.index('Bayern Munich') if 'Bayern Munich' in teams else 0)
            t2 = c2.selectbox("Gastverein", teams, index=teams.index('Borussia Dortmund') if 'Borussia Dortmund' in teams else min(1, len(teams)-1))

            r1, r2 = get_radar_data(df, t1), get_radar_data(df, t2)
            if r1 and r2:
                cats = list(r1.keys())
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=list(r1.values())+[list(r1.values())[0]], theta=cats+[cats[0]], fill='toself', name=t1, line_color='#d20515', fillcolor='rgba(210,5,21,0.15)'))
                fig.add_trace(go.Scatterpolar(r=list(r2.values())+[list(r2.values())[0]], theta=cats+[cats[0]], fill='toself', name=t2, line_color='#ffab00', fillcolor='rgba(255,171,0,0.10)'))
                fig.update_layout(
                    polar=dict(bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0,100], gridcolor='rgba(255,255,255,0.06)', tickfont=dict(color='rgba(255,255,255,0.25)', size=8)),
                        angularaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(color='rgba(255,255,255,0.5)', size=10))),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'), legend=dict(font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=60,r=60,t=30,b=30), height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

                probs = get_model_probs(df, model, t1, t2)
                if probs:
                    ph, pd_p, pa = probs[:3]
                    st.markdown(clean_html(f"""
<div style="background:rgba(210,5,21,0.06); border:1px solid rgba(210,5,21,0.12); border-radius:10px; padding:18px; margin-top:8px;">
<div style="text-align:center; font-size:10px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.3); margin-bottom:10px;">AI-PROGNOSE</div>
<div style="display:grid; grid-template-columns:1fr 1fr 1fr; text-align:center;">
<div><div style="font-size:22px; font-weight:900; color:#d20515;">{ph:.0%}</div><div style="font-size:9px; color:rgba(255,255,255,0.3); text-transform:uppercase;">{t1}</div></div>
<div><div style="font-size:22px; font-weight:900; color:rgba(255,255,255,0.4);">{pd_p:.0%}</div><div style="font-size:9px; color:rgba(255,255,255,0.3); text-transform:uppercase;">Unentschieden</div></div>
<div><div style="font-size:22px; font-weight:900; color:#ffab00;">{pa:.0%}</div><div style="font-size:9px; color:rgba(255,255,255,0.3); text-transform:uppercase;">{t2}</div></div>
</div>
</div>
                    """), unsafe_allow_html=True)

    # ═══════════ TAB 3: HISTORICAL AUDIT ═══════════
    with tab3:
        st.markdown(clean_html("""
<div style="background:rgba(255,171,0,0.05); padding:14px; border-radius:10px; margin-bottom:18px; border-left:3px solid #ffab00;">
<strong style="color:#ffab00; font-size:12px;">HISTORISCHE LEISTUNGSANALYSE</strong><br>
<span style="font-size:11px; color:rgba(255,255,255,0.4);">
Saison-für-Saison Aufschlüsselung. Wähle einen Verein für Elo-Verlauf, Form und Ergebnisverteilung.
</span>
</div>
        """), unsafe_allow_html=True)

        if df is not None:
            teams = sorted(df['HomeTeam'].unique())
            team = st.selectbox("Verein auswählen", teams, index=teams.index('Bayern Munich') if 'Bayern Munich' in teams else 0, key='bl_hist_team')
            mask = (df['HomeTeam'] == team) | (df['AwayTeam'] == team)
            team_df = df[mask].sort_values('Date').copy()

            if not team_df.empty:
                elo_vals = [r['Home_Elo'] if r['HomeTeam'] == team else r['Away_Elo'] for _, r in team_df.iterrows()]
                team_df['Team_Elo'] = elo_vals
                fig_elo = go.Figure()
                fig_elo.add_trace(go.Scatter(x=team_df['Date'], y=team_df['Team_Elo'], mode='lines',
                    line=dict(color='#d20515', width=2), fill='tozeroy', fillcolor='rgba(210,5,21,0.06)', name='Elo'))
                fig_elo.update_layout(
                    title=dict(text=f"{team} – Elo-Verlauf", font=dict(size=13, color='white')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.04)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', title='Elo'),
                    height=320, margin=dict(l=40,r=20,t=45,b=25))
                st.plotly_chart(fig_elo, use_container_width=True)

                results = []
                for _, r in team_df.iterrows():
                    is_h = r['HomeTeam'] == team
                    if (is_h and r['FTR'] == 'H') or (not is_h and r['FTR'] == 'A'): results.append('Sieg')
                    elif r['FTR'] == 'D': results.append('Unentschieden')
                    else: results.append('Niederlage')
                rc = pd.Series(results).value_counts()
                fig_pie = go.Figure(go.Pie(labels=rc.index, values=rc.values,
                    marker=dict(colors=['#00e676', '#ffab00', '#d20515']), hole=0.55,
                    textinfo='label+percent', textfont=dict(size=11, color='white')))
                fig_pie.update_layout(
                    title=dict(text=f"{team} – Ergebnisverteilung (Gesamt)", font=dict(size=13, color='white')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'),
                    height=320, margin=dict(l=20,r=20,t=45,b=20), showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

    # Footer
    st.markdown(clean_html("""
<div style="text-align:center; padding:25px 0 10px 0; margin-top:30px; border-top:1px solid rgba(255,255,255,0.03);">
<p style="font-size:9px; letter-spacing:2px; text-transform:uppercase; color:rgba(255,255,255,0.1);">
Bundesliga Analytics Engine v3.0 | 2025 Research Hub
</p>
<p style="font-size:8px; color:rgba(255,255,255,0.06);">
Powered by XGBoost + Optuna | Data: football-data.co.uk
</p>
</div>
    """), unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Bundesliga Analytics Engine",
        page_icon="https://upload.wikimedia.org/wikipedia/en/d/df/Bundesliga_logo_%282017%29.svg",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
