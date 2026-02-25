import re
import os

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

# Markers
m1 = "# TAB 1: LIVE MARKET"
m2 = "# TAB 2: TACTICAL SCOUTING"

idx1 = content.find(m1)
idx2 = content.find(m2)

if idx1 != -1 and idx2 != -1:
    tab1_code = r'''# TAB 1: LIVE MARKET
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
            active_model = model
            min_ev = 0.03
            cols = st.columns(2)
            for idx, m in enumerate(matches):
                h_name, a_name = m.get('home'), m.get('away')
                h = TEAM_MAPPING.get(normalize_text_safe(h_name), h_name)
                a = TEAM_MAPPING.get(normalize_text_safe(a_name), a_name)

                probs_data = get_model_probs(df, model, h, a)
                if probs_data is None: continue
                
                ph, pd_prob, pa = probs_data[:3]
                X_row = probs_data[3] if len(probs_data) > 3 else {}

                try: oh, od, oa = float(m.get('1',1)), float(m.get('X',1)), float(m.get('2',1))
                except: oh,od,oa=1,1,1
                
                eh, ed, ea = (ph*oh)-1, (pd_prob*od)-1, (pa*oa)-1

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
                    
                    dc_html = f'<div style="background:rgba(61,25,91,0.2); border:1px solid rgba(255,40,130,0.1); border-top:none; padding:10px; margin-bottom:10px; border-radius:0 0 12px 12px; margin-top:-10px;"><div style="font-size:9px; opacity:0.4; margin-bottom:6px; font-weight:700; letter-spacing:1px;">DOBLE OPORTUNIDAD</div><div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px;"><div style="padding:6px; border-radius:4px; text-align:center; background:rgba(0,0,0,0.2); border:1px solid {"#00ff85" if "1X" in value_bets else "rgba(255,255,255,0.05)"};"><div style="font-size:8px; opacity:0.5;">1X</div><div style="font-size:12px; font-weight:700;">{o_1x:.2f}</div><div style="font-size:9px; color:{"#00ff85" if e_1x > 0.03 else "rgba(255,255,255,0.2)"}; font-weight:600;">EV {e_1x:+.1%}</div></div><div style="padding:6px; border-radius:4px; text-align:center; background:rgba(0,0,0,0.2); border:1px solid {"#00ff85" if "X2" in value_bets else "rgba(255,255,255,0.05)"};"><div style="font-size:8px; opacity:0.5;">X2</div><div style="font-size:12px; font-weight:700;">{o_x2:.2f}</div><div style="font-size:9px; color:{"#00ff85" if e_x2 > 0.03 else "rgba(255,255,255,0.2)"}; font-weight:600;">EV {e_x2:+.1%}</div></div><div style="padding:6px; border-radius:4px; text-align:center; background:rgba(0,0,0,0.2); border:1px solid {"#00ff85" if "12" in value_bets else "rgba(255,255,255,0.05)"};"><div style="font-size:8px; opacity:0.5;">12</div><div style="font-size:12px; font-weight:700;">{o_12:.2f}</div><div style="font-size:9px; color:{"#00ff85" if e_12 > 0.03 else "rgba(255,255,255,0.2)"}; font-weight:600;">EV {e_12:+.1%}</div></div></div></div>'
                    st.markdown(clean_html(dc_html), unsafe_allow_html=True)

                    risk_lvl = "ALTO" if rank_diff < 0.5 else ("MEDIO" if rank_diff < 1.0 else "BAJO")
                    risk_clr = "#ff2882" if risk_lvl == "ALTO" else ("#f59e0b" if risk_lvl == "MEDIO" else "#00ff85")
                    risk_html = f'<div style="display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.15); padding:8px 12px; border-radius:6px; margin-bottom:10px; border-left:4px solid {risk_clr};"><span style="font-size:10px; color:rgba(255,255,255,0.6); font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">Riesgo del Algoritmo</span><div style="text-align:right;"><span style="font-size:11px; font-weight:900; color:{risk_clr};">{risk_lvl}</span></div></div>'
                    st.markdown(clean_html(risk_html), unsafe_allow_html=True)
                    
                    stk_rows = ""
                    for op_s in ["1", "X", "2", "1X", "X2", "12"]:
                        o_s, e_s = q_map[op_s], ev_map[op_s]
                        if e_s > min_ev and o_s > 1:
                            k_r = (p_map[op_s] * o_s - 1) / (o_s - 1)
                            k_f = np.clip(k_r * 0.25, 0, 0.05)
                            imp = round(k_f * user_bankroll, 2)
                            clr_s, amt_s, kp_s = "#00ff85", f"€{imp:.0f}", f"{k_f:.1%}"
                        else:
                            clr_s, amt_s, kp_s = "rgba(255,255,255,0.2)", "-", "-"
                        stk_rows += f"<tr style='color:{clr_s}; font-size:10px; border-bottom:1px solid rgba(255,255,255,0.03);'><td style='padding:4px; font-weight:600;'>{op_s}</td><td style='text-align:center;'>{e_s:+.1%}</td><td style='text-align:center;'>{kp_s}</td><td style='text-align:right; font-weight:800; padding:4px;'>{amt_s}</td></tr>"

                    stk_tbl = f'<table style="width:100%; border-collapse:collapse; background:rgba(0,0,0,0.1); border-radius:8px; overflow:hidden; margin-bottom:15px;"><tr style="font-size:9px; opacity:0.4; background:rgba(255,255,255,0.03);"><th style="padding:6px; text-align:left;">Selección</th><th style="text-align:center;">EV</th><th style="text-align:center;">Kelly</th><th style="text-align:right; padding:6px;">Importe</th></tr>{stk_rows}</table>'
                    st.markdown(clean_html(stk_tbl), unsafe_allow_html=True)
                    
                    with st.expander("Ver Análisis Estadístico Detallado"):
                        grid_h = ""
                        for op_g in ["1", "X", "2"]:
                            p_g, o_g = p_map[op_g], q_map[op_g]
                            res = st_results.get(op_g)
                            if res and res.get("filtro_pasado"):
                                b_g, s_g, v_g, e_g = "border-left: 3px solid #00ff85;", "<span style='color:#00ff85; font-weight:700;'>VIABLE</span>", f"<div style='color:#00ff85; font-size:14px; font-weight:800;'>{res['stake_scale']}/10 ({res['importe']}€)</div>", f"+{res['edge_pct']:.1f}%"
                            elif res:
                                b_g, s_g, v_g, e_g = "border-left: 3px solid rgba(255,255,255,0.1);", f"<span style='color:rgba(255,255,255,0.4); font-size:10px;'>{res['razon_rechazo']}</span>", "<div style='color:rgba(255,255,255,0.2); font-size:12px; font-weight:700;'>DESCARTADO</div>", f"{res['edge_pct']:+.1f}%"
                            else:
                                b_g, s_g, v_g, e_g = "border-left: 3px solid rgba(255,255,255,0.1);", "<span style='color:rgba(255,255,255,0.4); font-size:10px;'>Sin Data</span>", "<div style='color:rgba(255,255,255,0.2); font-size:12px; font-weight:700;'>N/A</div>", "-"
                            grid_h += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:10px; background:rgba(0,0,0,0.2); margin-bottom:6px; border-radius:4px; {b_g}'><div><div style='font-size:12px; font-weight:700; color:white;'>Opción {op_g} <span style='font-size:10px; color:rgba(255,255,255,0.3); font-weight:400; margin-left:6px;'>@ {o_g:.2f}</span></div><div style='font-size:10px; margin-top:4px;'>Edge: <span style='font-weight:700; color:white;'>{e_g}</span> <span style='margin:0 6px;opacity:0.2;'>|</span> {s_g}</div></div><div style='text-align:right;'>{v_g}</div></div>"
                        st.markdown(clean_html(grid_h), unsafe_allow_html=True)
                        
                        rt_rows = ""
                        for lbl, mk in [('Elo', 'Elo'), ('FIFA OVR', 'FIFA_Ova'), ('Value', 'Market_Value'), ('xG (L5)', 'xG_Avg_L5'), ('Streak', 'Streak_L5')]:
                            hv, av = X_row.get(f'Home_{mk}', 0), X_row.get(f'Away_{mk}', 0)
                            hs = "color:#00ff85; font-weight:700;" if hv > av else ""
                            as_ = "color:#00ff85; font-weight:700;" if av > hv else ""
                            rt_rows += f"<div style='display:flex; justify-content:space-between; padding:6px 12px; border-bottom:1px solid rgba(255,255,255,0.03); background:rgba(0,0,0,0.1); font-size:11px;'><div style='flex:1; opacity:0.5; font-size:9px;'>{lbl}</div><div style='flex:1; text-align:center; {hs}'>{hv:,.0f}</div><div style='flex:1; text-align:right; {as_}'>{av:,.0f}</div></div>"
                        rt_h = f"<div style='margin-top:10px; border:1px solid rgba(255,255,255,0.05); border-radius:8px; overflow:hidden;'><div style='display:flex; justify-content:space-between; padding:8px 12px; background:rgba(255,255,255,0.03); font-size:9px; opacity:0.4; font-weight:700;'><div style='flex:1;'>STAT</div><div style='flex:1; text-align:center;'>HOME</div><div style='flex:1; text-align:right;'>AWAY</div></div>{rt_rows}</div>"
                        st.markdown(clean_html(rt_h), unsafe_allow_html=True)
    '''
    
    new_content = content[:idx1] + tab1_code + content[idx2:]
    
    with open("app_premier.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Done")
else:
    print("Markers not found")
'''

with open("surgical_ux_fix.py", "w", encoding="utf-8") as f:
    f.write(fix_code)
