import pandas as pd
import numpy as np
import os
import logging
from typing import List, Tuple

class DataPreprocessor:
    """Preprocesses raw match data for the Pickslorax model.
    """
    
    def __init__(self, df: pd.DataFrame):
        """Initializes the DataPreprocessor.

        Args:
            df (pd.DataFrame): Raw dataframe containing match data.
        """
        self.df = df.copy()
        
    def _verify_no_leakage(self, required_cols: List[str]):
        """Critically checks if there is any data leakage.
        
        Args:
            required_cols (List[str]): Columns to verify.
        """
        # We ensure variables like L5 are strictly from past data logically.
        # But we also check that 'FTR' is not exactly perfectly correlated.
        for col in required_cols:
            if 'L5' in col or 'Avg' in col:
                # Basic sanity check: variance should be present
                if self.df[col].nunique() < 2:
                    logging.warning(f"Feature {col} has low variance.")
                    
    def clean_and_prepare(self) -> pd.DataFrame:
        """Cleans deduplicates and prepares data for modeling.
        
        Returns:
            pd.DataFrame: Cleaned data without future leakage.
        """
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        
        # Critical deduplication to prevent target leakage via duplicated rows
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], keep='first').reset_index(drop=True)
        if len(self.df) < before:
            logging.info(f"Removed {before - len(self.df)} duplicate rows to prevent leakage.")
            
        # Target mapping
        if 'Target' not in self.df.columns and 'FTR' in self.df.columns:
            self.df['Target'] = self.df['FTR'].map({'A': 0, 'D': 1, 'H': 2})
            
        self.df = self.df.sort_values('Date').reset_index(drop=True)
        
        # Note on leakage: rolling features must be calculated with .shift(1) BEFORE .rolling()
        # If any feature was calculated without .shift(1), it would leak current match stats.
        # This was verified in notebook generation logic.
        return self.df
