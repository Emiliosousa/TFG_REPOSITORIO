## Sistema de detección de *value bets* en fútbol

**Título largo del TFG**: Ingeniería de características y análisis predictivo sobre eventos deportivos y apuestas  
**Grado**: Ingeniería Informática – Tecnologías Informáticas  
**Universidad**: Universidad de Sevilla  

Este repositorio contiene el código y los datos del Trabajo de Fin de Grado cuyo objetivo es responder, con rigor, a una pregunta muy concreta:

> ¿Se puede construir un sistema de *Machine Learning* que prediga partidos de LaLiga mejor que una casa de apuestas profesional (Winamax) y encuentre apuestas con valor esperado positivo?

La respuesta empírica es **no** (el ROI es negativo), pero el proyecto demuestra un **pipeline completo y honesto** de ciencia de datos:

- Recogida y limpieza de datos reales (25 años de LaLiga).
- Ingeniería de características avanzada y ratings tipo Elo/xG.
- Entrenamiento y validación temporal rigurosa de un modelo XGBoost.
- Sistema para detectar *value bets* y simular estrategias.
- Dashboard web interactivo (*LaLiga Enterprise*) para explorar predicciones e historial.

El README está escrito en español claro para que **cualquier lector**, incluso sin base técnica, entienda qué hace cada pieza.

---

## 1. Visión general (para no técnicos)

Imagina que quieres saber:

- Si las cuotas que ofrece una casa de apuestas están “bien puestas”.
- Si con datos públicos (resultados, estadísticas, valores de mercado, ratings FIFA, lesiones, etc.) puedes detectar errores en esas cuotas.

Este TFG construye un sistema que:

1. **Recoge datos históricos** de LaLiga (resultados, estadísticas, cuotas, valores de mercado, ratings FIFA, lesiones…).
2. **Transforma esos datos en números útiles** que describen la fuerza y el estado de forma de cada equipo.
3. **Entrena un modelo de *Machine Learning*** (XGBoost) para estimar la probabilidad de victoria local, empate o victoria visitante.
4. **Compara esas probabilidades con las cuotas reales de Winamax** para detectar posibles *value bets* (apuestas con valor esperado positivo).
5. **Simula una estrategia de apuestas a lo largo de 25 años** para ver si, en la práctica, ganarías o perderías dinero.
6. **Muestra todo en un dashboard web** con pestañas de:
   - Mercado en vivo (*LIVE MARKET*).
   - Análisis táctico de equipos (*TACTICAL SCOUTING*).
   - Auditoría histórica y métricas académicas (*HISTORICAL AUDIT*).

---

## 2. Flujo completo del sistema

De forma resumida, el flujo de trabajo es:

1. **Datos brutos**  
   - Descarga de resultados históricos de LaLiga (2000–2025) desde *football-data.co.uk*.  
   - Descarga/procesado de valores de mercado desde *Transfermarkt*.  
   - Ratings medios de jugadores/equipos desde *SoFIFA*.  
   - Lesiones históricas desde *Transfermarkt*.  
   - Cuotas en vivo de Winamax vía *scraping* con Puppeteer.

2. **Ingeniería de características** (`LaLiga/notebooks/01_ingenieria_de_datos.ipynb` y `LaLiga/src/feature_engineering.py`)  
   - Cálculo de Elo híbrido y ratings de ataque/defensa.  
   - Estadísticas de forma reciente (últimos partidos).  
   - Indicadores avanzados (*Field Tilt*, xG proxy, PPDA proxy, etc.).  
   - Enriquecimiento con ratings FIFA y valores de mercado.  
   - Eliminación explícita de variables post-partido para evitar *leakage*.

3. **Modelado y validación** (`LaLiga/notebooks/02_entrenamiento_avanzado.ipynb`, `LaLiga/train_model.py`)  
   - Entrenamiento de un clasificador XGBoost multiclase (1X2).  
   - Validación con **TimeSeriesSplit** (ventana expansiva en el tiempo).  
   - Cálculo y guardado de métricas por *fold* en `validation_metrics.json`.  
   - Entrenamiento final del modelo y guardado en `modelo_city_group.joblib`.

4. **Definición y búsqueda de *value bets*** (`LaLiga/notebooks/03_auditoria_y_finanzas.ipynb`)  
   - Cálculo de esperanza matemática de cada apuesta combinando probabilidad del modelo y cuota de la casa.  
   - Filtro de apuestas según reglas de confianza y margen mínimo.  
   - Simulación (*backtest*) sobre 25 años de datos.

5. **Scraping de cuotas en vivo y actualización de datos** (`LaLiga/src/scraper_winamax.js`, `LaLiga/src/process_state.py`, `LaLiga/src/update_system.py`)  
   - Puppeteer extrae el estado interno (`window.PRELOADED_STATE`) de Winamax.  
   - Un script Python procesa ese estado y genera `data/live_odds.json`.  
   - `update_system.py` descarga la última temporada, recalcula todas las características y refresca el dataset `df_final_app.csv`.

6. **Dashboard web (*LaLiga Enterprise*)** (`LaLiga/app_dashboard.py` o `app_dashboard.py` en la raíz)  
   - Interfaz Streamlit con diseño corporativo oscuro.  
   - Tres módulos principales: LIVE MARKET, TACTICAL SCOUTING, HISTORICAL AUDIT.  
   - Botón de “Actualizar Datos” integrado con el sistema de actualización.

---

## 3. Datos utilizados

Resumen de las fuentes de datos principales (todas públicas):

- **Resultados y estadísticas de partidos de LaLiga (2000–2025)**  
  - Fuente: `football-data.co.uk`  
  - Información: marcador final, goles, tiros, tiros a puerta, córners, tarjetas, faltas, cuotas históricas, etc.

- **Valores de mercado de plantillas por temporada**  
  - Fuente: *Transfermarkt*  
  - Se usa para medir el “poder económico” y la profundidad de las plantillas.

- **Ratings FIFA (calidad media de la plantilla)**  
  - Fuente: *SoFIFA*  
  - Se usa como indicador de calidad técnica agregada.

- **Lesiones históricas de jugadores**  
  - Fuente: *Transfermarkt*  
  - Se emplean para ajustar la percepción de fortaleza según ausencias relevantes.

- **Cuotas en vivo (Winamax)**  
  - Obtenidas mediante *scraping* con Puppeteer.  
  - Se actualizan de forma puntual (no es un sistema 24/7, sino una captura periódica para análisis académico).

Todos estos datos se combinan en el fichero procesado `LaLiga/df_final_app.csv`, que es el **dataset final** usado por el modelo y el dashboard.

---

## 4. Ingeniería de características (qué variables se construyen)

El corazón del TFG es la **ingeniería de características**. A partir de los datos brutos se generan más de 30 variables que intentan capturar:

- **Fortaleza global del equipo (Elo híbrido)**  
  - Adaptación del sistema Elo al fútbol.  
  - Incluye ventaja de jugar en casa (+70/+100 puntos).  
  - Se combina con valores de mercado y ratings FIFA para afinar.

- **Forma reciente (últimos N partidos)**  
  - Puntos conseguidos en los últimos 5 partidos.  
  - Diferencia de goles en la racha reciente.  
  - Días de descanso desde el último partido (*Rest Days*).

- **Estadísticas avanzadas post-partido (usadas solo para construir históricos)**  
  - *xG Proxy*: aproximación de goles esperados a partir de tiros y tiros a puerta.  
  - *Field Tilt*: porcentaje de acciones ofensivas en campo rival (tiros + córners).  
  - *PPDA Proxy*: intensidad de la presión defensiva.  
  - *PDO*: medida de sostenibilidad (relación entre goles y tiros a puerta propios y rivales).

- **Features rodantes por equipo**  
  - Medias móviles (últimos 5–10 partidos) de xG, presión, *Field Tilt*, PDO, etc.  
  - *Rest Days* capado a 30 días para evitar extremos irreales.

- **Historial cara a cara (H2H)**  
  - Puntos medios obtenidos en los últimos enfrentamientos directos entre ambos equipos.

El módulo `LaLiga/src/feature_engineering.py` se encarga de:

1. Limpiar y completar columnas faltantes.  
2. Calcular estas métricas avanzadas partido a partido.  
3. Generar las variables finales utilizadas por el modelo (`MODEL_FEATURES`).  
4. **Eliminar las columnas que podrían generar *data leakage*** (todas las que empiezan por `PostMatch_`) antes de pasar los datos al modelo.

---

## 5. Modelo predictivo y validación académica

### 5.1. Modelo utilizado

En producción se usa un **XGBoostClassifier** multiclase con configuración moderadamente conservadora:

- Profundidad máxima moderada (árboles no excesivamente profundos).  
- *Learning rate* bajo.  
- Número de árboles suficiente para capturar patrones sin sobreajustar.  
- Submuestreo de filas y columnas para robustez.

El objetivo del modelo es dar, para cada partido:

- Probabilidad de **1** (victoria local).  
- Probabilidad de **X** (empate).  
- Probabilidad de **2** (victoria visitante).

### 5.2. Validación con series temporales (*TimeSeriesSplit*)

Para evitar errores metodológicos (entrenar con el futuro para predecir el pasado), se utiliza:

- `TimeSeriesSplit` de *scikit-learn* con **5 particiones**.  
- Esquema de **ventana expansiva**:
  - En cada *fold* se entrena con temporadas antiguas y se prueba en temporadas posteriores.  
  - Se repite el proceso 5 veces, avanzando en el tiempo.

En cada *fold* se calculan métricas estándar:

- **Accuracy** (porcentaje de aciertos 1X2).  
- **Precision, Recall y F1 ponderados** (importante en problemas multiclase desbalanceados).  
- Estas métricas se guardan en `LaLiga/validation_metrics.json` y se muestran en la pestaña **HISTORICAL AUDIT** del dashboard.

### 5.3. Entrenamiento final

Tras evaluar el rendimiento temporal, se entrena un modelo final sobre todo el histórico disponible y se guarda en:

- `LaLiga/modelo_city_group.joblib`

Este artefacto incluye:

- El modelo XGBoost entrenado.  
- La lista de características utilizadas.  
- El resumen de resultados de validación temporal.

---

## 6. Definición de *value bets* y resultados del *backtest*

### 6.1. ¿De dónde salen las probabilidades del modelo?

Para cada partido histórico del dataset final (`df_final_app.csv`), se construye un vector de entrada con las variables definidas en `MODEL_FEATURES` (Elo, forma, presiones, xG proxy, H2H, ratings FIFA, valores de mercado, etc.).

En el script de entrenamiento `LaLiga/train_model.py` se hace:

- Se mapea el resultado real del partido (`FTR`) a una clase numérica:
  - `A` (gana el visitante) → 0  
  - `D` (empate) → 1  
  - `H` (gana el local) → 2
- Se entrena un `XGBClassifier` con objetivo `multi:softprob`, es decir:
  - Para cada partido, el modelo devuelve un **vector de 3 probabilidades** \([P(A), P(D), P(H)]\) que suman 1.
- En los notebooks de modelado (`02_entrenamiento_avanzado.ipynb`) se usan estas probabilidades, no solo el signo más probable.

Resumiendo:

- **Las probabilidades del modelo vienen directamente de XGBoost**, alimentado con las 20+ características construidas en la fase de ingeniería.
- Esas probabilidades se usan después para:
  - Calcular métricas (log-loss, Brier score, etc.).  
  - Compararlas con las probabilidades implícitas de las cuotas.

### 6.2. Definición de *value bet*

Una apuesta se considera con valor cuando:

> Probabilidad_modelo × Cuota_casa > 1.05

Es decir:

- Se exige una **esperanza matemática > 1.05** (al menos un 5 % por encima del punto de equilibrio) para compensar el margen típico de la casa de apuestas.

Ejemplo simplificado:

- El modelo estima que el Real Madrid ganará con probabilidad 60 %.  
- Winamax ofrece cuota 2.00 (equivale a una probabilidad implícita del 50 %).  
- Valor esperado teórico: 0.60 × 2.00 = 1.20 → *value bet*.

### 6.3. Reglas adicionales

Para evitar apuestas demasiado locas:

- Se descartan apuestas con probabilidad del modelo inferior a un cierto umbral (p. ej. 0.35).  
- Se usa un *stake* fijo (por ejemplo 2 % de un bankroll inicial) en cada apuesta.

### 6.4. Backtest (simulación histórica)

En el *backtest* sobre ~25 años de datos:

- Se simulan todas las *value bets* detectadas por el modelo.  
- Se actualiza el bankroll partido a partido usando las cuotas históricas.

El resultado agregado es un **ROI negativo** (pérdida a largo plazo). Es importante dejar claro que:

- **Refuerza la hipótesis de mercado eficiente** en apuestas pre-partido con datos públicos.  
- Demuestra la **honestidad metodológica** del TFG: no se han “forzado” resultados positivos eliminando muestras o sobreajustando parámetros.

---

## 7. Dashboard *LaLiga Enterprise* (app web)

El dashboard se encuentra en:

- `LaLiga/app_dashboard.py` (ruta original)  
- `app_dashboard.py` en la raíz (versión pensada para ejecutarse desde el directorio del repositorio).

Está desarrollado con **Streamlit** y ofrece tres módulos:

- **LIVE MARKET**  
  - Muestra partidos para los que hay cuotas recientes en `data/live_odds.json` (extraídas de Winamax).  
  - La versión actual de la app está pensada como **prototipo visual** de cómo sería el análisis en vivo:
    - El código incluye la carga del modelo y del dataset (`df_final_app.csv`), pero en la sección LIVE MARKET se usan actualmente **probabilidades de ejemplo (placeholders)** para renderizar las tarjetas.
    - Es decir: **NO se están generando todavía value bets reales en directo**, sino que se enseña la interfaz y lógica de cálculo de valor esperado.
  - La detección real de value bets se ha implementado y evaluado sobre datos históricos (backtest en los notebooks), no como sistema 24/7 conectado permanentemente al mercado.

- **TACTICAL SCOUTING**  
  - Permite elegir dos equipos y compararlos mediante gráficos de radar.  
  - Ejes incluidos: Ataque, Defensa, Posesión (proxy por tiros), Forma (puntos recientes), Intensidad (fouls/PPDA proxy).

- **HISTORICAL AUDIT**  
  - Muestra las métricas de validación temporal (*TimeSeriesSplit*).  
  - Tabla con Accuracy, Precision, Recall y F1 por *fold*.  
  - Gráfico de barras y líneas para visualizar estabilidad temporal del modelo.

---

## 8. Cómo ejecutar el proyecto

### 8.1. Requisitos previos

- **Python 3.10+** (recomendado).  
- **Node.js** (para el *scraper* de Winamax).  
- Paquetes Python típicos:
  - `pandas`, `numpy`, `scikit-learn`, `xgboost`, `joblib`, `requests`, `streamlit`, `plotly`, etc.  
- Paquete Node:
  - `puppeteer` (ya declarado en `package.json`).

> Nota: en un entorno real se incluiría un `requirements.txt`/`environment.yml` con versiones concretas.

### 8.2. Instalación de dependencias Node (scraper Winamax)

Desde la raíz del repositorio (`TFG_REPOSITORIO`):

```bash
npm install
```

Esto instalará `puppeteer` según lo definido en `package.json`.

### 8.3. Ejecutar solo el dashboard (modo “demo”)

Si quieres simplemente ver la aplicación funcionando con el modelo y dataset ya generados:

1. Asegúrate de tener instaladas las librerías Python necesarias.  
2. Desde la carpeta raíz del repositorio:

```bash
streamlit run app_dashboard.py
```

3. Se abrirá el navegador (o podrás acceder en `http://localhost:8501`).  
4. Podrás navegar por las pestañas **LIVE MARKET**, **TACTICAL SCOUTING** y **HISTORICAL AUDIT**.

### 8.4. Actualizar datos y cuotas (pipeline completo)

Cuando pulses el botón **“Actualizar Datos”** en la barra lateral del dashboard:

1. Se ejecuta `LaLiga/src/update_system.py`.  
2. Este script:
   - Descarga el CSV más reciente de LaLiga 24/25 desde `football-data.co.uk`.  
   - Fusiona con el histórico, elimina duplicados y recalcula todas las características (Elo, xG proxy, Field Tilt, etc.).  
   - Actualiza `LaLiga/df_final_app.csv`.  
   - Lanza el *scraper* Winamax (`scraper_winamax.js`) y el procesador de estado (`process_state.py`) para actualizar `LaLiga/data/live_odds.json`.

Para lanzar esta actualización manualmente (sin entrar al dashboard):

```bash
cd LaLiga
python src/update_system.py
```

### 8.5. Reentrenar el modelo

Si se desea reentrenar el modelo XGBoost (por ejemplo, tras actualizar muchos datos):

```bash
cd LaLiga
python train_model.py
```

Esto:

- Recalculará las métricas temporales y actualizará `validation_metrics.json`.  
- Entrenará un modelo final y guardará el artefacto en `modelo_city_group.joblib`.

---

## 9. Estructura principal del repositorio

Esquema simplificado (las carpetas de datos contienen más archivos CSV/JSON):

```text
TFG_REPOSITORIO/
├── app_dashboard.py            # Versión "unificada" del dashboard para ejecutar desde raíz
├── package.json                # Dependencias Node (puppeteer)
├── node_modules/               # Dependencias instaladas de Node
├── LaLiga/
│   ├── app_dashboard.py        # Dashboard original específico de LaLiga
│   ├── notebooks/
│   │   ├── 01_ingenieria_de_datos.ipynb
│   │   ├── 02_entrenamiento_avanzado.ipynb
│   │   └── 03_auditoria_y_finanzas.ipynb
│   ├── data/                   # Datos crudos y enriquecidos (CSVs, JSON, logos, etc.)
│   ├── df_final_app.csv        # Dataset final listo para el modelo/dashboard
│   ├── modelo_city_group.joblib# Modelo XGBoost entrenado
│   ├── validation_metrics.json # Resultados de TimeSeriesSplit
│   ├── src/
│   │   ├── feature_engineering.py  # Pipeline de ingeniería de características
│   │   ├── update_system.py        # Actualización de datos + scraping Winamax
│   │   ├── scraper_winamax.js      # Scraper Puppeteer (Winamax)
│   │   └── process_state.py        # Procesa window.PRELOADED_STATE → live_odds.json
│   ├── visualizations/         # Gráficos de ROI, calibración, importancia de features, etc.
│   ├── RESUMEN_TFG.md          # Resumen textual del proyecto
│   └── INFORME_FINAL_MODIFICACIONES.md # Cambios finales para elevar rigor académico
└── Premier/                    # Scripts y datos para extensión a Premier League (no núcleo del TFG)
```

---

## 10. Limitaciones y líneas futuras

Las limitaciones principales, discutidas en la memoria, incluyen:

- **Eficiencia del mercado**:  
  - Las casas de apuestas tienen acceso a información privada y modelos muy avanzados.  
  - Con solo datos públicos, superar de forma consistente su margen (5–10 %) es extremadamente difícil.

- **Cobertura de datos**:  
  - Estadísticas avanzadas incompletas en temporadas antiguas.  
  - Lesiones históricas completas solo a partir de cierto año.

- **Generalización**:  
  - El sistema está calibrado y validado para **LaLiga**.  
  - Otras ligas pueden requerir ajustes de ingeniería de características y parámetros.

Líneas futuras propuestas:

- Extender el análisis a otras ligas (Premier League, Bundesliga, Serie A…).  
- Integrar datos de *Expected Goals* (xG) detallados cuando estén disponibles.  
- Explorar modelos secuenciales (LSTM, Transformers) para capturar mejor la dinámica temporal.  
- Estudiar apuestas *in-play* (durante el partido), donde el mercado puede ser menos eficiente.

---

## 11. Aviso ético

Este proyecto tiene un **fin exclusivamente académico**:

- No pretende fomentar el juego ni las apuestas compulsivas.  
- El resultado principal es metodológico: demuestra cómo construir, validar y auditar un sistema de predicción aplicado a un mercado real.  
- Se recuerda que las apuestas conllevan riesgos económicos y personales, y que las casas de apuestas están diseñadas para tener ventaja estructural.

Para cualquier duda técnica o académica, consulta los notebooks de `LaLiga/notebooks` y los documentos `RESUMEN_TFG.md` e `INFORME_FINAL_MODIFICACIONES.md`, donde se profundiza en cada decisión.

