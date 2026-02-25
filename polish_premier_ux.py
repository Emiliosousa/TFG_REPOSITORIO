import re
import os

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Improved render_match_card with better CSS and logic, removing the docstring text
new_render_match_card = """
def render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets=None):
    if value_bets is None: value_bets = set()
    
    def ev_cls(v): return "pl-ev-pos" if v > 0.03 else ("pl-ev-neg" if v < -0.05 else "")
    def badge_cls(v): return "pl-ev-badge-pos" if v > 0.03 else ("pl-ev-badge-neg" if v < -0.05 else "")
    
    has_value = any(op in value_bets for op in ['1', 'X', '2'])
    vb_badge = '<span class="pl-value-bet-badge">VALUE BET</span>' if has_value else ''
    
    # Simple implicit probs
    ih, id, ia = 1/oh if oh>0 else 0, 1/od if od>0 else 0, 1/oa if oa>0 else 0

    html = clean_html(f'''
        <div class="pl-card">
            <div class="pl-card-header">
                <div style="font-size: 10px; color: rgba(255,255,255,0.3); letter-spacing: 2px; text-transform: uppercase;">Premier League | Matchday</div>
                {vb_badge}
            </div>
            <div class="pl-teams">
                <span>{h}</span>
                <span class="pl-vs">VS</span>
                <span>{a}</span>
            </div>
            <div class="pl-odds-row">
                <div class="pl-odd-cell" style="{"border:1px solid #00ff85; background:rgba(0,255,133,0.05);" if '1' in value_bets else ""}">
                    <div class="pl-odd-label">Home (1)</div>
                    <div class="pl-odd-value {ev_cls(eh)}">{oh:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(eh)}">EV {eh:+.1%}</div>
                    <div style="font-size: 9px; opacity: 0.4; margin-top: 4px;">AI: {ph:.0%} | Mkt: {ih:.0%}</div>
                </div>
                <div class="pl-odd-cell" style="{"border:1px solid #00ff85; background:rgba(0,255,133,0.05);" if 'X' in value_bets else ""}">
                    <div class="pl-odd-label">Draw (X)</div>
                    <div class="pl-odd-value {ev_cls(ed)}">{od:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(ed)}">EV {ed:+.1%}</div>
                    <div style="font-size: 9px; opacity: 0.4; margin-top: 4px;">AI: {pd_prob:.0%} | Mkt: {id:.0%}</div>
                </div>
                <div class="pl-odd-cell" style="{"border:1px solid #00ff85; background:rgba(0,255,133,0.05);" if '2' in value_bets else ""}">
                    <div class="pl-odd-label">Away (2)</div>
                    <div class="pl-odd-value {ev_cls(ea)}">{oa:.2f}</div>
                    <div class="pl-ev-badge {badge_cls(ea)}">EV {ea:+.1%}</div>
                    <div style="font-size: 9px; opacity: 0.4; margin-top: 4px;">AI: {pa:.0%} | Mkt: {ia:.0%}</div>
                </div>
            </div>
        </div>
    ''')
    st.markdown(html, unsafe_allow_html=True)
"""

# Replace old render_match_card
content = re.sub(r'def render_match_card.*?(?=# --- MAIN ---)', new_render_match_card + "\n", content, flags=re.DOTALL)

# 2. Re-fix the main loop to be super clean and remove the leaked docstring
main_loop_start = """
        if not matches:
             st.info("No live market data available.", icon=None)
        elif df is None or model is None:
            st.warning("Datos o modelo no cargados correctamente.", icon=None)
        else:
            active_model = model
            min_ev = 0.03
            cols = st.columns(2)
            for idx, m in enumerate(matches):
                h, a = m.get('home'), m.get('away')
                h = TEAM_MAPPING.get(normalize_text_safe(h), h)
                a = TEAM_MAPPING.get(normalize_text_safe(a), a)

                probs_data = get_model_probs(df, model, h, a)
                if probs_data is None: continue
                
                ph, pd_prob, pa = probs_data[:3]
                X_row = probs_data[3] if len(probs_data) > 3 else {}

                try: oh, od, oa = float(m.get('1',1)), float(m.get('X',1)), float(m.get('2',1))
                except: oh,od,oa=1,1,1
                
                eh, ed, ea = (ph*oh)-1, (pd_prob*od)-1, (pa*oa)-1

                # Double Chance Logic
                def dc_odds(o1, o2): return 1/(1/o1 + 1/o2) if o1>0 and o2>0 else 1.0
                o_1x, o_x2, o_12 = dc_odds(oh,od), dc_odds(od,oa), dc_odds(oh,oa)
                p_1x, p_x2, p_12 = min(ph+pd_prob, 1.0), min(pd_prob+pa, 1.0), min(ph+pa, 1.0)
                e_1x, e_x2, e_12 = p_1x*o_1x-1, p_x2*o_x2-1, p_12*o_12-1
                
                h_elo = X_row.get('Home_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
                a_elo = X_row.get('Away_Elo', 1500) if isinstance(X_row, pd.Series) else 1500
                rank_diff = abs(h_elo - a_elo) / 100.0

                ev_map = {'1': eh, 'X': ed, '2': ea, '1X': e_1x, 'X2': e_x2, '12': e_12}
                p_map = {'1': ph, 'X': pd_prob, '2': pa, '1X': p_1x, 'X2': p_x2, '12': p_12}
                q_map = {'1': oh, 'X': od, '2': oa, '1X': o_1x, 'X2': o_x2, '12': o_12}
                
                value_bets = {op for op, ev in ev_map.items() if ev > min_ev}

                st_results = {}
                for op in ['1', 'X', '2']:
                    st_results[op] = calcular_stake_profesional(p_map[op], q_map[op], user_bankroll, rank_diff)

                with cols[idx % 2]:
                    render_match_card(h, a, oh, od, oa, eh, ed, ea, ph, pd_prob, pa, value_bets)
                    
                    # Double Chance Row
                    dc_html = f'''
                    <div style="margin-top:-10px; margin-bottom:10px; padding:0 10px;">
                        <div style="font-size:9px; opacity:0.4; margin-bottom:4px; font-weight:700;">DOBLE OPORTUNIDAD</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px;">
                            <div style="padding:6px; border-radius:4px; text-align:center; background:rgba(255,255,255,0.03); border:1px solid {"#00ff85" if '1X' in value_bets else "rgba(255,255,255,0.05)"};">
                                <div style="font-size:8px; opacity:0.6;">1X</div>
                                <div style="font-size:12px; font-weight:700;">{o_1x:.2f}</div>
                                <div style="font-size:9px; color:{"#00ff85" if e_1x > 0.03 else "rgba(255,255,255,0.3)"};">EV {e_1x:+.1%}</div>
                            </div>
                            <div style="padding:6px; border-radius:4px; text-align:center; background:rgba(255,255,255,0.03); border:1px solid {"#00ff85" if 'X2' in value_bets else "rgba(255,255,255,0.05)"};">
                                <div style="font-size:8px; opacity:0.6;">X2</div>
                                <div style="font-size:12px; font-weight:700;">{o_x2:.2f}</div>
                                <div style="font-size:9px; color:{"#00ff85" if e_x2 > 0.03 else "rgba(255,255,255,0.3)"};">EV {e_x2:+.1%}</div>
                            </div>
                            <div style="padding:6px; border-radius:4px; text-align:center; background:rgba(255,255,255,0.03); border:1px solid {"#00ff85" if '12' in value_bets else "rgba(255,255,255,0.05)"};">
                                <div style="font-size:8px; opacity:0.6;">12</div>
                                <div style="font-size:12px; font-weight:700;">{o_12:.2f}</div>
                                <div style="font-size:9px; color:{"#00ff85" if e_12 > 0.03 else "rgba(255,255,255,0.3)"};">EV {e_12:+.1%}</div>
                            </div>
                        </div>
                    </div>'''
                    st.markdown(clean_html(dc_html), unsafe_allow_html=True)

                    # Risk Badge
                    risk_level = "ALTO" if rank_diff < 0.5 else ("MEDIO" if rank_diff < 1.0 else "BAJO")
                    risk_color = "#ff2882" if risk_level == "ALTO" else ("#f59e0b" if risk_level == "MEDIO" else "#00ff85")
                    risk_html = f'''
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:6px 12px; border-radius:6px; margin-bottom:8px; border-left:3px solid {risk_color}; margin:0 10px 8px 10px;">
                        <span style="font-size:9px; color:rgba(255,255,255,0.5); font-weight:700; text-transform:uppercase;">Riesgo Algorítmico</span>
                        <div style="text-align:right;">
                            <span style="font-size:10px; font-weight:800; color:{risk_color};">{risk_level}</span>
                        </div>
                    </div>'''
                    st.markdown(clean_html(risk_html), unsafe_allow_html=True)
                    
                    # Stake Table
                    stake_rows = ""
                    for op in ['1', 'X', '2', '1X', 'X2', '12']:
                        odds, ev_val = q_map[op], ev_map[op]
                        if ev_val > min_ev and odds > 1:
                            kelly_raw = (p_map[op] * odds - 1) / (odds - 1)
                            kelly_frac = np.clip(kelly_raw * 0.25, 0, 0.05)
                            importe = round(kelly_frac * user_bankroll, 2)
                            color, amount, k_pct = "#00ff85", f"€{importe:.0f}", f"{kelly_frac:.1%}"
                        else:
                            color, amount, k_pct = "rgba(255,255,255,0.2)", "-", "-"
                        
                        stake_rows += f'<tr style="color:{color}; font-size:10px; border-bottom:1px solid rgba(255,255,255,0.03);"><td style="padding:3px;">{op}</td><td style="text-align:center;">{ev_val:+.1%}</td><td style="text-align:center;">{k_pct}</td><td style="text-align:right; font-weight:700;">{amount}</td></tr>'

                    stake_table = f'''
                    <div style="margin:0 10px 15px 10px;">
                        <table style="width:100%; border-collapse:collapse; background:rgba(0,0,0,0.15); border-radius:6px; overflow:hidden;">
                            <tr style="font-size:8px; opacity:0.4; background:rgba(255,255,255,0.03); text-transform:uppercase;">
                                <th style="padding:4px; text-align:left;">Pick</th>
                                <th style="text-align:center;">EV</th>
                                <th style="text-align:center;">Kelly</th>
                                <th style="text-align:right; padding-right:4px;">Stake</th>
                            </tr>
                            {stake_rows}
                        </table>
                    </div>'''
                    st.markdown(clean_html(stake_table), unsafe_allow_html=True)
                    
                    with st.expander("Ver Análisis Estadístico Detallado"):
                        # ... Detail logic ...
"""

# Replace the Tab 1 section
old_tab1_pattern = r'matches = \[\]\n        if os\.path\.exists\(ODDS_FILE\):.*?with st\.expander\("Ver Análisis Estadístico Detallado"\):'
content = re.sub(old_tab1_pattern, main_loop_start, content, flags=re.DOTALL)

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)

print("done")
