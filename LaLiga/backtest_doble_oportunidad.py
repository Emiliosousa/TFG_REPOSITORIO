"""
============================================================================
BACKTEST COMPARATIVO: Sin vs Con Doble Oportunidad
============================================================================
Compara dos estrategias:
  A) Solo apuestas simples (1, X, 2)
  B) Simples + Doble Oportunidad (1, X, 2, 1X, X2, 12)

Parametros del backtest (identicos al notebook):
  - Modelo: V3 Calibrado
  - EV minimo: 3%
  - Kelly: 1/4 (25%)
  - Max Stake: 5% del bankroll
  - Bankroll inicial: 1000 EUR
============================================================================
"""

import pandas as pd
import numpy as np
import joblib
import warnings
import os

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURACION
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'notebooks', 'df_final_clean.csv')
MODEL_V3_PATH = os.path.join(BASE_DIR, 'notebooks', 'modelo_v3_calibrado.joblib')
MODEL_V2_PATH = os.path.join(BASE_DIR, 'modelo_city_group.joblib')

INITIAL_BANKROLL = 1000.0
KELLY_FRACTION   = 0.25    # Kelly 1/4
MAX_KELLY_STAKE  = 0.05    # Max 5% bankroll
MIN_EV           = 0.03    # EV > 3%
MIN_ODDS         = 1.10    # Cuota minima

# =============================================================================
# CARGA DE DATOS
# =============================================================================
print("=" * 70)
print("BACKTEST COMPARATIVO: Sin vs Con Doble Oportunidad")
print("=" * 70)

df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values('Date').reset_index(drop=True)

# Target: 0=Away, 1=Draw, 2=Home
# FTR equivalent:  H=2, D=1, A=0
print(f"Total partidos cargados: {len(df)}")
print(f"Rango: {df['Date'].min().date()} - {df['Date'].max().date()}")
print(f"Temporadas: {sorted(df['Season'].unique())}")

# =============================================================================
# CARGAR MODELO
# =============================================================================
try:
    model = joblib.load(MODEL_V3_PATH)
    model_name = "V3 Calibrated"
    model_feats = model.get_booster().feature_names
    print(f"\nModelo: {model_name} ({len(model_feats)} features)")
except:
    model = joblib.load(MODEL_V2_PATH)
    model_name = "V2 Academic"
    model_feats = model.get_booster().feature_names
    print(f"\nModelo: {model_name} ({len(model_feats)} features)")

# =============================================================================
# DOUBLE CHANCE ODDS FORMULA
# =============================================================================
def double_chance_odds(o1, o2):
    """Cuota doble oportunidad = 1 / (1/o1 + 1/o2)"""
    if o1 > 0 and o2 > 0:
        return 1.0 / (1.0/o1 + 1.0/o2)
    return 1.0

# =============================================================================
# BACKTEST FUNCTION
# =============================================================================
def run_backtest(df, model, model_feats, include_double_chance=False, label=""):
    """
    Run backtest on historical data.
    
    For each match:
      1. Predict p_home, p_draw, p_away
      2. Calculate EV for each option (and double chance if enabled)
      3. Select the best EV option above threshold
      4. Calculate Kelly stake
      5. Simulate profit/loss
    """
    # Use only matches from 2015 onwards (allowing rolling features to stabilize)
    test_df = df[df['Season'] >= 2015].copy()
    
    # Ensure required columns exist
    required_odds = ['B365H', 'B365D', 'B365A']
    for c in required_odds:
        if c not in test_df.columns:
            print(f"  ERROR: Missing column {c}")
            return None
    
    bets = []
    seasons = sorted(test_df['Season'].unique())
    
    for season in seasons:
        season_df = test_df[test_df['Season'] == season]
        
        for idx, row in season_df.iterrows():
            # Get odds
            oh = float(row.get('B365H', 0))
            od = float(row.get('B365D', 0))
            oa = float(row.get('B365A', 0))
            
            if oh <= MIN_ODDS or od <= MIN_ODDS or oa <= MIN_ODDS:
                continue
            
            # Get model features
            available = [f for f in model_feats if f in row.index]
            if len(available) < len(model_feats) * 0.5:
                continue
            
            X = pd.DataFrame([{f: row.get(f, 0) for f in model_feats}])
            
            try:
                proba = model.predict_proba(X)[0]
                # proba order: [Away, Draw, Home] (classes 0, 1, 2)
                p_away = float(proba[0])
                p_draw = float(proba[1])
                p_home = float(proba[2])
            except:
                continue
            
            # Actual result
            actual = int(row['Target'])  # 0=Away, 1=Draw, 2=Home
            
            # --- SINGLE BETS ---
            options = {
                '1':  {'p': p_home, 'odds': oh, 'wins_if': actual == 2},
                'X':  {'p': p_draw, 'odds': od, 'wins_if': actual == 1},
                '2':  {'p': p_away, 'odds': oa, 'wins_if': actual == 0},
            }
            
            # --- DOUBLE CHANCE ---
            if include_double_chance:
                o_1x = double_chance_odds(oh, od)
                o_x2 = double_chance_odds(od, oa)
                o_12 = double_chance_odds(oh, oa)
                
                options['1X'] = {
                    'p': min(p_home + p_draw, 1.0), 
                    'odds': o_1x,
                    'wins_if': actual in (2, 1)  # Home or Draw
                }
                options['X2'] = {
                    'p': min(p_draw + p_away, 1.0), 
                    'odds': o_x2,
                    'wins_if': actual in (1, 0)  # Draw or Away
                }
                options['12'] = {
                    'p': min(p_home + p_away, 1.0), 
                    'odds': o_12,
                    'wins_if': actual in (2, 0)  # Home or Away
                }
            
            # --- EVALUATE ALL OPTIONS ---
            for bet_type, opt in options.items():
                ev = opt['p'] * opt['odds'] - 1
                
                if ev > MIN_EV and opt['odds'] > 1:
                    # Kelly stake
                    kelly_raw = (opt['p'] * opt['odds'] - 1) / (opt['odds'] - 1)
                    kelly_frac = kelly_raw * KELLY_FRACTION
                    kelly_frac = min(kelly_frac, MAX_KELLY_STAKE)
                    kelly_frac = max(kelly_frac, 0)
                    kelly_stake = kelly_frac * INITIAL_BANKROLL
                    
                    flat_stake = 10.0
                    
                    won = opt['wins_if']
                    flat_profit  = flat_stake * (opt['odds'] - 1) if won else -flat_stake
                    kelly_profit = kelly_stake * (opt['odds'] - 1) if won else -kelly_stake
                    
                    bets.append({
                        'Date': row['Date'],
                        'Season': season,
                        'HomeTeam': row.get('HomeTeam', ''),
                        'AwayTeam': row.get('AwayTeam', ''),
                        'Bet_Type': bet_type,
                        'Odds': opt['odds'],
                        'P_Model': opt['p'],
                        'EV': ev,
                        'Won': won,
                        'Flat_Stake': flat_stake,
                        'Flat_Profit': round(flat_profit, 2),
                        'Kelly_Stake': round(kelly_stake, 2),
                        'Kelly_Profit': round(kelly_profit, 2),
                    })
    
    if not bets:
        print(f"  {label}: No bets generated!")
        return None
    
    bets_df = pd.DataFrame(bets)
    bets_df = bets_df.sort_values('Date').reset_index(drop=True)
    
    return bets_df


# =============================================================================
# RUN BOTH BACKTESTS
# =============================================================================
print(f"\nParametros: Kelly {KELLY_FRACTION:.0%} | EV > {MIN_EV:.0%} | Max Stake {MAX_KELLY_STAKE:.0%}")
print(f"Bankroll inicial: {INITIAL_BANKROLL:.0f} EUR")
print()

print("-" * 70)
print("ESTRATEGIA A: Solo apuestas simples (1, X, 2)")
print("-" * 70)
bets_simple = run_backtest(df, model, model_feats, include_double_chance=False, label="Simple")

print("-" * 70)
print("ESTRATEGIA B: Simples + Doble Oportunidad (1, X, 2, 1X, X2, 12)")  
print("-" * 70)
bets_double = run_backtest(df, model, model_feats, include_double_chance=True, label="Doble Oportunidad")

# =============================================================================
# RESULTS COMPARISON
# =============================================================================
def print_results(bets_df, label):
    if bets_df is None:
        print(f"\n{label}: Sin resultados")
        return
    
    n_bets = len(bets_df)
    n_won  = bets_df['Won'].sum()
    hit_rate = n_won / n_bets
    
    flat_pnl  = bets_df['Flat_Profit'].sum()
    flat_roi   = flat_pnl / bets_df['Flat_Stake'].sum()
    
    kelly_pnl  = bets_df['Kelly_Profit'].sum()
    kelly_roi  = kelly_pnl / bets_df['Kelly_Stake'].sum()
    
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(f"  Total apuestas:       {n_bets}")
    print(f"  Acertadas:            {n_won} ({hit_rate:.1%})")
    print(f"  Flat P&L:             {flat_pnl:+,.2f} EUR")
    print(f"  Flat ROI:             {flat_roi:+.2%}")
    print(f"  Kelly P&L:            {kelly_pnl:+,.2f} EUR")
    print(f"  Kelly ROI:            {kelly_roi:+.2%}")
    
    # Per-season breakdown
    print(f"\n  {'Temporada':<10} {'Apuestas':>10} {'Hit Rate':>10} {'Flat ROI':>10} {'Kelly ROI':>10}")
    print(f"  {'-'*50}")
    for season in sorted(bets_df['Season'].unique()):
        s = bets_df[bets_df['Season'] == season]
        s_n = len(s)
        s_hit = s['Won'].mean()
        s_flat_roi = s['Flat_Profit'].sum() / s['Flat_Stake'].sum()
        s_kelly_roi = s['Kelly_Profit'].sum() / s['Kelly_Stake'].sum() if s['Kelly_Stake'].sum() > 0 else 0
        print(f"  {season:<10} {s_n:>10} {s_hit:>10.1%} {s_flat_roi:>+10.1%} {s_kelly_roi:>+10.1%}")
    
    # Breakdown by bet type
    print(f"\n  {'Tipo':<8} {'Apuestas':>10} {'Hit Rate':>10} {'Flat ROI':>12} {'Kelly ROI':>12}")
    print(f"  {'-'*55}")
    for bt in sorted(bets_df['Bet_Type'].unique()):
        bt_df = bets_df[bets_df['Bet_Type'] == bt]
        bt_n = len(bt_df)
        bt_hit = bt_df['Won'].mean()
        bt_flat_roi = bt_df['Flat_Profit'].sum() / bt_df['Flat_Stake'].sum()
        bt_kelly_roi = bt_df['Kelly_Profit'].sum() / bt_df['Kelly_Stake'].sum() if bt_df['Kelly_Stake'].sum() > 0 else 0
        print(f"  {bt:<8} {bt_n:>10} {bt_hit:>10.1%} {bt_flat_roi:>+12.2%} {bt_kelly_roi:>+12.2%}")


print_results(bets_simple, "ESTRATEGIA A: Solo Simples (1, X, 2)")
print_results(bets_double, "ESTRATEGIA B: Simples + Doble Oportunidad")

# =============================================================================
# HEAD-TO-HEAD COMPARISON
# =============================================================================
if bets_simple is not None and bets_double is not None:
    print(f"\n{'='*70}")
    print(f"  COMPARATIVA DIRECTA")
    print(f"{'='*70}")
    
    s_flat  = bets_simple['Flat_Profit'].sum() / bets_simple['Flat_Stake'].sum()
    s_kelly = bets_simple['Kelly_Profit'].sum() / bets_simple['Kelly_Stake'].sum()
    
    d_flat  = bets_double['Flat_Profit'].sum() / bets_double['Flat_Stake'].sum()
    d_kelly = bets_double['Kelly_Profit'].sum() / bets_double['Kelly_Stake'].sum()
    
    print(f"\n  {'Metrica':<25} {'Sin Doble':>15} {'Con Doble':>15} {'Diferencia':>15}")
    print(f"  {'-'*70}")
    print(f"  {'Num. Apuestas':<25} {len(bets_simple):>15} {len(bets_double):>15} {len(bets_double)-len(bets_simple):>+15}")
    print(f"  {'Hit Rate':<25} {bets_simple['Won'].mean():>15.1%} {bets_double['Won'].mean():>15.1%} {bets_double['Won'].mean()-bets_simple['Won'].mean():>+15.1%}")
    print(f"  {'Flat ROI':<25} {s_flat:>+15.2%} {d_flat:>+15.2%} {d_flat-s_flat:>+15.2%}")
    print(f"  {'Kelly ROI':<25} {s_kelly:>+15.2%} {d_kelly:>+15.2%} {d_kelly-s_kelly:>+15.2%}")
    print(f"  {'Flat P&L (EUR)':<25} {bets_simple['Flat_Profit'].sum():>+15,.2f} {bets_double['Flat_Profit'].sum():>+15,.2f} {bets_double['Flat_Profit'].sum()-bets_simple['Flat_Profit'].sum():>+15,.2f}")
    print(f"  {'Kelly P&L (EUR)':<25} {bets_simple['Kelly_Profit'].sum():>+15,.2f} {bets_double['Kelly_Profit'].sum():>+15,.2f} {bets_double['Kelly_Profit'].sum()-bets_simple['Kelly_Profit'].sum():>+15,.2f}")
    
    # Only double chance bets
    dc_bets = bets_double[bets_double['Bet_Type'].isin(['1X', 'X2', '12'])]
    if not dc_bets.empty:
        print(f"\n  Solo apuestas de Doble Oportunidad (1X, X2, 12):")
        print(f"    Total: {len(dc_bets)} apuestas")
        print(f"    Hit Rate: {dc_bets['Won'].mean():.1%}")
        dc_flat_roi = dc_bets['Flat_Profit'].sum() / dc_bets['Flat_Stake'].sum()
        dc_kelly_roi = dc_bets['Kelly_Profit'].sum() / dc_bets['Kelly_Stake'].sum() if dc_bets['Kelly_Stake'].sum() > 0 else 0
        print(f"    Flat ROI: {dc_flat_roi:+.2%}")
        print(f"    Kelly ROI: {dc_kelly_roi:+.2%}")
        print(f"    Flat P&L: {dc_bets['Flat_Profit'].sum():+,.2f} EUR")
    
    winner = "CON Doble Oportunidad" if d_kelly > s_kelly else "SIN Doble Oportunidad"
    print(f"\n  >>> GANADOR (Kelly ROI): {winner}")

print(f"\n{'='*70}")
print("Backtest completado.")
print(f"{'='*70}")
