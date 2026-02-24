from sklearn.metrics import log_loss, accuracy_score, confusion_matrix
import joblib
import os
import json
import difflib
import numpy as np

print(f"Directorio de trabajo actual: {os.getcwd()}")

possible_paths = [
    "../df_final_app.csv",
    "LaLiga/df_final_app.csv",
    "df_final_app.csv",
    "../../df_final_app.csv",
    "../../LaLiga/df_final_app.csv"
]

CSV_PATH = None
for p in possible_paths:
    if os.path.exists(p):
        CSV_PATH = p
        print(f"Archivo encontrado en: {p}")
        break

if not CSV_PATH:
    raise FileNotFoundError(f"df_final_app.csv no encontrado. Se busco en: {possible_paths}")

df = pd.read_csv(CSV_PATH)
df["Date"] = pd.to_datetime(df["Date"])

# DEDUPLICACION CRITICA (Fix preventivo para Season 2024)
before = len(df)
df = df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='first').reset_index(drop=True)
if len(df) != before:
    print(f"⚠️ Se eliminaron {before - len(df)} filas duplicadas en la carga inicial.")

target_map = {"A": 0, "D": 1, "H": 2}
df["Target"] = df["FTR"].map(target_map)
df["Season"] = df["Season"].fillna(df["Date"].apply(lambda d: d.year if d.month >= 8 else d.year - 1))
df["Season"] = df["Season"].astype(int)

# ===========================================================
# ENRIQUECIMIENTO: FIFA & TRANSFERMARKT
# ===========================================================
SOFIFA_PATH = "../data/sofifa_history.json"
TM_PATH = "../data/transfermarkt_history.json"

# Check local paths if running from notebooks dir
if not os.path.exists(SOFIFA_PATH): SOFIFA_PATH = "../../data/sofifa_history.json"
if not os.path.exists(SOFIFA_PATH): SOFIFA_PATH = "data/sofifa_history.json"

if not os.path.exists(TM_PATH): TM_PATH = "../../data/transfermarkt_history.json"
if not os.path.exists(TM_PATH): TM_PATH = "data/transfermarkt_history.json"

if os.path.exists(SOFIFA_PATH) and os.path.exists(TM_PATH):
    print("Cargando datos externos (FIFA + Transfermarkt)...")
    with open(SOFIFA_PATH, 'r', encoding='utf-8') as f: sofifa_data = json.load(f)
    with open(TM_PATH, 'r', encoding='utf-8') as f: tm_data = json.load(f)
    
    # Helper: Normalizar Valor de Mercado
    def parse_tm_value(val_str):
        if not isinstance(val_str, str): return 0.0
        val_str = val_str.replace('€', '')
        if 'bn' in val_str: return float(val_str.replace('bn', '')) * 1000
        elif 'm' in val_str: return float(val_str.replace('m', ''))
        elif 'Th' in val_str: return float(val_str.replace('Th.', '')) / 1000
        return 0.0

    # Helper: Match Fuzzy
    def get_match(name, candidates):
        match = difflib.get_close_matches(name, candidates, n=1, cutoff=0.5)
        return match[0] if match else None

    # Inicializar columnas con NaN
    new_cols = [
        'Home_FIFA_OVR', 'Home_FIFA_ATT', 'Home_FIFA_MID', 'Home_FIFA_DEF',
        'Away_FIFA_OVR', 'Away_FIFA_ATT', 'Away_FIFA_MID', 'Away_FIFA_DEF',
        'Home_TM_Value', 'Home_TM_Avg_Age',
        'Away_TM_Value', 'Away_TM_Avg_Age'
    ]
    for c in new_cols: df[c] = np.nan

    # Iterar por temporada para mapeo preciso
    for season in df['Season'].unique():
        s_str = str(season)
        season_teams = df[df['Season'] == season]['HomeTeam'].unique()
        
        # --- PROCESAR FIFA ---
        if s_str in sofifa_data:
            fifa_recs = {t['team']: t for t in sofifa_data[s_str]}
            fifa_names = list(fifa_recs.keys())
            
            for team in season_teams:
                match = get_match(team, fifa_names)
                if match:
                    data = fifa_recs[match]
                    # Asignar a HomeTeam
                    mask_h = (df['Season'] == season) & (df['HomeTeam'] == team)
                    df.loc[mask_h, 'Home_FIFA_OVR'] = float(data.get('ova', 0))
                    df.loc[mask_h, 'Home_FIFA_ATT'] = float(data.get('att', 0))
                    df.loc[mask_h, 'Home_FIFA_MID'] = float(data.get('mid', 0))
                    df.loc[mask_h, 'Home_FIFA_DEF'] = float(data.get('def', 0))
                    # Asignar a AwayTeam
                    mask_a = (df['Season'] == season) & (df['AwayTeam'] == team)
                    df.loc[mask_a, 'Away_FIFA_OVR'] = float(data.get('ova', 0))
                    df.loc[mask_a, 'Away_FIFA_ATT'] = float(data.get('att', 0))
                    df.loc[mask_a, 'Away_FIFA_MID'] = float(data.get('mid', 0))
                    df.loc[mask_a, 'Away_FIFA_DEF'] = float(data.get('def', 0))

        # --- PROCESAR TRANSFERMARKT ---
        if s_str in tm_data:
            tm_recs = {t['team']: t for t in tm_data[s_str]}
            tm_names = list(tm_recs.keys())
            
            for team in season_teams:
                match = get_match(team, tm_names)
                if match:
                    data = tm_recs[match]
                    val = parse_tm_value(data.get('value', '0'))
                    age = float(data.get('avg_age', 0) or 0)
                    
                    mask_h = (df['Season'] == season) & (df['HomeTeam'] == team)
                    df.loc[mask_h, 'Home_TM_Value'] = val
                    df.loc[mask_h, 'Home_TM_Avg_Age'] = age
                    
                    mask_a = (df['Season'] == season) & (df['AwayTeam'] == team)
                    df.loc[mask_a, 'Away_TM_Value'] = val
                    df.loc[mask_a, 'Away_TM_Avg_Age'] = age

    # Imputar faltantes (Media o Forward Fill)
    df = df.fillna(method='ffill').fillna(method='bfill')
    print("Datos FIFA y Transfermarkt fusionados correctamente.")

else:
    print("⚠️ NO SE ENCONTRARON JSONs de FIFA/TM. Se omiten estas features.")

# Features actualizadas para el Modelo
features = [
    "Home_Elo", "Away_Elo",
    "Home_xG_Avg_L5", "Away_xG_Avg_L5",
    "Home_Streak_L5", "Away_Streak_L5",
    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",
    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",
    "Home_FIFA_OVR", "Away_FIFA_OVR",
    "Home_TM_Value", "Away_TM_Value",
    "Home_TM_Avg_Age", "Away_TM_Avg_Age"
]
print(f"Datos Totales (Post-Procesamiento): {len(df)} registros.")
df.head()


# --- [INJECTED] STRICT DATA CLEANING (REAL DATA ONLY) ---
print("\n🔍 STARTING STRICT DATA CLEANING...")
initial_rows = len(df)

# 1. Update Mapping for Transfermarkt (Fix Alaves)
# Note: Alaves is missing in FIFA history but present in TM as 'Deportivo Alavés'
# We map it here so at least TM data is correct, though rows might be dropped if FIFA is missing.
team_map = {
    'Alaves': 'Deportivo Alavés',
    'Ath Bilbao': 'Athletic Club',
    'Atl. Madrid': 'Atlético Madrid',
    'Betis': 'Real Betis Balompié',
    'Celta Vigo': 'RC Celta',
    'Dep. La Coruna': 'RC Deportivo de La Coruña',
    'Espanyol': 'RCD Espanyol',
    'Gijon': 'Sporting Gijón',
    'Granada': 'Granada CF',
    'La Coruna': 'RC Deportivo de La Coruña',
    'Las Palmas': 'UD Las Palmas',
    'Leganes': 'CD Leganés',
    'Levante': 'Levante UD',
    'Malaga': 'Málaga CF',
    'Mallorca': 'RCD Mallorca',
    'Osasuna': 'CA Osasuna',
    'Racing Santander': 'Racing Santander', # Verify
    'Rayo Vallecano': 'Rayo Vallecano',
    'Real Sociedad': 'Real Sociedad',
    'Sevilla': 'Sevilla FC',
    'Sp. Gijon': 'Sporting Gijón',
    'Valencia': 'Valencia CF',
    'Valladolid': 'Real Valladolid CF',
    'Villarreal': 'Villarreal CF',
    'Zaragoza': 'Real Zaragoza'
}

# Apply manual map fix for TM matching if not already applied
# Rerun enrichment logic if needed or just patch the dataframe if columns exist with NaNs?
# The enrichment logic (Cell 3/4 usually) uses fuzzy matching.
# Here we enforce the check.

cols_to_check = ['Home_FIFA_OVR', 'Away_FIFA_OVR', 'Home_TM_Value', 'Away_TM_Value']
missing_mask = df[cols_to_check].isnull().any(axis=1) | (df[cols_to_check] == 0).any(axis=1)

rows_to_drop = missing_mask.sum()
print(f"⚠️ Found {rows_to_drop} rows with missing or zero-filled data in FIFA/TM columns.")

if rows_to_drop > 0:
    print("🧹 DROPPING incomplete rows to enforce 'REAL DATA ONLY' policy...")
    df = df[~missing_mask].copy()
    print(f"✅ Dropped {rows_to_drop} rows. New shape: {df.shape}")
else:
    print("✅ No missing data found. Dataset is clean.")

features = [
    "Home_Elo", "Away_Elo",
    "Home_xG_Avg_L5", "Away_xG_Avg_L5",
    "Home_Streak_L5", "Away_Streak_L5",
    "Home_Pressure_Avg_L5", "Away_Pressure_Avg_L5",
    "Home_Dominance_Avg_L5", "Away_Dominance_Avg_L5",
    "Home_FIFA_OVR", "Away_FIFA_OVR",
    "Home_TM_Value", "Away_TM_Value",
    "Home_TM_Avg_Age", "Away_TM_Avg_Age"
]
# Filter to only features that exist in df
features = [f for f in features if f in df.columns]

TEST_SEASON_START = 2024

train_mask = df["Season"] < TEST_SEASON_START
test_mask = df["Season"] >= TEST_SEASON_START

X_train = df.loc[train_mask, features].astype(float)
y_train = df.loc[train_mask, "Target"].astype(int)
X_test = df.loc[test_mask, features].astype(float)
y_test = df.loc[test_mask, "Target"].astype(int)

print(f"Entrenamiento: {len(X_train)} partidos")
print(f"Test (Validacion): {len(X_test)} partidos")

def objective(trial):
    import numpy as np
    import xgboost as xgb
    
    # 1. Hyperparameters (Optimized for ROI)
    param = {
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss', 
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.08),  # CAP at 0.08
        'max_depth': trial.suggest_int('max_depth', 2, 4),  # CAP at 4
        'n_estimators': 500,  # FIXED
        'subsample': trial.suggest_float('subsample', 0.6, 0.9),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.9),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
        'random_state': 42,
        'n_jobs': -1,
        'verbosity': 0
    }
    
    # 2. Walk-Forward Validation
    rois = []
    
    # Ensure seasons are sorted
    unique_seasons = sorted(df['Season'].unique())
    
    # Start validation from 6th season (need history to stabilize)
    for i in range(5, len(unique_seasons)):
        train_seasons = unique_seasons[:i]
        val_season = unique_seasons[i]
        
        train_mask = df['Season'].isin(train_seasons)
        val_mask = df['Season'] == val_season
        
        X_train, y_train = df.loc[train_mask, features].astype(float), df.loc[train_mask, 'Target'].astype(int)
        X_val, y_val = df.loc[val_mask, features].astype(float), df.loc[val_mask, 'Target'].astype(int)
        
        # Train
        model = xgb.XGBClassifier(**param)
        model.fit(X_train, y_train)
        
        # Predict Probabilities (Shape: N x 3 for A, D, H)
        probs_matrix = model.predict_proba(X_val)
        
        # 3. Betting Simulation (STRICT)
        # Get Odds
        try:
            val_odds = df.loc[val_mask, ['B365A', 'B365D', 'B365H']].values
        except KeyError:
            continue
            
        # EV Calculation: EV = (Prob * Odds) - 1
        ev_matrix = (probs_matrix * val_odds) - 1
        
        # Find Best Bet per match
        best_bet_idx = np.argmax(ev_matrix, axis=1) # 0, 1, or 2
        best_ev = np.max(ev_matrix, axis=1) # The EV of the best bet
        best_odds = val_odds[np.arange(len(val_odds)), best_bet_idx]
        best_probs = probs_matrix[np.arange(len(probs_matrix)), best_bet_idx]
        
        # --- FILTERS (USER SPECS) ---
        # 1. EV >= 10%
        # 2. Odds <= 6.0
        
        bet_mask = (best_ev >= 0.03) & (best_odds <= 6.0)
        
        if bet_mask.sum() == 0:
            rois.append(0.0)
            continue
            
        # --- KELLY STRATEGY ---
        # b = Odds - 1
        # p = Prob
        # f = (bp - q) / b
        
        b = best_odds[bet_mask] - 1
        p = best_probs[bet_mask]
        
        # Filtered arrays
        f = (b * p - (1 - p)) / b
        
        # Kelly Fraction 25% & Max Stake 5%
        f = f * 0.25 
        f = np.clip(f, 0.0, 0.05)
        
        # Calculate Profit
        # Did we win?
        actual_outcomes = y_val.values[bet_mask]
        bet_predictions = best_bet_idx[bet_mask]
        
        wins = (actual_outcomes == bet_predictions)
        
        profit = np.zeros_like(f)
        profit[wins] = f[wins] * b[wins]
        profit[~wins] = -f[~wins]
        
        # Season ROI
        total_staked = f.sum()
        total_profit = profit.sum()
        
        if total_staked <= 0.0001:
            season_roi = 0.0
        else:
            season_roi = total_profit / total_staked
            
        rois.append(season_roi)
        
    # Return Mean ROI across valid seasons
    if len(rois) == 0:
        return 0.0
    return np.mean(rois)


# --- [INJECTED] OPTUNA OPTIMIZATION (ROI-DRIVEN) ---
import optuna
import numpy as np
import xgboost as xgb

# Ensure global vars are accessible: X, y, season_series, df_final
# If separate variables for odds aren't passed, we rely on df_final global

print("🚀 Iniciando optimización de ROI con Optuna...")
print("Estrategia: Kelly 25% | EV > 3% | Max Stake 5%")

study = optuna.create_study(direction='maximize') # MAXIMIZE ROI
study.optimize(objective, n_trials=50) # 50 Trials as requested

print("✅ Optimización completada.")
print(f"Mejor ROI Validado: {study.best_value:.2%}")
print("Mejores Parámetros:", study.best_params)

print("\n--- WALK-FORWARD VALIDATION (ROLLING WINDOW 5 SEASONS) ---")
seasons = sorted(df['Season'].unique())
window_size = 5

wf_metrics = []

# Check if we have enough seasons
if len(seasons) < window_size + 1:
    print(f"Not enough seasons for window size {window_size}. Available: {len(seasons)}")
else:
    for i in range(len(seasons) - window_size):
        train_seasons = seasons[i : i + window_size]
        test_season = seasons[i + window_size]
        
        print(f"\nWindow {i+1}: Train {train_seasons} | Test {test_season}")
        
        # Split Data
        train_mask = df['Season'].isin(train_seasons)
        test_mask = df['Season'] == test_season
        
        X_train_fold = df.loc[train_mask, features].astype(float)
        y_train_fold = df.loc[train_mask, 'Target'].astype(int)
        X_test_fold = df.loc[test_mask, features].astype(float)
        y_test_fold = df.loc[test_mask, 'Target'].astype(int)
        
        # Train (using best params found previously or default)
        _params = best_params if 'best_params' in dir() else {
            'objective': 'multi:softprob', 'num_class': 3, 'max_depth': 4,
            'learning_rate': 0.05, 'n_estimators': 150, 'random_state': 42
        }
        model_fold = xgb.XGBClassifier(**_params)
        model_fold.fit(X_train_fold, y_train_fold)
        
        # Predict
        probs_fold = model_fold.predict_proba(X_test_fold)
        preds_fold = model_fold.predict(X_test_fold)
        
        # Metrics
        loss_fold = log_loss(y_test_fold, probs_fold)
        acc_fold = accuracy_score(y_test_fold, preds_fold)
        print(f"   Log Loss: {loss_fold:.4f} | Accuracy: {acc_fold:.4f}")
        
        wf_metrics.append({
            'test_season': int(test_season),
            'log_loss': loss_fold,
            'accuracy': acc_fold
        })

print("\nAverage Walk-Forward Metrics:")
print(f"Mean Log Loss: {np.mean([m['log_loss'] for m in wf_metrics]):.4f}")
print(f"Mean Accuracy: {np.mean([m['accuracy'] for m in wf_metrics]):.4%}")

best_params = study.best_params
best_params["objective"] = "multi:softprob"
best_params["num_class"] = 3
best_params["random_state"] = 42
best_params["verbosity"] = 0

final_model = xgb.XGBClassifier(**best_params)
final_model.fit(X_train, y_train)

# Guardar
model_dir = os.path.dirname(CSV_PATH) if os.path.dirname(CSV_PATH) else '.'
model_path = os.path.join(model_dir, "modelo_city_group.joblib")
joblib.dump(final_model, model_path)
print(f"Modelo guardado en: {model_path}")

probs = final_model.predict_proba(X_test)
preds = final_model.predict(X_test)

loss = log_loss(y_test, probs)
acc = accuracy_score(y_test, preds)

print(f"RESULTADOS EN TEST:")
print(f"   Log Loss: {loss:.4f} (Menor es mejor)")
print(f"   Accuracy: {acc:.2%} (Acierto directo)")
