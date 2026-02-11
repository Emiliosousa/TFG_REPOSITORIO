import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
import os
import json
import re

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check if Premier subfolder exists
if not os.path.exists(os.path.join(BASE_DIR, 'Premier', 'df_premier_features.csv')):
    if os.path.exists(os.path.join(BASE_DIR, 'df_premier_features.csv')):
        PREMIER_DIR = BASE_DIR
    else:
        PREMIER_DIR = os.path.join(BASE_DIR, 'Premier')
else:
    PREMIER_DIR = os.path.join(BASE_DIR, 'Premier')

DATA_FILE = os.path.join(PREMIER_DIR, 'df_premier_features.csv')
MODEL_FILE = os.path.join(PREMIER_DIR, 'modelo_premier.joblib')
ODDS_FILE = os.path.join(PREMIER_DIR, 'data', 'live_odds.json')

# Config moved to main block

# --- PREMIER LEAGUE BRAND CSS ---
def load_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
    --pl-purple: #3d195b;
    --pl-purple-light: #5b2d8e;
    --pl-magenta: #ff2882;
    --pl-cyan: #04f5ff;
    --pl-green: #00ff85;
    --pl-white: #ffffff;
    --pl-dark: #0c0420;
    --pl-card-bg: rgba(61, 25, 91, 0.35);
    --pl-glass: rgba(255, 255, 255, 0.04);
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0c0420 0%, #1a0a35 30%, #2d1155 60%, #1a0a35 100%) !important;
    font-family: 'Inter', sans-serif !important;
    color: white !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a0a35 0%, #0c0420 100%) !important;
    border-right: 1px solid rgba(255, 40, 130, 0.2) !important;
}

[data-testid="stSidebar"] * {
    color: #e0d0f0 !important;
}

h1 {
    font-size: 28px !important;
    font-weight: 900 !important;
    letter-spacing: -0.5px !important;
    color: white !important;
    margin-bottom: 20px !important;
    text-shadow: 0 0 30px rgba(255, 40, 130, 0.3);
}
h2 {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #e0d0f0 !important;
    margin: 16px 0 8px 0 !important;
}
h3 {
    font-size: 13px !important;
    color: rgba(255, 255, 255, 0.5) !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    font-weight: 600 !important;
}

/* Tabs */
div[data-testid="stTabs"] button {
    background: transparent !important;
    color: rgba(255, 255, 255, 0.5) !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #ff2882 !important;
    border-bottom: 2px solid #ff2882 !important;
}
div[data-testid="stTabs"] button:hover {
    color: #04f5ff !important;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(61, 25, 91, 0.5), rgba(91, 45, 142, 0.3)) !important;
    border: 1px solid rgba(255, 40, 130, 0.15) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}
div[data-testid="stMetric"] label {
    color: rgba(255, 255, 255, 0.5) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: white !important;
    font-weight: 800 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #ff2882, #ff0066) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 20px rgba(255, 40, 130, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* Match Card */
.pl-card {
    background: linear-gradient(135deg, rgba(61, 25, 91, 0.6) 0%, rgba(44, 15, 70, 0.4) 100%);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 40, 130, 0.12);
    border-radius: 16px;
    padding: 24px;
    margin: 10px 0;
    transition: all 0.3s ease;
}
.pl-card:hover {
    border-color: rgba(255, 40, 130, 0.35);
    box-shadow: 0 8px 32px rgba(255, 40, 130, 0.15);
    transform: translateY(-2px);
}
.pl-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.pl-teams {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 700;
    color: white;
}
.pl-vs {
    color: #ff2882;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    padding: 0 16px;
}
.pl-odds-row {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
    margin-top: 16px;
}
.pl-odd-cell {
    text-align: center;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 10px;
    padding: 12px 8px;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
.pl-odd-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 6px;
}
.pl-odd-value {
    font-size: 20px;
    font-weight: 800;
}
.pl-ev-pos { color: #00ff85; }
.pl-ev-neg { color: rgba(255, 255, 255, 0.3); }
.pl-ev-badge {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 4px;
    display: inline-block;
    font-weight: 700;
}
.pl-ev-badge-pos { background: rgba(0, 255, 133, 0.15); color: #00ff85; }
.pl-ev-badge-neg { background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.3); }
.pl-value-bet-badge {
    background: linear-gradient(135deg, #00ff85, #00cc6a);
    color: #0c0420;
    font-size: 10px;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* Sponsor Bar */
.sponsor-bar {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 40px;
    padding: 12px;
    margin: 20px 0;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}
.sponsor-item {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.25);
    font-weight: 600;
}

/* KPI strip */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 16px 0;
}
.kpi-box {
    background: linear-gradient(135deg, rgba(61, 25, 91, 0.5), rgba(91, 45, 142, 0.2));
    border: 1px solid rgba(255, 40, 130, 0.1);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.kpi-val {
    font-size: 24px;
    font-weight: 900;
    color: white;
    text-shadow: 0 0 20px rgba(255, 40, 130, 0.3);
}
.kpi-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: rgba(255, 255, 255, 0.4);
    margin-top: 4px;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: rgba(61, 25, 91, 0.4) !important;
    border: 1px solid rgba(255, 40, 130, 0.2) !important;
    border-radius: 8px !important;
    color: white !important;
}
</style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
MODEL_FEATURES = [
    'Home_Elo', 'Away_Elo',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Dominance', 'Away_Dominance'
]

TEAM_MAPPING = {
    'Man United': 'Manchester United', 'Man City': 'Manchester City',
    'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
    'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton',
    'Brighton': 'Brighton', 'Bournemouth': 'Bournemouth',
    "Nott'm Forest": 'Nott. Forest', 'Luton': 'Luton',
    'Ipswich': 'Ipswich',
}

# --- UTILS ---
def clean_html(html):
    """Remove leading whitespace from every line to fix Streamlit formatting."""
    return re.sub(r'^\s+', '', html, flags=re.MULTILINE)

def get_model_probs(df, model, home_team, away_team):
    if df is None or model is None:
        return None

    subset = df[(df['HomeTeam'] == home_team) & (df['AwayTeam'] == away_team)]

    if not subset.empty:
        row = subset.sort_values('Date').iloc[-1]
    else:
        h_last = df[(df['HomeTeam'] == home_team) | (df['AwayTeam'] == home_team)].sort_values('Date').iloc[-1:]
        a_last = df[(df['HomeTeam'] == away_team) | (df['AwayTeam'] == away_team)].sort_values('Date').iloc[-1:]
        if h_last.empty or a_last.empty:
            return None
        h_row, a_row = h_last.iloc[0], a_last.iloc[0]

        row = pd.Series(0.0, index=MODEL_FEATURES)
        def gs(r, team, p):
            return r.get(f"Home_{p}", 0) if r['HomeTeam'] == team else r.get(f"Away_{p}", 0)

        row['Home_Elo'] = gs(h_row, home_team, 'Elo')
        row['Away_Elo'] = gs(a_row, away_team, 'Elo')
        row['Home_xG_Avg_L5'] = gs(h_row, home_team, 'xG_Avg_L5')
        row['Away_xG_Avg_L5'] = gs(a_row, away_team, 'xG_Avg_L5')
        row['Home_Streak_L5'] = gs(h_row, home_team, 'Streak_L5')
        row['Away_Streak_L5'] = gs(a_row, away_team, 'Streak_L5')
        row['Home_Pressure_Avg_L5'] = gs(h_row, home_team, 'Pressure_Avg_L5')
        row['Away_Pressure_Avg_L5'] = gs(a_row, away_team, 'Pressure_Avg_L5')
        row['Home_Dominance'] = gs(h_row, home_team, 'Dominance')
        row['Away_Dominance'] = gs(a_row, away_team, 'Dominance')

    try:
        X = row[MODEL_FEATURES].to_frame().T
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        proba = model.predict_proba(X)[0]
        return float(proba[2]), float(proba[1]), float(proba[0])  # H, D, A
    except Exception as e:
        return None


def get_radar_data(df, team):
    """Team radar from last 10 matches."""
    mask = (df['HomeTeam'] == team) | (df['AwayTeam'] == team)
    recent = df[mask].sort_values('Date').tail(10)
    if recent.empty:
        return None

    goals, xg, pressure, pts, dominance, clean = [], [], [], [], [], []
    for _, r in recent.iterrows():
        is_h = r['HomeTeam'] == team
        p = 'Home' if is_h else 'Away'
        opp = 'Away' if is_h else 'Home'
        goals.append(r.get(f'FTHG' if is_h else 'FTAG', 0))
        xg.append(r.get(f'{p}_xG_Avg_L5', 0))
        pressure.append(r.get(f'{p}_Pressure_Avg_L5', 0))
        pts.append(r.get(f'{p}_Streak_L5', 0))
        dominance.append(r.get(f'{p}_Dominance', 0))
        clean.append(1 if r.get(f'{"FTAG" if is_h else "FTHG"}', 1) == 0 else 0)

    return {
        'Attack': min(np.mean(goals) / 3 * 100, 100),
        'xG Quality': min(np.mean(xg) / 2 * 100, 100),
        'Pressure': min(np.mean(pressure) / 2 * 100, 100),
        'Form': min(np.mean(pts) / 3 * 100, 100),
        'Dominance': min(np.mean(dominance) / 1.5 * 100, 100),
        'Defence': min(np.mean(clean) * 100, 100),
    }


# --- LOADING ---
@st.cache_resource(ttl=3600)
def load_resources():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        for c in MODEL_FEATURES:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    except Exception:
        df = None

    model = None
    if os.path.exists(MODEL_FILE):
        try:
            model = joblib.load(MODEL_FILE)
        except Exception:
            pass
    return df, model


# --- HEADER ---
def render_header():
    st.markdown(clean_html("""
    <div style="text-align: center; padding: 10px 0 5px 0;">
        <img src="https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1200px-Premier_League_Logo.svg.png" width="120" style="margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(255, 40, 130, 0.4));">
        <h1 style="margin: 4px 0 0 0; font-size: 26px !important;">ANALYTICS ENGINE</h1>
        <p style="font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: rgba(255,255,255,0.35); margin: 4px 0 0 0;">
            POWERED BY EA SPORTS FC™ | SEASON 2024/25
        </p>
    </div>
    <div class="sponsor-bar">
        <span class="sponsor-item">BARCLAYS</span>
        <span class="sponsor-item">•</span>
        <span class="sponsor-item">NIKE</span>
        <span class="sponsor-item">•</span>
        <span class="sponsor-item">EA SPORTS FC</span>
        <span class="sponsor-item">•</span>
        <span class="sponsor-item">ORACLE</span>
        <span class="sponsor-item">•</span>
        <span class="sponsor-item">HUBLOT</span>
    </div>
    """), unsafe_allow_html=True)


# --- MATCH CARD ---
def render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, has_value=False):
    ev_cls = lambda v: "pl-ev-pos" if v > 0 else "pl-ev-neg"
    badge_cls = lambda v: "pl-ev-badge-pos" if v > 0 else "pl-ev-badge-neg"
    vb = '<span class="pl-value-bet-badge">VALUE BET</span>' if has_value else ''

    vb = '<span class="pl-value-bet-badge">VALUE BET</span>' if has_value else ''

    html_content = clean_html(f"""
        <div class="pl-card">
            <div class="pl-card-header">
                <div style="font-size: 10px; color: rgba(255,255,255,0.3); letter-spacing: 2px; text-transform: uppercase;">Premier League • Matchday</div>
                {vb}
            </div>
            <div class="pl-teams">
                <span>{h}</span>
                <span class="pl-vs">VS</span>
                <span>{a}</span>
            </div>
            <div class="pl-odds-row">
                <div class="pl-odd-cell">
                    <div class="pl-odd-label">HOME</div>
                    <div class="pl-odd-value {ev_cls(eh)}">{oh:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(eh)}">EV {eh:+.1%}</div>
                    <div style="font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 4px;">AI: {ph:.0%}</div>
                </div>
                <div class="pl-odd-cell">
                    <div class="pl-odd-label">DRAW</div>
                    <div class="pl-odd-value {ev_cls(ed)}">{od:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(ed)}">EV {ed:+.1%}</div>
                    <div style="font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 4px;">AI: {pd_prob:.0%}</div>
                </div>
                <div class="pl-odd-cell">
                    <div class="pl-odd-label">AWAY</div>
                    <div class="pl-odd-value {ev_cls(ea)}">{oa:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(ea)}">EV {ea:+.1%}</div>
                    <div style="font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 4px;">AI: {pa:.0%}</div>
                </div>
            </div>
        </div>
    """)
    st.markdown(html_content, unsafe_allow_html=True)


# --- MAIN ---
def main():
    load_css()
    render_header()
    df, model = load_resources()

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f2/Premier_League_Logo.svg/1200px-Premier_League_Logo.svg.png", width=80)
        st.markdown("### CONTROL PANEL")
        st.markdown("<p style='font-size: 11px; color: rgba(255,255,255,0.3);'>Official Analytics Platform</p>", unsafe_allow_html=True)
        if df is not None:
            st.markdown(f"<p style='font-size: 11px; color: #00ff85;'>{len(df)} matches loaded</p>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["LIVE MARKET", "TACTICAL SCOUTING", "HISTORICAL AUDIT"])

    # ======================================================
    # TAB 1: LIVE MARKET
    # ======================================================
    with tab1:
        st.markdown(clean_html("""
        <div style="background: rgba(255,40,130,0.06); padding: 16px; border-radius: 12px; margin-bottom: 20px; border-left: 3px solid #ff2882;">
            <strong style="color: #ff2882; font-size: 13px;">LIVE ODDS SCANNER</strong><br>
            <span style="font-size: 12px; color: rgba(255,255,255,0.5);">
            Real-time comparison of bookmaker odds vs AI model probabilities. <strong style="color: #00ff85;">Green EV → Value Bet detected.</strong>
            </span>
        </div>
        """), unsafe_allow_html=True)

        matches = []
        if os.path.exists(ODDS_FILE):
            try:
                matches = json.load(open(ODDS_FILE))
            except Exception:
                pass

        if not matches:
            st.markdown(clean_html("""
            <div style="text-align: center; padding: 60px 20px; opacity: 0.4;">
                <div style="font-size: 14px; font-weight: 600; letter-spacing: 1px;">NO LIVE MARKET DATA</div>
                <div style="font-size: 11px; margin-top: 6px;">Waiting for odds feed...</div>
            </div>
            """), unsafe_allow_html=True)
        else:
            cols = st.columns(2)
            for i, m in enumerate(matches):
                h = TEAM_MAPPING.get(m.get('home', ''), m.get('home', ''))
                a = TEAM_MAPPING.get(m.get('away', ''), m.get('away', ''))
                probs = get_model_probs(df, model, h, a)
                if probs is None:
                    continue
                ph, pd_p, pa = probs
                try:
                    oh, od, oa = float(m.get('1', 1)), float(m.get('X', 1)), float(m.get('2', 1))
                except Exception:
                    oh, od, oa = 1, 1, 1
                eh, ed, ea = (ph * oh) - 1, (pd_p * od) - 1, (pa * oa) - 1
                has_value = any(ev > 0.05 for ev in (eh, ed, ea))
                with cols[i % 2]:
                    render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_p, pa, has_value)

    # ======================================================
    # TAB 2: TACTICAL SCOUTING
    # ======================================================
    with tab2:
        st.markdown(clean_html("""
        <div style="background: rgba(0,255,133,0.06); padding: 16px; border-radius: 12px; margin-bottom: 20px; border-left: 3px solid #00ff85;">
            <strong style="color: #00ff85; font-size: 13px;">TACTICAL RADAR COMPARISON</strong><br>
            <span style="font-size: 12px; color: rgba(255,255,255,0.5);">
            6-axis performance profile based on last 10 matches. Compare any two Premier League clubs.
            </span>
        </div>
        """), unsafe_allow_html=True)

        if df is not None:
            teams = sorted(df['HomeTeam'].unique())
            c1, c2 = st.columns(2)
            t1 = c1.selectbox("Home Club", teams, index=teams.index('Arsenal') if 'Arsenal' in teams else 0)
            t2 = c2.selectbox("Away Club", teams, index=teams.index('Liverpool') if 'Liverpool' in teams else 1)

            r1, r2 = get_radar_data(df, t1), get_radar_data(df, t2)

            if r1 and r2:
                cats = list(r1.keys())
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=list(r1.values()) + [list(r1.values())[0]],
                    theta=cats + [cats[0]],
                    fill='toself', name=t1,
                    line_color='#ff2882',
                    fillcolor='rgba(255, 40, 130, 0.15)'
                ))
                fig.add_trace(go.Scatterpolar(
                    r=list(r2.values()) + [list(r2.values())[0]],
                    theta=cats + [cats[0]],
                    fill='toself', name=t2,
                    line_color='#04f5ff',
                    fillcolor='rgba(4, 245, 255, 0.10)'
                ))
                fig.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.08)', tickfont=dict(color='rgba(255,255,255,0.3)', size=9)),
                        angularaxis=dict(gridcolor='rgba(255,255,255,0.08)', tickfont=dict(color='rgba(255,255,255,0.6)', size=11))
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'),
                    legend=dict(font=dict(size=12), bgcolor='rgba(0,0,0,0)'),
                    margin=dict(l=60, r=60, t=30, b=30),
                    height=420,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)

                # Prediction
                probs = get_model_probs(df, model, t1, t2)
                if probs:
                    ph, pd_p, pa = probs
                    st.markdown(clean_html(f"""
                    <div style="background: rgba(255,40,130,0.08); border: 1px solid rgba(255,40,130,0.15); border-radius: 12px; padding: 20px; margin-top: 10px;">
                        <div style="text-align: center; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.4); margin-bottom: 12px;">AI Match Prediction</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center;">
                            <div><div style="font-size: 24px; font-weight: 900; color: #ff2882;">{ph:.0%}</div><div style="font-size: 10px; color: rgba(255,255,255,0.4); text-transform: uppercase;">{t1}</div></div>
                            <div><div style="font-size: 24px; font-weight: 900; color: rgba(255,255,255,0.5);">{pd_p:.0%}</div><div style="font-size: 10px; color: rgba(255,255,255,0.4); text-transform: uppercase;">Draw</div></div>
                            <div><div style="font-size: 24px; font-weight: 900; color: #04f5ff;">{pa:.0%}</div><div style="font-size: 10px; color: rgba(255,255,255,0.4); text-transform: uppercase;">{t2}</div></div>
                        </div>
                    </div>
                    """), unsafe_allow_html=True)

    # ======================================================
    # TAB 3: HISTORICAL AUDIT
    # ======================================================
    with tab3:
        st.markdown(clean_html("""
        <div style="background: rgba(4,245,255,0.06); padding: 16px; border-radius: 12px; margin-bottom: 20px; border-left: 3px solid #04f5ff;">
            <strong style="color: #04f5ff; font-size: 13px;">HISTORICAL PERFORMANCE AUDIT</strong><br>
            <span style="font-size: 12px; color: rgba(255,255,255,0.5);">
            Season-by-season breakdown. Select a team to view Elo trajectory, form, and result distribution.
            </span>
        </div>
        """), unsafe_allow_html=True)

        if df is not None:
            teams = sorted(df['HomeTeam'].unique())
            team = st.selectbox("Select Club", teams, index=teams.index('Arsenal') if 'Arsenal' in teams else 0, key='hist_team')

            mask = (df['HomeTeam'] == team) | (df['AwayTeam'] == team)
            team_df = df[mask].sort_values('Date').copy()

            if not team_df.empty:
                # Elo Evolution
                elo_vals = []
                for _, r in team_df.iterrows():
                    elo_vals.append(r['Home_Elo'] if r['HomeTeam'] == team else r['Away_Elo'])
                team_df['Team_Elo'] = elo_vals

                fig_elo = go.Figure()
                fig_elo.add_trace(go.Scatter(
                    x=team_df['Date'], y=team_df['Team_Elo'],
                    mode='lines',
                    line=dict(color='#ff2882', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(255, 40, 130, 0.08)',
                    name='Elo'
                ))
                fig_elo.update_layout(
                    title=dict(text=f"{team} — Elo Rating Evolution", font=dict(size=14, color='white')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Elo'),
                    height=350, margin=dict(l=40, r=20, t=50, b=30)
                )
                st.plotly_chart(fig_elo, use_container_width=True)

                # Result Distribution
                results = []
                for _, r in team_df.iterrows():
                    is_h = r['HomeTeam'] == team
                    if (is_h and r['FTR'] == 'H') or (not is_h and r['FTR'] == 'A'):
                        results.append('Win')
                    elif r['FTR'] == 'D':
                        results.append('Draw')
                    else:
                        results.append('Loss')

                res_counts = pd.Series(results).value_counts()
                fig_pie = go.Figure(go.Pie(
                    labels=res_counts.index, values=res_counts.values,
                    marker=dict(colors=['#00ff85', '#f59e0b', '#ef4444']),
                    hole=0.55,
                    textinfo='label+percent',
                    textfont=dict(size=12, color='white')
                ))
                fig_pie.update_layout(
                    title=dict(text=f"{team} — Result Distribution (All Time)", font=dict(size=14, color='white')),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Inter'),
                    height=350, margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)

    # Footer
    st.markdown(clean_html("""
    <div style="text-align: center; padding: 30px 0 10px 0; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.05);">
        <p style="font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,0.15);">
            Premier League Analytics Engine™ v3.0 | © 2025 Valbrix Intelligence
        </p>
        <p style="font-size: 9px; color: rgba(255,255,255,0.1);">
            Powered by XGBoost + Optuna | Data: football-data.co.uk
        </p>
    </div>
    """), unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(
        page_title="PL Analytics Engine | Powered by EA SPORTS FC",
        page_icon="PL",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
