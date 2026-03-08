# Pickslorax: Predictive Modeling Engine 📈⚽
> **Author**: Emilio - TFG Project

Architectural Refactoring of "Pickslorax," an end-to-end framework integrating Big Data, Feature Engineering (L5 Rolling Proxies), XGBoost parameter tuning, and strict Financial Auditing (Walk-Forward Temporal Backtesting) for advanced value-betting operations.

---

## 🛠 Project Architecture (SOLID Principles)

The pipeline is split into self-contained objects managing specialized processing layers:

```
src/
├── data/
│   └── preprocessor.py   # Leakage-Free Data Deduplication & Standardization
├── models/
│   ├── trainer.py        # XGBoost Time-Series Calibration & Optuna Walk-Forward
│   └── evaluator.py      # Backtesting Engine & Bankroll vs Yield Diagnostics
└── visualization/
    └── reports.py        # Professional Matplotlib/Seaborn Rendering
```

- **`DataPreprocessor`** (`src.data`): Encapsulates feature safety checking, assuring categorical transformations (`Target` classes mapping) execute properly over isolated timestamps.
- **`PicksloraxTrainer`** (`src.models`): Implements `CalibratedClassifierCV` specifically preserving time-series splits (`TimeSeriesSplit` philosophy validation) with a pure log-loss optimization logic by `optuna`.
- **`FinancialEvaluator`** (`src.models.evaluator`): Implements strict financial differentiation metrics avoiding typical gambler fallacies:
   * **Model Yield (Net ROI):** `Total Net Profit / Wager Volume`
   * **Bankroll Growth:** `Net PnL / Initial Absolute Bankroll`

## ⚙️ Running the Inference Pipeline

```python
import pandas as pd
from src.data.preprocessor import DataPreprocessor
from src.models.trainer import PicksloraxTrainer
from src.models.evaluator import FinancialEvaluator

# 1. Clean Leakage Data Ensurements
df_raw = pd.read_csv('df_final_app.csv')
df_clean = DataPreprocessor(df_raw).clean_and_prepare()

# 2. Time-Series Training
trainer = PicksloraxTrainer(random_state=42)
X_test, y_test, ... = trainer.train_test_split_temporal(df_clean, features)
trainer.optimize_hyperparameters(...) 
trainer.train_final_model(...)

# 3. Bankroll Auditor
evaluator = FinancialEvaluator(...)
df_bets, df_seasons = evaluator.backtest(df_clean, features, ...)
metrics, final_bets = evaluator.generate_financial_summary(df_bets, df_seasons)

print(f"✅ Yield Neto Generado: {metrics['model_yield']:.2%}")
print(f"💰 Crecimiento del Bankroll Asignado: {metrics['bankroll_growth']:.2%}")
```

## 🔒 Auditoría de Data Leakage (Corregida & Verificada)
El modelo opera iterando sobre DataFrames cronológicos. Por ello, el cómputo de las variables `_L5` se ha verificado ejecutando invariablemente el método `shift(1)` de `pandas` antes de proceder al `rolling().mean()`. Esto inyecta un retardo forzado de ventana 1 (T-1) entre el match actual y los metadatos consultados, aislando rigurosamente eventos simultáneos y asegurando un preprocesamiento puro, sin inducción al "Hindsight Bias".
