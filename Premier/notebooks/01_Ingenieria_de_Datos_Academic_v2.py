#!/usr/bin/env python
# coding: utf-8

# # 01. Ingeniería de Datos Avanzada (Enfoque Académico)
#     
# ## 1. Introducción y Objetivo
# Este cuaderno constituye el primer pilar del TFG. Su objetivo es transformar datos crudos de partidos de fútbol en un **dataset estructurado de alto valor predictivo**.
# 
# A diferencia de un enfoque tradicional que solo usa goles y puntos, aquí implementamos una **ingeniería de características (Feature Engineering)** inspirada en la analítica deportiva moderna (City Football Group, Opta).
# 
# ### Metodología:
# 1.  **Recolección de Datos**: Unificación de histórico (2010-2024) y datos en tiempo real (temporada actual).
# 2.  **Normalización**: Estandarización de nombres de equipos entre distintas fuentes (Betting, Transfermarkt, FIFA).
# 3.  **Métricas Avanzadas (Proxies)**: Cálculo de métricas estimadas cuando no hay tracking data (ej: Presión, Dominio).
# 4.  **Sistemas de Rating Dinámico**: Implementación vectorial de Elo, Glicko-2 y Dixon-Coles.
# 

# In[1]:


import pandas as pd
import numpy as np
import os
import json
import requests
from datetime import datetime

# Configuración de visualización
pd.set_option('display.max_columns', None)
import warnings
warnings.filterwarnings('ignore')

print("✅ Librerías cargadas correctamente.")


# ## 2. Ingesta de Datos (Data Ingestion)
#     
# Cargamos los datos históricos desde archivos locales y descargamos la temporada actual directamente desde la fuente oficial (Football-Data.co.uk) para asegurar que el modelo siempre tenga la información más reciente.
# 

# In[2]:


DATA_DIR = '../data' # Ruta relativa asumida
CURRENT_SEASON_URL = 'https://www.football-data.co.uk/mmz4281/2425/E0.csv'

def load_and_update_data():
    dfs = []

    # 1. Cargar Histórico (2010 - 2024)
    # Iteramos por los años para cargar cada CSV de temporada
    # Ajustamos el rango según disponibilidad real
    for year in range(10, 30): 
        season_str = f"{year:02d}{(year+1)%100:02d}"
        filename = f"E0_{season_str}.csv"
        path = os.path.join(DATA_DIR, filename)

        if os.path.exists(path):
            try:
                # 'latin1' es necesario para caracteres especiales en nombres españoles
                df_temp = pd.read_csv(path, encoding='latin1', on_bad_lines='skip')
                df_temp['Season'] = 2000 + year
                dfs.append(df_temp)
            except Exception as e:
                print(f"⚠️ Error cargando {filename}: {e}")

    # 2. Descargar Temporada Actual (Live Data)
    print(f"🔄 Descargando datos en vivo: {CURRENT_SEASON_URL}...")
    try:
        r = requests.get(CURRENT_SEASON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            from io import StringIO
            df_live = pd.read_csv(StringIO(r.text), encoding='latin1')
            df_live['Season'] = 2024 # Temporada actual, ajustar fecha
            if 'Date' in df_live.columns:
                 dfs.append(df_live)
                 print("✅ Datos en vivo integrados.")
        else:
            print(f"⚠️ No se pudo descargar datos en vivo (Status {r.status_code})")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

    # 3. Concatenación
    if not dfs: # Safety check
        return pd.DataFrame()

    df_main = pd.concat(dfs, ignore_index=True)

    # 4. Limpieza de Fechas
    # Convertimos la columna 'Date' a datetime. Es crítico usar dayfirst=True para formato europeo.
    df_main['Date'] = pd.to_datetime(df_main['Date'], dayfirst=True, errors='coerce')
    df_main = df_main.dropna(subset=['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG'])
    df_main = df_main.sort_values('Date').reset_index(drop=True)

    return df_main

df_raw = load_and_update_data()
if not df_raw.empty:
    print(f"📊 Dataset Total: {len(df_raw)} partidos ({df_raw['Date'].min().year} - {df_raw['Date'].max().year})")
    display(df_raw.tail(3))
else:
    print("❌ No se cargaron datos. Verifica la ruta '../data'")


# ## 3. Normalización de Entidades (Entity Resolution)
#     
# Uno de los mayores retos en analítica de fútbol es que cada proveedor de datos nombra a los equipos de forma diferente (ej: "Ath Bilbao", "Athletic Club", "Athletic Bilbao").
#     
# Para solucionar esto, implementamos un **diccionario de mapeo canónico** que estandariza todos los nombres a una única versión oficial. Esto es crucial para poder cruzar los datos con otras fuentes como Transfermarkt o FIFA.
# 

# In[3]:


# Diccionario de Mapeo Maestro
TEAM_MAPPING = {
    'Man United': 'Manchester United', 'Man City': 'Manchester City',
    'Spurs': 'Tottenham', 'Newcastle': 'Newcastle United',
    'Leicester': 'Leicester City', 'Norwich': 'Norwich City',
    'Leeds': 'Leeds United', 'Sheffield United': 'Sheffield Utd',
    'West Ham': 'West Ham United', 'Wolves': 'Wolverhampton',
    'Brighton': 'Brighton', 'Huddersfield': 'Huddersfield',
    'Cardiff': 'Cardiff City', 'Swansea': 'Swansea City',
    'Stoke': 'Stoke City', 'Hull': 'Hull City',
    'QPR': 'QPR', 'West Brom': 'West Brom',
    'Bournemouth': 'Bournemouth', "Nott'm Forest": 'Nott. Forest',
    'Luton': 'Luton', 'Ipswich': 'Ipswich',
}

def standardize_names(df):
    if df.empty: return df
    df['HomeTeam'] = df['HomeTeam'].map(TEAM_MAPPING).fillna(df['HomeTeam'])
    df['AwayTeam'] = df['AwayTeam'].map(TEAM_MAPPING).fillna(df['AwayTeam'])
    return df

df_normalized = standardize_names(df_raw.copy())
print("✅ Nombres de equipos normalizados.")


# ## 4. Ingeniería de Características: "The City Engine"
#     
# Aquí creamos variables sintéticas que aportan contexto táctico al modelo.
#     
# ### 4.1. xG Proxy (Goles Esperados Estimados)
# Como no disponemos de mapas de tiros (shot maps) detallados, construimos un "proxy" o estimador de xG basado en la cantidad de tiros y tiros a puerta.
# *   **Hipótesis**: Un tiro a puerta tiene mucha más probabilidad de gol (~29%) que un tiro fuera (~9%).
# *   **Fórmula**: `xG = (Tiros_Total * 0.09) + (Tiros_Puerta * 0.29)`
# 
# ### 4.2. Proxy de Presión (Intensity)
# Estimamos la intensidad defensiva de un equipo calculando cuántas faltas y tarjetas genera en relación a la posesión estimada del rival.
# 

# In[4]:


def calculate_advanced_metrics(df):
    if df.empty: return df
    df = df.copy()

    # Fill Nans safely
    for col in ['HS', 'HST', 'AS', 'AST', 'HF', 'HY', 'HR', 'AF', 'AY', 'AR', 'HC', 'AC']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 1. xG Proxy
    # Coeficientes derivados de análisis de regresión histórica
    if 'HS' in df.columns and 'HST' in df.columns:
        df['Home_xG_Proxy'] = (df['HS'] * 0.09) + (df['HST'] * 0.29)
        df['Away_xG_Proxy'] = (df['AS'] * 0.09) + (df['AST'] * 0.29)
    else:
        df['Home_xG_Proxy'] = 0
        df['Away_xG_Proxy'] = 0

    # 2. Estimación de Posesión (Simplificada)
    # Asumimos 50/50 si no hay dato, pero se podría refinar con cuotas de apuestas
    df['Home_Possession_Est'] = 0.50
    df['Away_Possession_Est'] = 0.50

    # 3. Presión (Faltas + Tarjetas / Posesión Rival)
    # Indica qué tan agresivo es el equipo para recuperar el balón
    if 'HF' in df.columns:
        df['Home_Pressure'] = (df['HF'] + df['HY'] + df['HR']) / np.maximum(df['Away_Possession_Est'], 0.1)
        df['Away_Pressure'] = (df['AF'] + df['AY'] + df['AR']) / np.maximum(df['Home_Possession_Est'], 0.1)
    else:
        df['Home_Pressure'] = 0
        df['Away_Pressure'] = 0

    # 4. Dominancia Territorial (Corner Share) — PostMatch metric
    # Los corners ocurren durante el partido → se marca como PostMatch para
    # que luego se convierta en rolling average y NO haya data leakage.
    if 'HC' in df.columns:
        total_corners = df['HC'] + df['AC']
        df['PostMatch_Home_Dominance'] = np.where(total_corners > 0, df['HC'] / total_corners, 0.5)
        df['PostMatch_Away_Dominance'] = np.where(total_corners > 0, df['AC'] / total_corners, 0.5)
    else:
        df['PostMatch_Home_Dominance'] = 0.5
        df['PostMatch_Away_Dominance'] = 0.5

    return df

df_advanced = calculate_advanced_metrics(df_normalized)
if not df_advanced.empty:
    display(df_advanced[['Date', 'HomeTeam', 'Home_xG_Proxy', 'Home_Pressure']].tail())


# ## 5. Ventanas Temporales (Rolling Features)
#     
# El fútbol es un deporte de **rachas**. El rendimiento de un equipo hace 3 años es irrelevante para el partido de hoy. Lo que importa es la **forma reciente**.
#     
# Calculamos promedios móviles de los últimos 5 partidos (`L5`) para cada métrica clave:
# *   `xG_Avg_L5`: Calidad ofensiva reciente.
# *   `Streak_L5`: Puntos obtenidos en los últimos 5 partidos (Forma).
# *   `Pressure_Avg_L5`: Intensidad defensiva reciente.
# 

# In[5]:


def calculate_rolling_features(df, window=5):
    if df.empty: return df

    # 1. Preparar Puntos
    df['Home_Pts'] = np.where(df['FTR'] == 'H', 3, np.where(df['FTR'] == 'D', 1, 0))
    df['Away_Pts'] = np.where(df['FTR'] == 'A', 3, np.where(df['FTR'] == 'D', 1, 0))

    cols_needed = ['Date', 'HomeTeam', 'AwayTeam', 'Home_xG_Proxy', 'Away_xG_Proxy', 
                   'Home_Pts', 'Away_Pts', 'Home_Pressure', 'Away_Pressure',
                   'PostMatch_Home_Dominance', 'PostMatch_Away_Dominance']

    # Vista desde el Local
    h_side = df[cols_needed].rename(columns={
        'HomeTeam': 'Team', 'Home_xG_Proxy': 'xG', 'Home_Pts': 'Pts',
        'Home_Pressure': 'Press', 'PostMatch_Home_Dominance': 'Dom'
    })[['Date', 'Team', 'xG', 'Pts', 'Press', 'Dom']]

    # Vista desde el Visitante
    a_side = df[cols_needed].rename(columns={
        'AwayTeam': 'Team', 'Away_xG_Proxy': 'xG', 'Away_Pts': 'Pts',
        'Away_Pressure': 'Press', 'PostMatch_Away_Dominance': 'Dom'
    })[['Date', 'Team', 'xG', 'Pts', 'Press', 'Dom']]

    # Concatenar y Ordenar
    all_matches = pd.concat([h_side, a_side]).sort_values('Date')

    # Calcular Rolling con GroupBy
    # shift(1) es VITAL para evitar Data Leakage (no usar el dato del propio partido para predecirlo)
    grouped = all_matches.groupby('Team')

    all_matches['xG_Avg_L5'] = grouped['xG'].transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    all_matches['Streak_L5'] = grouped['Pts'].transform(lambda x: x.shift(1).rolling(window, min_periods=1).sum())
    all_matches['Pressure_Avg_L5'] = grouped['Press'].transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
    # Dominancia territorial (rolling de PostMatch corners share, con shift(1) para evitar leakage)
    all_matches['Dominance_Avg_L5'] = grouped['Dom'].transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean()).fillna(0.5)

    # Columnas calculadas para el merge
    merge_cols = ['Date', 'Team', 'xG_Avg_L5', 'Streak_L5', 'Pressure_Avg_L5', 'Dominance_Avg_L5']

    # Unir de nuevo al dataframe original
    # Join para Local
    df = df.merge(all_matches[merge_cols], 
                  left_on=['Date', 'HomeTeam'], right_on=['Date', 'Team'], how='left')
    df = df.rename(columns={
        'xG_Avg_L5': 'Home_xG_Avg_L5', 'Streak_L5': 'Home_Streak_L5',
        'Pressure_Avg_L5': 'Home_Pressure_Avg_L5', 'Dominance_Avg_L5': 'Home_Dominance_Avg_L5'
    })
    df = df.drop(columns=['Team'])

    # Join para Visitante
    df = df.merge(all_matches[merge_cols], 
                  left_on=['Date', 'AwayTeam'], right_on=['Date', 'Team'], how='left')
    df = df.rename(columns={
        'xG_Avg_L5': 'Away_xG_Avg_L5', 'Streak_L5': 'Away_Streak_L5',
        'Pressure_Avg_L5': 'Away_Pressure_Avg_L5', 'Dominance_Avg_L5': 'Away_Dominance_Avg_L5'
    })
    df = df.drop(columns=['Team'])

    return df

df_rolling = calculate_rolling_features(df_advanced)
print("\u2705 Rolling Features calculadas.")


# ## 6. Sistema Elo Rating
#     
# Originalmente diseñado para ajedrez, el sistema Elo es el estándar de oro para medir la fuerza relativa de dos competidores en un juego de suma cero.
#     
# ### Fórmula de Actualización:
# $$ R'_{A} = R_{A} + K (S_{A} - E_{A}) $$
# 
# Donde:
# *   $R_{A}$: Rating actual.
# *   $K$: Factor de volatilidad (K=20). Determina cuánto cambia el rating tras un partido.
# *   $S_{A}$: Resultado real (1=Ganar, 0.5=Empate, 0=Perder).
# *   $E_{A}$: Probabilidad esperada de ganar, basada en la diferencia de Elo con el rival.
# 
# Calculamos el Elo iterativamente partido a partido, actualizando los valores históricos.
# 

# In[6]:


def calculate_elo(df, k_factor=20):
    if df.empty: return df
    # Diccionario para guardar el estado del Elo actual de cada equipo
    # Inicializamos a 1500 (promedio estándar)
    elo_ratings = {team: 1500 for team in set(df['HomeTeam']).union(set(df['AwayTeam']))}

    home_elos = []
    away_elos = []

    for idx, row in df.iterrows():
        h = row['HomeTeam']
        a = row['AwayTeam']
        res = row['FTR']

        # Recuperar Elo PREVIO al partido
        elo_h = elo_ratings.get(h, 1500)
        elo_a = elo_ratings.get(a, 1500)

        home_elos.append(elo_h)
        away_elos.append(elo_a)

        # Calcular Probabilidad Esperada (Incluyendo ventaja de campo +70 pts)
        dr = elo_a - (elo_h + 70)
        e_prob_h = 1 / (1 + 10 ** (dr / 400))

        # Resultado Real
        if res == 'H': score_h = 1
        elif res == 'D': score_h = 0.5
        else: score_h = 0

        # Actualizar Diccionario
        new_elo_h = elo_h + k_factor * (score_h - e_prob_h)
        new_elo_a = elo_a + k_factor * ((1-score_h) - (1-e_prob_h))

        elo_ratings[h] = new_elo_h
        elo_ratings[a] = new_elo_a

    df['Home_Elo'] = home_elos
    df['Away_Elo'] = away_elos
    return df

df_final = calculate_elo(df_rolling)
print("✅ Elo Ratings calculados.")


# ## 7. Diccionario de Variables y Exportación
#     
# Antes de exportar, es fundamental entender qué significa cada columna y por qué algunas pueden tener valores nulos (NaN) en las primeras filas.
#     
# ### 7.1. Diccionario de Datos (Data Dictionary)
# | Variable | Descripción | Importancia |
# |----------|-------------|-------------|
# | **Date, Season** | Fecha y temporada del partido. | Contexto temporal. |
# | **HomeTeam, AwayTeam** | Nombres normalizados de los clubes. | Identificación. |
# | **FTR** | Full Time Result (H=Home, D=Draw, A=Away). | **Variable Objetivo (Target)** del modelo. |
# | **Home_Elo, Away_Elo** | Rating de fuerza del equipo. Empieza en 1500. Se actualiza tras cada partido. | **Muy Alta**. Resume la fuerza histórica. |
# | **Home_xG_Proxy** | Goles Esperados estimados según tiros y tiros a puerta. | Alta. Mide calidad ofensiva inmediata. |
# | **Home_Pressure** | Intensidad defensiva (Faltas/Tarjetas por posesión rival). | Media. Contexto táctico. |
# | **Home_Dominance** | Porcentaje de corners a favor respecto al total del partido. | Media. Indica quién llevó la iniciativa. |
# | **xG_Avg_L5** | Promedio de xG Proxy en los últimos 5 partidos. | **Alta**. Mide la forma reciente ofensiva. |
# | **Streak_L5** | Puntos sumados en los últimos 5 partidos (Forma). | Alta. Mide la racha de resultados. |
# | **Pressure_Avg_L5** | Intensidad promedio reciente. | Baja. |
# 
# ### 7.2. Tratamiento de NaNs (Cold Start Problem)
# Es normal observar valores `NaN` (Not a Number) en las columnas terminadas en `_L5` (Rolling Features) al principio de cada temporada o en la historia de un equipo. 
# 
# Esto se debe al "período de calentamiento" (Warm-up Period):
# > "Para calcular el promedio de los últimos 5 partidos, necesitamos que el equipo haya jugado al menos 1 partido antes. Si es el primer partido de la historia en el dataset, no hay datos previos, por lo tanto = NaN."
# 
# **Estrategia**:
# *   Rellenamos estos huecos con 0 para que el modelo pueda entrenar sin errores.
# *   El set de datos final estará limpio y listo.
# 

# In[7]:


# --- [INJECTED] INTEGRACIÓN DE DATOS EXTERNOS (FIFA & TRANSFERMARKT) ---
import json
import os

# Rutas a los datos (Relative to notebooks/)
DATA_DIR = '../data'
SOFIFA_PATH = os.path.join(DATA_DIR, 'sofifa_history.json')
TM_PATH = os.path.join(DATA_DIR, 'transfermarkt_history.json')

def load_external_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    print(f"⚠️ Warning: Could not find {path}")
    return {}

fifa_data = load_external_json(SOFIFA_PATH)
tm_data = load_external_json(TM_PATH)

def parse_tm_value(val_str):
    try:
        if isinstance(val_str, (int, float)): return float(val_str)
        # Format: €100.00m or €1.00bn
        clean = val_str.replace('€', '').strip()
        if 'bn' in clean:
            return float(clean.replace('bn', '')) * 1000
        elif 'm' in clean:
            return float(clean.replace('m', ''))
        elif 'Th' in clean: # Thousands
            return float(clean.replace('Th', '')) / 1000
        return float(clean)
    except:
        return 10.0 # Default value

def fuzzy_match(team_name, entry_name):
    # Normalize for comparison
    t1 = team_name.lower().replace('cf', '').replace('fc', '').replace('de', '').strip()
    t2 = entry_name.lower().replace('cf', '').replace('fc', '').replace('de', '').strip()
    return t1 in t2 or t2 in t1

def get_external_metric(team, season, data, metric_type='fifa'):
    # Adjust season for FIFA (FIFA 23 reflects Season 22/23 usually, but sometimes next year)
    # Heuristic: Try exact season, then season+1

    # Function to search in specific season key
    def search_in_season(s_key):
        if s_key not in data: return None

        # 1. Exact Match
        for entry in data[s_key]:
            if entry.get('team') == team:
                return entry

        # 2. Fuzzy/Mapped Match
        for entry in data[s_key]:
            ename = entry.get('team', '')
            # Known Mappings
            if team == 'Atletico Madrid' and 'Atlético' in ename: return entry
            if team == 'Athletic Club' and 'Bilbao' in ename: return entry
            if team == 'Real Betis' and 'Betis' in ename: return entry
            if team == 'RCD Espanyol' and 'Espanyol' in ename: return entry
            if team == 'Sporting Gijon' and 'Sporting' in ename: return entry
            if team == 'Alaves' and 'Alavés' in ename: return entry

            # Generic Fuzzy
            if fuzzy_match(team, ename): return entry

        return None

    # Try Current Season
    res = search_in_season(str(season))
    # If not found, try Season + 1 (FIFA naming convention sometimes is ahead)
    if not res: res = search_in_season(str(season + 1))

    if res:
        if metric_type == 'fifa':
            return int(res.get('ova', 75))
        elif metric_type == 'tm':
            return parse_tm_value(res.get('value', '10m'))

    # Defaults
    return 75 if metric_type == 'fifa' else 10.0

print("⏳ Inyectando datos de FIFA y Transfermarkt...")
h_fifa, a_fifa = [], []
h_tm, a_tm = [], []

for idx, row in df_final.iterrows():
    s = row['Season']
    h = row['HomeTeam']
    a = row['AwayTeam']

    h_fifa.append(get_external_metric(h, s, fifa_data, 'fifa'))
    a_fifa.append(get_external_metric(a, s, fifa_data, 'fifa'))

    h_tm.append(get_external_metric(h, s, tm_data, 'tm'))
    a_tm.append(get_external_metric(a, s, tm_data, 'tm'))

df_final['Home_FIFA_Ova'] = h_fifa
df_final['Away_FIFA_Ova'] = a_fifa
df_final['Home_Market_Value'] = h_tm
df_final['Away_Market_Value'] = a_tm

print(f"✅ Integración completada. (Ej: Real Madrid 2024 -> FIFA: {h_fifa[-1]}, TM: {h_tm[-1]})")


# In[8]:


# Seleccionar solo las columnas necesarias para el modelo
final_cols = [
    'Date', 'Season', 'HomeTeam', 'AwayTeam', 'FTR', 
    'Home_Elo', 'Away_Elo',
    'Home_xG_Proxy', 'Away_xG_Proxy',
    'Home_xG_Avg_L5', 'Away_xG_Avg_L5',
    'Home_Streak_L5', 'Away_Streak_L5',
    'Home_Pressure_Avg_L5', 'Away_Pressure_Avg_L5',
    'Home_Dominance_Avg_L5', 'Away_Dominance_Avg_L5',
    'Home_FIFA_Ova', 'Away_FIFA_Ova',
    'Home_Market_Value', 'Away_Market_Value',
    'B365H', 'B365D', 'B365A'
]

# Verificar NaNs antes de limpiar
nan_counts = df_final[final_cols].isna().sum()
print("⚠️ Valores nulos detectados (esperados por Rolling Windows):")
print(nan_counts[nan_counts > 0])

# Rellenar NaNs residuales con 0 (primeros partidos sin historial)
# Esto es esencial para que el modelo no falle.
df_export = df_final[final_cols].fillna(0)

# Guardar en ruta relativa (subir un nivel desde 'notebooks/')
import os
output_dir = os.path.abspath(os.path.join(os.getcwd(), '..'))
# Si estamos corriendo el notebook, '..' suele ser TFG_REPOSITORIO/Premier
# Aseguramos que la ruta sea correcta.
OUTPUT_FILE = 'df_final_app.csv'
OUTPUT_PATH = '../' + OUTPUT_FILE

try:
    df_export.to_csv(OUTPUT_PATH, index=False)
    print(f"\n💾 Dataset guardado exitosamente en: {OUTPUT_PATH}")
    print(f"   (Ruta absoluta: {os.path.abspath(OUTPUT_PATH)})")
    print(f"Dimensiones: {df_export.shape}")
except Exception as e:
    print(f"❌ Error guardando el archivo: {e}")
    # Fallback to current dir
    df_export.to_csv(OUTPUT_FILE, index=False)
    print(f"⚠️ Guardado en el directorio actual: {OUTPUT_FILE}")

df_export.head(10)

