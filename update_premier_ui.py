import re

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
if "calcular_stake_profesional" not in content:
    content = content.replace("import re", "import re\n\ntry:\n    from src.staking_system import calcular_stake_profesional\n    from src.staking_config import STAKING_CONFIG\nexcept ImportError as e:\n    pass")

# 2. get_model_probs return signature
content = content.replace("return float(proba[2]), float(proba[1]), float(proba[0])  # H, D, A", "return float(proba[2]), float(proba[1]), float(proba[0]), row")

# 3. Sidebar Bankroll
sidebar_code = """
        st.markdown("<p style='font-size: 11px; color: rgba(255,255,255,0.3);'>Official Analytics Platform</p>", unsafe_allow_html=True)
        if df is not None:
            st.markdown(f"<p style='font-size: 11px; color: #00ff85;'>{len(df)} matches loaded</p>", unsafe_allow_html=True)
"""
new_sidebar = """
        st.markdown("<p style='font-size: 11px; color: rgba(255,255,255,0.3);'>Official Analytics Platform</p>", unsafe_allow_html=True)
        if df is not None:
            st.markdown(f"<p style='font-size: 11px; color: #00ff85;'>{len(df)} matches loaded</p>", unsafe_allow_html=True)
            
        user_bankroll = st.number_input(
            "GESTION DE BANCA", 
            min_value=100.0, 
            max_value=100000.0, 
            value=float(globals().get('STAKING_CONFIG', {}).get('bankroll', 1000)) if 'STAKING_CONFIG' in globals() else 1000.0,
            step=100.0
        )
"""
content = content.replace(sidebar_code, new_sidebar)

# 4. Extract render_match_card from app_dashboard.py
with open("app_dashboard.py", "r", encoding="utf-8") as fd:
    db_content = fd.read()
    match_card_match = re.search(r'(def render_match_card.*?)\n# --- APP ---', db_content, re.DOTALL)
    new_match_card = match_card_match.group(1).replace('get_team_logo(h)', '""').replace('get_team_logo(a)', '""')

content = re.sub(r'def render_match_card.*?(?=# --- MAIN ---)', new_match_card + "\n", content, flags=re.DOTALL)

# 5. Extract Tab 1 Logic from app_dashboard.py
tab1_match = re.search(r'(def render_model_picks.*?)\n\s+if not found_any:', db_content, re.DOTALL)
new_tab1_logic = tab1_match.group(1)

# Modify new_tab1_logic to work with app_premier.py's get_model_probs format
new_tab1_logic = new_tab1_logic.replace("h_clean, a_clean, m.get('date'), features=model_feats", "h, a")
new_tab1_logic = new_tab1_logic.replace("get_model_probs_for_match(df, active_model,", "get_model_probs(df, active_model,")
new_tab1_logic = new_tab1_logic.replace("ph, pd_prob, pa, X_row = probs_data", "ph, pd_prob, pa, X_row = probs_data")
new_tab1_logic = new_tab1_logic.replace("h_clean", "h").replace("a_clean", "a")
new_tab1_logic = new_tab1_logic.replace("get_team_stat(h, suffix)", "X_row.get(f'Home_{suffix}', 0)")
new_tab1_logic = new_tab1_logic.replace("get_team_stat(a, suffix)", "X_row.get(f'Away_{suffix}', 0)")
new_tab1_logic = new_tab1_logic.replace("h_elo = last_h_row['Home_Elo'] if last_h_row['HomeTeam'] == h else last_h_row['Away_Elo']", "h_elo = X_row.get('Home_Elo', 1500)")
new_tab1_logic = new_tab1_logic.replace("a_elo = last_a_row['Home_Elo'] if last_a_row['HomeTeam'] == a else last_a_row['Away_Elo']", "a_elo = X_row.get('Away_Elo', 1500)")
new_tab1_logic = new_tab1_logic.replace("h_sub_all", "False")
new_tab1_logic = new_tab1_logic.replace("a_sub_all", "False")

# Write the new content to app_premier.py
# First replace the old Tab 1 logic
old_tab1_pattern = r'matches = \[\]\n        if os\.path\.exists\(ODDS_FILE\):.*?# ======================================================\n    # TAB 2: TACTICAL SCOUTING'
new_tab1 = """matches = []
        if os.path.exists(ODDS_FILE):
            try: matches = json.load(open(ODDS_FILE))
            except: pass
            
        c1, c2, c3 = st.columns(3)
        c1.metric("Live Matches", str(len(matches)))
        c2.metric("Pitbull financiero V3", "[OK] Cargado" if model else "[FAIL] No encontrado")
        c3.metric("Signal Strength", "High")

        if not matches:
             st.info("No live market data available.", icon=None)
        elif df is None or model is None:
            st.warning("Datos o modelo no cargados correctamente.", icon=None)
        else:
            """ + new_tab1_logic.replace("active_model", "model").replace("def render_model_picks(model, model_label, label_color, min_ev=0.03):", "") + """
            
    # ======================================================
    # TAB 2: TACTICAL SCOUTING"""
    
content = re.sub(old_tab1_pattern, new_tab1, content, flags=re.DOTALL)

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)
