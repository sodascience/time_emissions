
# %%
# =============================================================================
# Section 1: Imports and Setup
# =============================================================================
import os
import pickle
from typing import Any, Dict, List, Tuple, Union, Optional

import numpy as np
import pandas as pd
import polars as pl

# Modeling and evaluation packages
import optuna
from optuna.visualization import (
    plot_optimization_history,
    plot_parallel_coordinate,
    plot_contour,
    plot_param_importances,
    plot_slice,
    plot_edf,
)
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.metrics import (mean_squared_error, mean_absolute_error,
                             r2_score, mean_absolute_percentage_error)
from sklearn.model_selection import (train_test_split, cross_val_score)
from sklearn.inspection import permutation_importance
from sklearn.preprocessing import (StandardScaler, OneHotEncoder, MinMaxScaler,
                                   QuantileTransformer)
from sklearn.compose import ColumnTransformer

# Custom modules
import config as f

def hyperparameter_tuning_boost(
    X_train: pd.DataFrame, y_train: pd.Series, name_layer: str, n_trials: int = 100, viz: bool = False,
) -> Tuple[Dict[str, Any], HistGradientBoostingRegressor]:
    """
    Tune hyperparameters for a HistGradientBoostingRegressor using optuna.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training features.
    y_train : pd.Series
        Training target.
    name_layer : str
        Name of the feature layer.
    n_trials : int, optional
        Number of optuna trials (default is 100).
    viz : bool, optional
        Whether to generate and save visualization plots (default is False).

    Returns
    -------
    tuple
        Best parameters dictionary and a fitted HistGradientBoostingRegressor model.
    """
    def objective(trial: optuna.Trial) -> float:
        learning_rate = trial.suggest_float("learning_rate", 0.01, 1)
        max_iter = trial.suggest_int("max_iter", 50, 200)
        max_leaf_nodes = trial.suggest_int("max_leaf_nodes", 2, 50)
        min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 100)
        max_depth = trial.suggest_int("max_depth", 1, 20)
        model = HistGradientBoostingRegressor(
            learning_rate=learning_rate,
            max_iter=max_iter,
            max_leaf_nodes=max_leaf_nodes,
            min_samples_leaf=min_samples_leaf,
            max_depth=max_depth,
            random_state=42,
        )
        scores = cross_val_score(model, X_train, y_train, scoring="neg_mean_squared_error")
        return np.mean(scores)
    
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    
    if viz:
        # Save visualization figures.
        for viz_func in [
            plot_optimization_history,
            plot_parallel_coordinate,
            plot_contour,
            plot_param_importances,
            plot_slice,
            plot_edf,
        ]:
            fig = viz_func(study)
            fig.write_image(f"{f.path_results}/hyperparameter_optuna/boost_{name_layer}_{viz_func.__name__}.png")
            fig.show()
    
    final_model = HistGradientBoostingRegressor(**study.best_params, random_state=42)
    final_model.fit(X_train, y_train)
    return study.best_params, final_model