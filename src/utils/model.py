import polars as pl
import numpy as np
from dataclasses import dataclass, field
from typing import Callable

import optuna
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler, MinMaxScaler, RobustScaler
from sklearn.multioutput import MultiOutputRegressor

from .helpers import Named, _label


@dataclass(eq = False)
class Model(Named):
    """A recipe for a pipeline: preprocessor, estimator and what tuning may change.
    It knows nothing about the surveys, so one model can serve both surveys."""

    estimator: Callable
    preprocess: bool    = True
    asinh_target: bool    = True
    preprocessor_params: dict   = field(default_factory = dict)
    model_params: dict          = field(default_factory = dict)
    search_preprocessor: Callable[[optuna.Trial], dict] | None  = None      # what preprocessing parameters tuning may change
    search_model: Callable[[optuna.Trial], dict] | None         = None      # what model parameters tuning may change
    description: str = ""
    name: str | None = None

    def __repr__(self) -> str:
        return _label("Model", name = self.name, description = self.description)
    
    @property
    def is_tunable(self) -> bool:
        """Whether there is anything to tune"""
        return self.search_preprocessor is not None or self.search_model is not None
    

    def get_params(self, trial: optuna.Trial | None = None) -> dict[str, dict]:
        """The settings, as {"preprocessor": {...}, "model": {...}}.
        Without a trial: the defaults. With a trial: the defaults, overwritten by
        the values the search spaces sample from it."""
        def sample(search: Callable | None) -> dict:
            return search(trial) if trial is not None and search is not None else {}
        return {"preprocessor": {**self.preprocessor_params, **sample(self.search_preprocessor)},
                "model":        {**self.model_params,        **sample(self.search_model)}}
    
    
    def get_pipeline(self, features: dict[str, pl.DataType],
                     params: dict[str, dict] | None = None) -> Pipeline:
        """An unfitted pipeline for these features. Without params, the defaults. Outputs polars."""
        params = params or self.get_params()
        model_params = dict(params["model"])
        cat_features = get_cat_features(features)
        if self.preprocess and cat_features and params["preprocessor"].get("cat_encoder") == "native":
            model_params["categorical_features"] = list(range(len(cat_features)))
        estimator = self.estimator(**model_params)
        if self.asinh_target:
            estimator = asinh_transform(estimator)
        steps = [("model", MultiOutputRegressor(estimator))]
        if self.preprocess:
            steps.insert(0, ("preprocessor", load_preprocessor(features, params["preprocessor"])))
        return Pipeline(steps = steps).set_output(transform = "polars")



# --- modelling helpers ---
def get_cat_features(features: dict[str, pl.DataType]) -> list[str]:
    return [k for k, v in features.items() if v in (pl.Categorical, pl.Enum, pl.Boolean, pl.String)]



def load_preprocessor(features: dict[str, pl.DataType], params: dict) -> ColumnTransformer:
    """
    Loads steps to preprocess features
    """
    cat_features = get_cat_features(features)
    num_features = [k for k, v in features.items() if v.is_numeric()]
    unused = set(features) - set(cat_features) - set(num_features)
    assert not unused, f"features of no known kind: {sorted(unused)}"

    return ColumnTransformer(
        transformers = [("cat", load_cat_preprocessor(cat_encoder = params.get("cat_encoder")), cat_features),
                        ("num", load_num_preprocessor(num_scaler = params.get("num_scaler")), num_features)],
        remainder = "drop")



def load_cat_preprocessor(cat_encoder: str):
    """Load categorical preprocessing pipeline"""

    if cat_encoder == "onehot":
        return OneHotEncoder(handle_unknown = 'infrequent_if_exist', sparse_output = False)                       # polars does not accept sparse_output = True

    if cat_encoder == "native":
        return OrdinalEncoder(handle_unknown = 'use_encoded_value', unknown_value = -1, max_categories = 255)

    raise ValueError(f"unknown cat_encoder {cat_encoder!r}; choose 'onehot' or 'native'")



SCALERS = {"standard": StandardScaler, "minmax": MinMaxScaler, "robust": RobustScaler}

def load_num_preprocessor(num_scaler):
    """Load numerical scaler"""
    
    if num_scaler == 'passthrough':
        return 'passthrough'
    if num_scaler not in SCALERS:
        raise ValueError(f"unknown num_scaler {num_scaler!r}; choose 'passthrough' or {list(SCALERS)}")
    return SCALERS[num_scaler]()



def asinh_transform(estimator):
    """asinh-transform the y variables for training; 
    then re-scaling the y variables back when predicting (e.g. for evaluation)"""    

    return TransformedTargetRegressor(regressor = estimator, func = np.arcsinh, inverse_func = np.sinh, check_inverse = True)

