import re
import os
import numpy as np

def main():
    with open("app_premier.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add STAKING utils
    stake_import = """
def calcular_stake_profesional(prob, quota, bankroll, rank_diff=0):
    if prob * quota <= 1.0 or prob <= 0 or quota <= 1.0:
        return {'stake_pct': 0, 'importe': 0, 'filtro_pasado': False, 'razon_rechazo': 'EV Negativo'}
    kelly = (prob * quota - 1) / (quota - 1)
    kelly_fraction = kelly * 0.25 # Conservador
    if rank_diff < 0.5: stake_pct = np.clip(kelly_fraction, 0, 0.05)
    elif rank_diff < 1.0: stake_pct = np.clip(kelly_fraction, 0, 0.035)
    else: stake_pct = np.clip(kelly_fraction, 0, 0.02)
    importe = stake_pct * bankroll
    filtro_pasado = stake_pct > 0
    return {
        'stake_pct': stake_pct,
        'importe': round(importe, 2) if importe >= 1 else 0,
        'stake_scale': int(min(max(stake_pct / 0.05 * 10, 1), 10)) if stake_pct > 0 else 0,
        'filtro_pasado': filtro_pasado,
        'razon_rechazo': '' if filtro_pasado else 'Stake ~0',
        'edge_pct': (prob * quota - 1) * 100
    }
"""
    if "def calcular_stake_profesional" not in content:
        content = content.replace("# --- UTILS ---", "# --- UTILS ---\n" + stake_import)

    # 2. Modify get_model_probs to return row
    if "return float(proba[2]), float(proba[1]), float(proba[0]), row" not in content:
        content = content.replace("return float(proba[2]), float(proba[1]), float(proba[0])  # H, D, A", "return float(proba[2]), float(proba[1]), float(proba[0]), row")

    # 3. Get match card body replacement
    with open("app_dashboard.py", "r", encoding="utf-8") as fd:
        db_content = fd.read()
    
    match_card_match = re.search(r'(def render_match_card.*?)\n# --- APP ---', db_content, re.DOTALL)
    if match_card_match:
        new_match_card = match_card_match.group(1).replace('l_h, l_a = get_team_logo(h), get_team_logo(a)', 'l_h, l_a = "", ""').replace('<img src="{l_h}" style="width:40px;height:40px;object-fit:contain;">', '').replace('<img src="{l_a}" style="width:40px;height:40px;object-fit:contain;">', '')
        # Replace the premier match card
        content = re.sub(r'def render_match_card.*?(?=# --- MAIN ---)', new_match_card + "\n\n", content, flags=re.DOTALL)

    # 4. Extract render_model_picks logic (everything inside 'with tab1:' for the matches iteration)
    tab1_match = re.search(r'def render_model_picks\(.*?\):.*?(""".*?""").*?(found_any = False.*?)\n\s+if not found_any:', db_content, re.DOTALL)
    if tab1_match:
        html_head = tab1_match.group(1).replace('{model_label}', 'PREMIER LEAGUE LIVE TARGETS').replace('{label_color}', '#ff2882')
        new_logic = tab1_match.group(2)
        
        # Adapt for Premier League
        new_logic = new_logic.replace("h_clean, a_clean, m.get('date'), features=model_feats", "h, a")
        new_logic = new_logic.replace("get_model_probs_for_match(df, active_model,", "get_model_probs(df, model,")
        new_logic = new_logic.replace("X_row = probs_data", "X_row = probs_data[3] if len(probs_data) > 3 else {}")
        new_logic = new_logic.replace("h_clean", "h").replace("a_clean", "a")
        
        # Simplify team stat fetching (we don't need complex subqueries if we just use X_row)
        stat_repl = """
                            def get_team_stat(team, col_prefix, role='any'):
                                if role == 'home': return X_row.get(f'Home_{col_prefix}', 0)
                                if role == 'away': return X_row.get(f'Away_{col_prefix}', 0)
                                if team == h: return X_row.get(f'Home_{col_prefix}', 0)
                                if team == a: return X_row.get(f'Away_{col_prefix}', 0)
                                return 0
        """
        new_logic = re.sub(r'def get_team_stat.*?return 0', stat_repl, new_logic, flags=re.DOTALL, count=1)
        
        # ELO Replacement fix
        elo_code = """
                    h_elo = X_row.get('Home_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
                    a_elo = X_row.get('Away_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
        """
        new_logic = re.sub(r' +h_sub_all = .*?a_elo = 1500', elo_code, new_logic, flags=re.DOTALL)
        
        # Add the html wrapper that we stripped
        new_tab1_logic = f"""
                st.markdown(clean_html(f{html_head}), unsafe_allow_html=True)
                active_model = model
                min_ev = 0.03
                {new_logic}
        """

    # 5. Insert new Tab 1 Logic
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
            """ + new_tab1_logic + """
            
    # ======================================================
    # TAB 2: TACTICAL SCOUTING"""
    
    content = re.sub(old_tab1_pattern, new_tab1, content, flags=re.DOTALL)
    
    with open("app_premier.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
