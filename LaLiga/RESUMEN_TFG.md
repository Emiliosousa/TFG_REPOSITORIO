# Resumen del TFG: Sistema de Detección de Value Bets en Fútbol

Hola! Te hago un resumen de todo el proyecto para que veas qué he montado.

---

## 1. Objetivo del TFG

La idea es construir un sistema completo de Machine Learning que:
- Prediga resultados de partidos de La Liga con más precisión que las casas de apuestas
- Identifique "value bets" (apuestas con valor esperado positivo)
- Lo despliegue en una app web funcional en tiempo real

Básicamente: ¿puede un modelo de ML batir a Winamax? (spoiler: no, pero el proceso es interesante)

---

## 2. De dónde salen los datos

He usado varias fuentes públicas:

**Datos históricos de partidos (2000-2025)**
- Fuente: football-data.co.uk
- 25 años de La Liga (9,388 partidos)
- Incluye: resultados, tiros, córners, faltas, tarjetas, cuotas históricas

**Valores de mercado de plantillas**
- Fuente: Transfermarkt
- Valor total de cada equipo por temporada
- Para saber quién tiene más presupuesto

**Ratings FIFA**
- Fuente: SoFIFA
- Rating promedio de la plantilla según FIFA
- Indicador de calidad técnica

**Lesiones históricas**
- Fuente: Transfermarkt
- Jugadores lesionados por fecha
- Para ajustar predicciones

**Cuotas en vivo**
- Fuente: Winamax (scraping con Puppeteer)
- Actualización cada 5 minutos
- Para detectar oportunidades en tiempo real

---

## 3. Cómo construyo el dataset y las variables

He creado 32 variables divididas en 5 categorías:

**Elo Rating Híbrido**
- Sistema Elo adaptado al fútbol (como en ajedrez)
- Ajustado por valor de mercado
- Ventaja de localía: +100 puntos al equipo local

**Estadísticas Avanzadas (últimos 5 partidos)**
- Shot Accuracy: Tiros a puerta / Tiros totales
- Conversion Rate: Goles / Tiros a puerta
- Corner Dominance: Córners a favor / Córners totales
- Aggression Index: Tarjetas + Faltas ponderadas
- Defense Stress: Tiros recibidos promedio
- Fatigue: Días de descanso desde el último partido

**Variables de Forma**
- Puntos en los últimos 5 partidos
- Goles anotados y recibidos
- Rendimiento en casa vs fuera

**Variables Contextuales**
- Temporada (para detectar cambios de era)
- Jornada (inicio vs final de temporada)
- Derby (Madrid, Barcelona, Sevilla)

**Interacciones**
- Diferencia de Elo
- Ratio de valor de mercado
- Diferencia de forma

Todo esto lo proceso en `01_ingenieria_de_datos.ipynb` y genero un CSV con las 32 features por partido.

---

## 4. Qué modelos he probado y cómo los valido

**Modelos probados:**
- Regresión Logística (baseline simple)
- Random Forest (ensemble clásico)
- XGBoost (el ganador)
- LightGBM (considerado para futuro)

**Por qué XGBoost:**
- Mejor rendimiento en datos tabulares
- Maneja bien valores faltantes (temporadas antiguas sin estadísticas)
- Regularización integrada (evita overfitting)
- Feature importance interpretable

**Validación: Walk-Forward (ventana deslizante)**

No hago un simple 80/20 porque eso filtraría datos del futuro. En su lugar:

```
Iteración 1: Entreno con 2000-2004 → Predigo 2004-2005
Iteración 2: Entreno con 2001-2005 → Predigo 2005-2006
...
Iteración 21: Entreno con 2020-2024 → Predigo 2024-2025
```

Esto simula la realidad: solo conoces el pasado cuando apuestas.

**Métricas:**
- Log Loss (función objetivo principal)
- Brier Score (distancia entre probabilidades y resultados)
- ROI (Return on Investment)
- Confusion Matrix

---

## 5. Modelo final y calibración

**Configuración XGBoost:**
```python
max_depth=6              # Profundidad de árboles
learning_rate=0.05       # Tasa de aprendizaje conservadora
n_estimators=200         # 200 árboles
subsample=0.8            # Muestreo para evitar overfitting
```

**Calibración con Platt Scaling:**

XGBoost tiende a dar probabilidades "overconfident" (ej: 0.95 cuando la real es 0.75). Para corregir esto, uso calibración mediante regresión logística (Platt Scaling).

Esto es crítico para apuestas: necesito probabilidades precisas, no solo predicciones correctas.

**Resultado:**
- Log Loss: 1.05 (mejor que baseline de 1.10)
- Brier Score: 0.251 (después de calibración)

---

## 6. Cómo defino y detecto value bets

**Concepto de Value Bet:**

Una apuesta tiene valor cuando:
```
Probabilidad_modelo × Cuota_bookie > 1.05
```

El umbral de 1.05 (5%) es para superar el margen del bookmaker.

**Ejemplo:**
- Mi modelo: P(Real Madrid gana) = 60%
- Cuota Winamax: 2.00 (probabilidad implícita = 50%)
- Valor esperado: 0.60 × 2.00 = 1.20 > 1.05 ✓ (Value Bet!)

**Criterios adicionales:**
- Confianza mínima: P > 0.35 (evitar apuestas muy improbables)
- Stake fijo: 2% del bankroll (gestión conservadora)

**Detección en tiempo real:**
1. `run_live_odds.js` scrapes Winamax cada 5 min
2. Guarda cuotas en `live_odds.json`
3. `app_dashboard.py` carga el modelo con este comando: streamlit run app_dashboard.py
4. Compara P_modelo vs P_implícita
5. Alerta si hay value bet

---

## 7. Backtest y resultados (ROI)

**Setup del backtest:**
- Bankroll inicial: 1,000€
- Stake por apuesta: 2% (20€)
- Período: 2000-2025 (25 años)
- Validación: Walk-Forward con 21 iteraciones

**Resultados:**
```json
{
    "total_bets": 1813,
    "bets_won": 336,
    "win_rate": 18.5%,
    "final_bankroll": -2817.80€,
    "roi": -21.06%
}
```

**Interpretación:**

El ROI negativo NO es un fracaso. Es la confirmación de la **Hipótesis del Mercado Eficiente**: los bookmakers profesionales tienen acceso a datos privados (lesiones de última hora, alineaciones) y modelos muy sofisticados. Superar su margen (5-10%) con solo datos públicos es casi imposible.

**Lo que sí demuestra el proyecto:**
- Pipeline completo de ML (datos → modelo → despliegue)
- Validación rigurosa (Walk-Forward)
- Honestidad científica (no manipulé datos para forzar ROI positivo)

---

## 8. Qué hace el dashboard (app_dashboard.py)

Es una app web con Streamlit que tiene 2 módulos:

**LIVE SCOUTING (Predicciones en tiempo real)**
- Muestra partidos del día con cuotas de Winamax
- Calcula probabilidades con el modelo
- Detecta value bets automáticamente
- Overlay con estadísticas avanzadas (Elo, Form, xG)

**HISTORICAL AUDIT (Backtest)**
- Visualiza resultados históricos
- Curva de equity (evolución del bankroll)
- Feature importance
- Gráfico de calibración

**Cómo ejecutarlo:**
```bash
# 1. Scraper de cuotas (cada 5 min)
node run_live_odds.js

# 2. Dashboard
streamlit run app_dashboard.py
```

---

## 9. Documentación adicional creada

He creado varios documentos para el TFG:

**METODOLOGIA_TFG.md**
- Metodología completa (9 secciones)
- Desde el problema hasta el despliegue
- Tono académico formal

**JUSTIFICACION_DECISIONES.md**
- Por qué XGBoost y no Redes Neuronales
- Por qué Walk-Forward y no K-Fold
- Por qué umbral del 5%
- Incluye referencias académicas

**VISION_CRITICA.md**
- Limitaciones del modelo
- Análisis de varianza del ROI
- Riesgos de overfitting
- Consideraciones éticas

**Visualizaciones (6 gráficos profesionales)**
- ROI por temporada
- Curva de equity
- Matriz de confusión
- Feature importance
- Gráfico de calibración
- Log Loss por temporada

Todos en `./visualizations/` con alta resolución (300 DPI).

---

## 10. Limitaciones y líneas futuras

**Limitaciones actuales:**

**Eficiencia del mercado**
- Los bookmakers tienen ventaja informativa (datos privados)
- El margen del 5-10% es difícil de superar con datos públicos

**Datos incompletos**
- Temporadas 2000-2005 sin estadísticas avanzadas
- Lesiones históricas solo desde 2010

**Generalización limitada**
- Solo validado en La Liga
- Otras ligas tienen dinámicas diferentes

**Concept drift**
- El fútbol evoluciona (tácticas, reglas)
- Requiere re-entrenamiento frecuente

---

**Líneas futuras (lo que me comentaste):**

**Otras ligas**
- Premier League, Bundesliga, Serie A
- Validar si las features tienen el mismo poder predictivo
- Ajustar umbrales según margen del bookmaker

**Pinnacle (bookmaker con menor margen)**
- Pinnacle tiene margen del 2-3% (vs 5-10% de Winamax)
- Más difícil de batir, pero más "justo"
- Requiere API oficial (no scraping)

**Redes Neuronales**
- LSTM para capturar dependencias temporales
- Transformer para atención en secuencias de partidos
- Requiere más datos (>50k partidos)

**Live Betting**
- Predicciones durante el partido
- Mayor ineficiencia (cuotas se ajustan más lento)
- Requiere modelos en tiempo real (<1s latencia)

**Expected Goals (xG)**
- Integrar modelos de xG propios
- Requiere datos de posiciones de tiro (StatsBomb/Opta)

**Ensemble Methods**
- Combinar XGBoost + LightGBM + NN
- Potencial mejora del 3-5% en Log Loss

**Sentiment Analysis**
- Análisis de noticias y redes sociales pre-partido
- Capturar factores no cuantificables (moral, presión)

---

## Estructura final del proyecto

```
01_ingenieria_de_datos.ipynb      → Carga y procesa datos
02_entrenamiento_avanzado.ipynb   → Entrena modelo XGBoost
03_auditoria_y_finanzas.ipynb     → Backtest y análisis ROI
app_dashboard.py                   → Dashboard Streamlit
run_live_odds.js                   → Scraper de cuotas

data/                              → CSVs históricos (2000-2025)
visualizations/                    → 6 gráficos académicos
RESUMEN_TFG.md                     → Este documento
```

---

## Conclusión

He montado un pipeline completo de ML en producción:
- Datos reales de 25 años
- 32 features con ingeniería avanzada
- Modelo XGBoost calibrado
- Validación rigurosa (Walk-Forward)
- Dashboard funcional en tiempo real

El ROI negativo es un hallazgo científico válido: confirma que los mercados de apuestas pre-partido están bien valorados. El valor real del TFG está en el rigor metodológico y la implementación completa del sistema.

Cualquier duda me dices!
