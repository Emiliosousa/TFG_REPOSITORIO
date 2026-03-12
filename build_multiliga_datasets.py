"""
build_multiliga_datasets.py
Genera df_final_clean_v2.csv para LaLiga, Premier y Bundesliga
con las 14 features completas (igual que el modelo LaLiga V3).

Ejecutar desde el directorio raiz del repositorio:
  python build_multiliga_datasets.py
"""

import pandas as pd
import numpy as np
import json, glob, os, unicodedata, warnings
warnings.filterwarnings('ignore')

BASE      = os.path.dirname(os.path.abspath(__file__))
LALIGA_DATA = os.path.join(BASE, 'LaLiga', 'data')
ELO_K     = 30
ELO_HA    = 100

FEATURES_14 = [
    'Home_Elo_Calc', 'Away_Elo_Calc', 'Elo_Diff',
    'Home_Market_Value', 'Away_Market_Value', 'Log_Value_Diff',
    'Diff_FIFA_Ova', 'Diff_FIFA_Mid', 'Diff_FIFA_Def', 'Diff_FIFA_Att',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_H2H_L3', 'Away_H2H_L3',
]

COMMON_COLS = ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'FTR', 'Target',
               'B365H', 'B365D', 'B365A'] + FEATURES_14

# Nombres cortos (football-data.co.uk) -> nombres completos
PREMIER_NAME_MAP = {
    'Bournemouth': 'AFC Bournemouth', 'Brighton': 'Brighton & Hove Albion',
    'Cardiff': 'Cardiff City', 'Huddersfield': 'Huddersfield Town',
    'Hull': 'Hull City', 'Ipswich': 'Ipswich Town', 'Leeds': 'Leeds United',
    'Leicester': 'Leicester City', 'Luton': 'Luton Town',
    'Man City': 'Manchester City', 'Man United': 'Manchester United',
    'Newcastle': 'Newcastle United', 'Norwich': 'Norwich City',
    'QPR': 'Queens Park Rangers', 'Sheffield United': 'Sheffield Utd',
    'Stoke': 'Stoke City', 'Swansea': 'Swansea City',
    'West Brom': 'West Bromwich Albion', 'West Ham': 'West Ham United',
    'Wolves': 'Wolverhampton Wanderers',
}

# Nombres CSV Bundesliga -> nombres sofifa
BUNDESLIGA_NAME_MAP = {
    'Bayern Munich':    'FC Bayern München',
    'Bayer Leverkusen': 'Bayer 04 Leverkusen',
    'Ein Frankfurt':    'Eintracht Frankfurt',
    'TSG Hoffenheim':   'TSG 1899 Hoffenheim',
    'M\'gladbach':      'Borussia Mönchengladbach',
    'Monchengladbach':  'Borussia Mönchengladbach',
    'Greuther Furth':   'SpVgg Greuther Fürth',
    'Nurnberg':         'FC Nürnberg',
    'Fortuna Dusseldorf': 'Fortuna Düsseldorf',
}


# ─── Funciones de features ─────────────────────────────────────────────────────

def get_season(d):
    return d.year if d.month >= 8 else d.year - 1


def calc_elo(df):
    ratings = {}
    h_elo, a_elo = [], []
    for _, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        he = ratings.get(h, 1500)
        ae = ratings.get(a, 1500)
        h_elo.append(he)
        a_elo.append(ae)
        if pd.isna(row.get('FTR')):
            continue
        score = 1.0 if row['FTR'] == 'H' else (0.5 if row['FTR'] == 'D' else 0.0)
        e = 1 / (1 + 10 ** ((ae - he - ELO_HA) / 400))
        ratings[h] = he + ELO_K * (score - e)
        ratings[a] = ae + ELO_K * ((1 - score) - (1 - e))
    df = df.copy()
    df['Home_Elo_Calc'] = h_elo
    df['Away_Elo_Calc'] = a_elo
    df['Elo_Diff']      = df['Home_Elo_Calc'] - df['Away_Elo_Calc']
    return df


def calc_streak(df, window=5):
    df = df.copy()
    df['_hp'] = np.where(df['FTR']=='H', 3, np.where(df['FTR']=='D', 1, 0))
    df['_ap'] = np.where(df['FTR']=='A', 3, np.where(df['FTR']=='D', 1, 0))
    hs = df[['Date','HomeTeam','_hp']].rename(columns={'HomeTeam':'Team','_hp':'Pts'})
    as_ = df[['Date','AwayTeam','_ap']].rename(columns={'AwayTeam':'Team','_ap':'Pts'})
    all_m = pd.concat([hs, as_]).sort_values('Date')
    all_m['S'] = (all_m.groupby('Team')['Pts']
                       .transform(lambda x: x.shift(1).rolling(window, min_periods=1).sum())
                       .fillna(0))
    df = df.merge(all_m[['Date','Team','S']], left_on=['Date','HomeTeam'],
                  right_on=['Date','Team'], how='left').rename(columns={'S':'Home_Streak_L5'}).drop(columns='Team')
    df = df.merge(all_m[['Date','Team','S']], left_on=['Date','AwayTeam'],
                  right_on=['Date','Team'], how='left').rename(columns={'S':'Away_Streak_L5'}).drop(columns='Team')
    df['Home_Streak_L5'] = df['Home_Streak_L5'].fillna(0)
    df['Away_Streak_L5'] = df['Away_Streak_L5'].fillna(0)
    return df.drop(columns=['_hp','_ap'])


def calc_h2h(df, window=3):
    df = df.copy()
    hp = np.where(df['FTR']=='H', 3, np.where(df['FTR']=='D', 1, 0))
    ap = np.where(df['FTR']=='A', 3, np.where(df['FTR']=='D', 1, 0))
    df['_hp'] = hp
    df['_ap'] = ap
    h2h_h, h2h_a, hist = [], [], {}
    for _, row in df.iterrows():
        h, a = row['HomeTeam'], row['AwayTeam']
        pair  = tuple(sorted([h, a]))
        past  = hist.get(pair, [])
        if not past:
            h2h_h.append(1.5); h2h_a.append(1.5)
        else:
            rel_h = [ph if gh==h else pa for gh, ph, pa in past[-window:]]
            rel_a = [ph if gh==a else pa for gh, ph, pa in past[-window:]]
            h2h_h.append(np.mean(rel_h))
            h2h_a.append(np.mean(rel_a))
        hist.setdefault(pair, []).append((h, row['_hp'], row['_ap']))
    df['Home_H2H_L3'] = h2h_h
    df['Away_H2H_L3'] = h2h_a
    return df.drop(columns=['_hp','_ap'])


def normalize(name):
    if not isinstance(name, str): return ''
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return name.lower().strip()


def enrich_fifa(df, name_map=None, default_ova=75):
    """
    Añade Diff_FIFA_Ova/Att/Mid/Def usando sofifa_history.json global.
    Market_Value debe venir ya en el DataFrame (columnas Home/Away_Market_Value).
    """
    with open(os.path.join(LALIGA_DATA, 'sofifa_history.json'), encoding='utf-8') as f:
        sofifa = json.load(f)

    def find_fifa(team_norm, year):
        for s in [str(year), str(year-1)]:
            if s not in sofifa: continue
            for e in sofifa[s]:
                if team_norm in normalize(e['team']) or normalize(e['team']) in team_norm:
                    try:
                        return (int(e.get('ova', default_ova)),
                                int(e.get('att', default_ova)),
                                int(e.get('mid', default_ova)),
                                int(e.get('def', default_ova)))
                    except: return (default_ova,)*4
        return (default_ova,)*4

    h_ova, h_att, h_mid, h_def = [], [], [], []
    a_ova, a_att, a_mid, a_def = [], [], [], []

    for _, row in df.iterrows():
        season = int(row['Season'])
        ht = normalize(name_map.get(row['HomeTeam'], row['HomeTeam']) if name_map else row['HomeTeam'])
        at = normalize(name_map.get(row['AwayTeam'], row['AwayTeam']) if name_map else row['AwayTeam'])
        ho, ha, hm, hd = find_fifa(ht, season)
        ao, aa, am, ad = find_fifa(at, season)
        h_ova.append(ho); h_att.append(ha); h_mid.append(hm); h_def.append(hd)
        a_ova.append(ao); a_att.append(aa); a_mid.append(am); a_def.append(ad)

    df = df.copy()
    df['Diff_FIFA_Ova'] = np.array(h_ova) - np.array(a_ova)
    df['Diff_FIFA_Att'] = np.array(h_att) - np.array(a_att)
    df['Diff_FIFA_Mid'] = np.array(h_mid) - np.array(a_mid)
    df['Diff_FIFA_Def'] = np.array(h_def) - np.array(a_def)
    df['Log_Value_Diff'] = (np.log1p(df['Home_Market_Value'].clip(lower=0.01)) -
                            np.log1p(df['Away_Market_Value'].clip(lower=0.01)))
    return df


def validate_and_save(df, path, league):
    missing = [c for c in COMMON_COLS if c not in df.columns]
    if missing:
        print(f'  [ERROR] Faltan columnas en {league}: {missing}'); return

    out = df[COMMON_COLS].dropna(subset=['Target','B365H','B365D','B365A'])
    nulls = out[FEATURES_14].isnull().sum()
    if nulls.sum() > 0:
        print(f'  [WARN] Nulos en features de {league}:\n{nulls[nulls>0]}')

    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.to_csv(path, index=False)
    print(f'  -> {league}: {len(out)} partidos | {int(out["Season"].min())}-{int(out["Season"].max())} '
          f'| {os.path.basename(path)}')


# ─── LaLiga ────────────────────────────────────────────────────────────────────

def process_laliga():
    print('\n=== LaLiga ===')
    src  = os.path.join(BASE, 'LaLiga', 'data', 'df_final_clean.csv')
    dest = os.path.join(BASE, 'LaLiga', 'data', 'df_final_clean_v2.csv')
    df = pd.read_csv(src)
    df['Date'] = pd.to_datetime(df['Date'])
    # Ya tiene todas las 14 features; solo verificar y guardar
    validate_and_save(df, dest, 'LaLiga')


# ─── Premier League ────────────────────────────────────────────────────────────

def process_premier():
    print('\n=== Premier League ===')

    raw_files = sorted(glob.glob(os.path.join(BASE, 'Premier', 'data', 'E0-20*.csv')))
    dfs = []
    for f in raw_files:
        try:
            d = pd.read_csv(f, encoding='latin1',
                            usecols=['Date','HomeTeam','AwayTeam','FTR','FTHG','FTAG',
                                     'B365H','B365D','B365A'])
            dfs.append(d)
        except Exception as e:
            print(f'  Omitiendo {os.path.basename(f)}: {e}')

    df = pd.concat(dfs, ignore_index=True)
    df['Date']   = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df           = df.dropna(subset=['Date','FTR','B365H','B365D','B365A'])
    df           = df[df['FTR'].isin(['H','D','A'])]
    df['Season'] = df['Date'].apply(get_season)
    df           = df[df['Season'] >= 2010].sort_values('Date').reset_index(drop=True)
    df['Target'] = df['FTR'].map({'H':2,'D':1,'A':0})
    print(f'  Raw: {len(df)} partidos')

    # Normalizar nombres a nombres completos antes de FIFA lookup
    df['HomeTeam'] = df['HomeTeam'].replace(PREMIER_NAME_MAP)
    df['AwayTeam'] = df['AwayTeam'].replace(PREMIER_NAME_MAP)

    df = calc_elo(df)
    df = calc_streak(df)
    df = calc_h2h(df)

    # Market_Value desde el CSV procesado (ya tiene valores por partido)
    proc = pd.read_csv(os.path.join(BASE, 'Premier', 'notebooks', 'df_final_clean.csv'))
    proc['Date'] = pd.to_datetime(proc['Date'], errors='coerce')
    proc = proc[['Date','HomeTeam','AwayTeam','Home_Market_Value','Away_Market_Value']].dropna()
    df = df.merge(proc, left_on=['Date','HomeTeam','AwayTeam'],
                  right_on=['Date','HomeTeam','AwayTeam'], how='left')
    df['Home_Market_Value'] = df['Home_Market_Value'].fillna(100.0)
    df['Away_Market_Value'] = df['Away_Market_Value'].fillna(100.0)
    n_mv = (df['Home_Market_Value'] != 100).sum()
    print(f'  Market_Value: {n_mv}/{len(df)} partidos con valor real')

    print('  Calculando FIFA...')
    df = enrich_fifa(df)

    dest = os.path.join(BASE, 'Premier', 'data', 'processed', 'df_final_clean_v2.csv')
    validate_and_save(df, dest, 'Premier')


# ─── Bundesliga ────────────────────────────────────────────────────────────────

def process_bundesliga():
    print('\n=== Bundesliga ===')

    # Usar el CSV procesado: ya tiene B365, FTR, Market_Value, Season (2010-2025)
    src = os.path.join(BASE, 'BUNDESLIGA', 'data', 'processed', 'df_final_clean.csv')
    df  = pd.read_csv(src)
    df['Date']   = pd.to_datetime(df['Date'], errors='coerce')
    df           = df.dropna(subset=['Date','FTR','B365H','B365D','B365A'])
    df           = df[df['FTR'].isin(['H','D','A'])]
    df['Season'] = df['Date'].apply(get_season)
    df           = df[df['Season'] >= 2010].sort_values('Date').reset_index(drop=True)
    if 'Target' not in df.columns:
        df['Target'] = df['FTR'].map({'H':2,'D':1,'A':0})
    print(f'  Procesado: {len(df)} partidos | {int(df["Season"].min())}-{int(df["Season"].max())}')

    # Recalcular Elo_Calc desde cero (K=30, HA=100)
    df = calc_elo(df)
    # Streak ya existe en el procesado; recalcular para consistencia
    df = calc_streak(df)
    # H2H no existia
    df = calc_h2h(df)

    n_mv = (df['Home_Market_Value'].fillna(0) > 0).sum()
    print(f'  Market_Value: {n_mv}/{len(df)} partidos con valor real')

    print('  Calculando FIFA Att/Mid/Def...')
    df = enrich_fifa(df, name_map=BUNDESLIGA_NAME_MAP)

    dest = os.path.join(BASE, 'BUNDESLIGA', 'data', 'processed', 'df_final_clean_v2.csv')
    validate_and_save(df, dest, 'Bundesliga')


# ─── Resumen ───────────────────────────────────────────────────────────────────

def print_summary():
    print('\n' + '='*65)
    print('RESUMEN')
    print('='*65)
    paths = {
        'LaLiga':     os.path.join(BASE, 'LaLiga', 'data', 'df_final_clean_v2.csv'),
        'Premier':    os.path.join(BASE, 'Premier', 'data', 'processed', 'df_final_clean_v2.csv'),
        'Bundesliga': os.path.join(BASE, 'BUNDESLIGA', 'data', 'processed', 'df_final_clean_v2.csv'),
    }
    total = 0
    for league, p in paths.items():
        if not os.path.exists(p):
            print(f'  {league}: NO GENERADO'); continue
        df = pd.read_csv(p)
        n  = len(df)
        total += n
        # Comprobar cobertura FIFA (% con Diff_FIFA_Ova != 0)
        fifa_ok = (df['Diff_FIFA_Ova'] != 0).mean() * 100
        mv_ok   = (df['Log_Value_Diff'] != 0).mean() * 100
        print(f'  {league:<12} {n:5} partidos | '
              f'{int(df["Season"].min())}-{int(df["Season"].max())} | '
              f'FIFA cobertura: {fifa_ok:.0f}% | Market cobertura: {mv_ok:.0f}%')
    print(f'  {"TOTAL":<12} {total:5} partidos')
    print(f'\n  14 features: {FEATURES_14}')


if __name__ == '__main__':
    process_laliga()
    process_premier()
    process_bundesliga()
    print_summary()
