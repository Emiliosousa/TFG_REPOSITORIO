import pandas as pd
import numpy as np

class FinancialEvaluator:
    """Evaluates the financial performance of the Pickslorax model via Walk-Forward Backtesting.
    """
    
    def __init__(self, initial_bankroll=1000, flat_stake_pct=0.01, min_ev=0.03, kelly_fraction=0.25, max_kelly_stake=0.05):
        self.initial_bankroll = initial_bankroll
        self.flat_stake_pct = flat_stake_pct
        self.flat_stake = initial_bankroll * flat_stake_pct
        self.min_ev = min_ev
        self.kelly_fraction = kelly_fraction
        self.max_kelly_stake = max_kelly_stake
        
    def _calculate_kelly_stake(self, p, odds):
        """Calculates Fractional Kelly Stake."""
        if (p * odds - 1) <= 0: return 0.0
        kelly_raw = (p * odds - 1) / (odds - 1)
        kelly_stake = kelly_raw * self.kelly_fraction
        return min(kelly_stake, self.max_kelly_stake) * self.initial_bankroll
        
    def backtest(self, df_bt, features, trainer_cls, best_params, window_size=5):
        """Runs a time-series cross-validation walk-forward backtest."""
        from sklearn.calibration import CalibratedClassifierCV
        import xgboost as xgb
        
        odds_cols = ['B365H', 'B365D', 'B365A']
        df_bt = df_bt.dropna(subset=odds_cols + features + ['Target']).sort_values('Date').reset_index(drop=True)
        seasons_bt = sorted(df_bt['Season'].unique())
        n_folds = len(seasons_bt) - window_size
        
        all_bets = []
        season_results = []
        
        for i in range(n_folds):
            train_seasons = seasons_bt[i : i + window_size]
            test_season = seasons_bt[i + window_size]
            
            tr_mask = df_bt['Season'].isin(train_seasons)
            te_mask = df_bt['Season'] == test_season
            
            X_tr, y_tr = df_bt.loc[tr_mask, features].astype(float), df_bt.loc[tr_mask, 'Target'].astype(int)
            X_te = df_bt.loc[te_mask, features].astype(float)
            
            # Sub-train without re-optimizing to prevent future peeking 
            fold_base = xgb.XGBClassifier(**best_params)
            fold_model = CalibratedClassifierCV(fold_base, method='isotonic', cv=3)
            if len(X_tr) > 0: fold_model.fit(X_tr, y_tr)
            
            probs = fold_model.predict_proba(X_te)
            
            df_season = df_bt.loc[te_mask].copy().reset_index(drop=True)
            df_season[['P_A', 'P_D', 'P_H']] = probs
            
            fold_bets = []
            for _, row in df_season.iterrows():
                for outcome_idx, (prob_col, odds_col) in enumerate(zip(['P_A', 'P_D', 'P_H'], odds_cols)):
                    p, odds = row[prob_col], row[odds_col]
                    ev = p * odds - 1
                    
                    if ev > self.min_ev:
                        kelly_stake = self._calculate_kelly_stake(p, odds)
                        result_map = {0: 'A', 1: 'D', 2: 'H'}
                        won = result_map[outcome_idx] == row['FTR']
                        
                        # Yield vs Bankroll Growth distinction
                        # flat_profit is NET profit (payout minus wager). 
                        flat_profit = self.flat_stake * (odds - 1) if won else -self.flat_stake
                        kelly_profit = kelly_stake * (odds - 1) if won else -kelly_stake
                        
                        fold_bets.append({
                            'Season': test_season,
                            'Date': row['Date'],
                            'Match': f"{row['HomeTeam']} vs {row['AwayTeam']}",
                            'Bet': result_map[outcome_idx],
                            'Odds': odds, 'P_model': p, 'EV': ev,
                            'Flat_Stake': self.flat_stake, 'Kelly_Stake': kelly_stake,
                            'Won': won, 'Flat_Profit': flat_profit, 'Kelly_Profit': kelly_profit
                        })
            
            all_bets.extend(fold_bets)
            
            if fold_bets:
                b_df = pd.DataFrame(fold_bets)
                season_results.append({
                    'Season': test_season,
                    'N_Bets': len(b_df),
                    'Hit_Rate': b_df['Won'].mean(),
                    'Yield_Flat': b_df['Flat_Profit'].sum() / (len(b_df) * self.flat_stake), # Net ROI per stake
                    'Yield_Kelly': b_df['Kelly_Profit'].sum() / b_df['Kelly_Stake'].sum(),
                    'Flat_PnL': b_df['Flat_Profit'].sum(),
                    'Kelly_PnL': b_df['Kelly_Profit'].sum()
                })
        
        return pd.DataFrame(all_bets), pd.DataFrame(season_results)
        
    def generate_financial_summary(self, df_bets: pd.DataFrame, season_results: pd.DataFrame):
        """Generates the executive summary cleanly differentiating Yield and Bankroll Growth."""
        df_bets = df_bets.sort_values('Date').reset_index(drop=True)
        # Bankroll Growth simulation
        df_bets['Flat_Bankroll'] = self.initial_bankroll + df_bets['Flat_Profit'].cumsum()
        df_bets['Kelly_Bankroll'] = self.initial_bankroll + df_bets['Kelly_Profit'].cumsum()
        
        total_bets = len(df_bets)
        flat_pnl = df_bets['Flat_Profit'].sum()
        kelly_pnl = df_bets['Kelly_Profit'].sum()
        
        # KEY DIFFERENTIATION FOR TFG
        # Yield (ROI del modelo por 1 EUR apostado) vs Bankroll Growth (Crecimiento del capital)
        flat_yield = flat_pnl / (total_bets * self.flat_stake)
        kelly_yield = kelly_pnl / df_bets['Kelly_Stake'].sum()
        
        flat_bankroll_growth = flat_pnl / self.initial_bankroll
        kelly_bankroll_growth = kelly_pnl / self.initial_bankroll
        
        # Risk Multipliers
        roll_max_flat = df_bets['Flat_Bankroll'].cummax()
        max_dd_flat = ((df_bets['Flat_Bankroll'] - roll_max_flat) / roll_max_flat).min()
        
        metrics = {
            'period': f'{df_bets["Season"].min()} - {df_bets["Season"].max()}',
            'total_bets': total_bets,
            'hit_rate': df_bets['Won'].mean(),
            'model_yield': flat_yield, # Yield Neto Real
            'bankroll_growth': flat_bankroll_growth,
            'kelly_model_yield': kelly_yield,
            'kelly_bankroll_growth': kelly_bankroll_growth,
            'max_drawdown': max_dd_flat,
            'total_pnl': flat_pnl,
            'kelly_total_pnl': kelly_pnl,
        }
        return metrics, df_bets
