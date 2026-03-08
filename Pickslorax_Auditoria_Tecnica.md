# Auditoría de Ingeniería y Refactorización: "Pickslorax" 📈

## 1. Detección de Data Leakage (Auditoría Técnica del Preprocesamiento)

Durante la auditoría del ciclo de procesamiento implementado para generar las variables predictoras que consume el modelo final en `02_Modelado_Avanzado_v3.ipynb`, se realizó una revisión intensiva de las "medias móviles" (como `L5`, `xG_Avg_L5`, etc.) para detectar indicios de "Data Leakage" (filtración temporal).

**Conclusión del Riesgo**:
Tras revisar el código base que engendra estos CSV (como `build_premier_features.py` y `feature_engineering.py`), **NO se encontró Data Leakage en las variables móviles L5 y xG**.
La metodología actual emplea explícitamente el operador de decalaje (`shift(1)`) _previo_ a la interpolación del intervalo móvil (`rolling()`).

```python
xG_Avg_L5_Seguro = grouped['xG'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
```
Esta función desplaza la métrica de un partido entero *antes* de promediar los últimos cinco, garantizando que el `Match M` utilice el promedio de los estadísticos del `[Match M-5 ... Match M-1]`. Por tanto, el resultado del propio partido `M` jamás corrompe las dinámicas del modelo predictivo previo al pitido incial.

## 2. Refactorización para Producción (Principios SOLID)

El sistema de modelado se extrajo de `02_Modelado_Avanzado_v3.ipynb` y se estructuró de manera orientada a objetos (POO) usando un entorno modular (SRP - *Single Responsibility Principle*) para facilitar su escalabilidad:
- **`src/data/preprocessor.py`**: Aísla la capa de limpieza y comprobación de integridad (*Data Validation*). Gestiona el mapeo de labels.
- **`src/models/trainer.py`**: Centraliza la capa de optimización de hiperparámetros (Optuna), Walk-Forward Time-Series Splitter, y su Calibración Isotónica final, encapsulado en la clase `PicksloraxTrainer`.
- **`src/models/evaluator.py`**: Realiza los *Backtesting* paralelos iterativos del Bankroll de forma totalmente independiente del entrenamiento.
- **`src/visualization/reports.py`**: Separa la capa lógica de la renderización del UI/Dashboard con Matplotlib.

## 3. Auditoría Financiera: Yield Neto vs Crecimiento de Capital

Es imperativo diferenciar en la sección de finanzas del Trabajo de Fin de Grado las matemáticas que conforman el **Yield** vs **Bankroll Growth** (frecuentemente mal reportados de manera sinónima).

*   **Yield del Modelo (ROI por euro apostado):** Es la eficiencia intrínseca del modelo Predictivo / Generador de Odds. Mide la rentabilidad obtenida por unidad invertida.
    *   **Fórmula:** `Yield = PnL_Total / (Total_Apuestas * Stake_Plano)`
    *   Si realizamos 100 apuestas de 10€, hemos arriesgado "1,000€ facturados". Si generamos un net-profit de 50€, el Yield es `50/1000 = 5%`.

*   **Crecimiento del Bankroll (ROI sobre Capital):** Es el crecimiento porcentual absoluto del capital general (los fondos totales del inversor).
    *   **Fórmula:** `Capital_Growth = PnL_Total / Bankroll_Inicial`
    *   Para un inversor que comienza con 1,000€, generar ese mismo profit de 50€ representará un Crecimiento Neto del Bankroll de `5%`.
    *   *Nota Diferencial:* En estrategias de Kelly Staking (Stake Variable), podemos generar un **Yield bajo (por ejemplo 1%)**, pero si hay mucha rotación de capital, el **Crecimiento del Bankroll puede exceder el 10% anual**.

Hemos integrado el archivo de lógica en `src/models/evaluator.py` para imprimir y auditar ambas métricas de forma diferenciada: reportando estrictamente la rentabilidad matemática separada del crecimiento del portfolio.
