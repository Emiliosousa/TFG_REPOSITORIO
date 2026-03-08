import numpy as np
import pandas as pd
import xgboost as xgb
import optuna
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, accuracy_score, brier_score_loss
from typing import Dict, Any, Tuple

class PicksloraxTrainer:
    """Trains and optimizes the pickslorax predictive model using XGBoost.
    """
    
    def __init__(self, random_state: int = 42, test_season_start: int = 2023):
        """Initializes trainer.
        
        Args:
            random_state (int): Seed for reproducibility.
            test_season_start (int): Season year where the out-of-sample test splits start.
        """
        self.random_state = random_state
        self.test_season_start = test_season_start
        self.best_params = {}
        self.final_model = None
        
    def train_test_split_temporal(self, df: pd.DataFrame, features: list) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
        """Strictly splits data avoiding temporal leakage.
        """
        train_mask = df['Season'] < self.test_season_start
        test_mask  = df['Season'] >= self.test_season_start
        
        X = df[features].astype(float)
        y = df['Target'].astype(int)
        
        X_train, y_train = X[train_mask].reset_index(drop=True), y[train_mask].reset_index(drop=True)
        X_test, y_test = X[test_mask].reset_index(drop=True), y[test_mask].reset_index(drop=True)
        seasons_train = df.loc[train_mask, 'Season'].reset_index(drop=True)
        
        return X_train, X_test, y_train, y_test, seasons_train

    def optimize_hyperparameters(self, X_train: pd.DataFrame, y_train: pd.Series, seasons_train: pd.Series, n_trials: int = 50) -> Dict[str, Any]:
        """Finds best hyperparameters with Optuna walk-forward logic.
        """
        def objective(trial):
            param = {
                'objective': 'multi:softprob',
                'num_class': 3,
                'eval_metric': 'mlogloss',
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
                'max_depth': trial.suggest_int('max_depth', 2, 5),
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'subsample': trial.suggest_float('subsample', 0.6, 0.9),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.9),
                'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 2.0),
                'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 2.0),
                'random_state': self.random_state,
                'n_jobs': -1,
                'verbosity': 0,
            }
            
            # Walk-forward nested CV to prevent temporal leakage on hyperparams
            unique_seasons = sorted(seasons_train.unique())
            losses = []
            for i in range(5, len(unique_seasons)):
                tr_seasons = unique_seasons[:i]
                val_season = unique_seasons[i]
                
                tr_mask = seasons_train.isin(tr_seasons)
                val_mask = seasons_train == val_season
                
                model = xgb.XGBClassifier(**param)
                model.fit(X_train[tr_mask], y_train[tr_mask])
                
                probs = model.predict_proba(X_train[val_mask])
                losses.append(log_loss(y_train[val_mask], probs))
                
            return np.mean(losses)
            
        study = optuna.create_study(direction='minimize')
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study.optimize(objective, n_trials=n_trials)
        
        self.best_params = study.best_params.copy()
        self.best_params.update({
            'objective': 'multi:softprob',
            'num_class': 3,
            'random_state': self.random_state,
            'verbosity': 0,
        })
        return self.best_params
        
    def train_final_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Trains final XGBoost with strictly required parameters and Isotonic Calibrated Classifier.
        """
        base_model = xgb.XGBClassifier(**self.best_params)
        
        # Using Calibration prevents overconfidence. cv=3 over full training split
        self.final_model = CalibratedClassifierCV(base_model, method='isotonic', cv=3)
        self.final_model.fit(X_train, y_train)
        
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluates final logloss, accuracy and brier score on unseen test data."""
        probs_test = self.final_model.predict_proba(X_test)
        preds_test = np.argmax(probs_test, axis=1)
        
        metrics = {
            'log_loss': log_loss(y_test, probs_test),
            'accuracy': accuracy_score(y_test, preds_test),
            'brier_score_H': brier_score_loss(y_test == 2, probs_test[:, 2])
        }
        return metrics

    def save_model(self, filepath: str = 'modelo_v3_calibrado.joblib'):
        """Saves model to disk."""
        if self.final_model:
            joblib.dump(self.final_model, filepath)
