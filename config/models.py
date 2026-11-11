from config.features import *

from sklearn.ensemble import HistGradientBoostingRegressor
from src.models.baseline_model import GroupedMeanRegressor


HH_TYPE_GROUPS = {"1": "single_noChildren",
                  "2": "couple_noChildren",
                  "3": "couple_noChildren",
                  "4": "couple_children",
                  "5": "couple_children",
                  "6": "single_children",
                  "7": "other"}

class Models(Namespace):
    """Every pipeline that the surveys can use."""
    kind = Model

    HIST_GRADIENT = Model(estimator = HistGradientBoostingRegressor,
                          model_params = {
                              "early_stopping":     True,
                              "max_iter":           1000,
                              "random_state":       42},
                          preprocessor_params = {
                              "cat_encoder":  "native",
                              "num_scaler":   "passthrough"
                          },
                          search_preprocessor = None,
                          search_model = lambda tuning_trial: {
                              "learning_rate":    tuning_trial.suggest_float("learning_rate", 0.001, 0.2, log = True),
                              "max_leaf_nodes":   tuning_trial.suggest_int("max_leaf_nodes", 15, 100),
                              "min_samples_leaf": tuning_trial.suggest_int("min_samples_leaf", 5, 100),
                              "max_features":     tuning_trial.suggest_float("max_features", 0.1, 1.0),
                              "l2_regularization": tuning_trial.suggest_float("l2_regularization", 0.001, 10, log = True)
                          },
                          asinh_target = True,
                          description = "Histogram gradient boosting regressor"
    )

    GENDER_MEAN = Model(estimator = GroupedMeanRegressor,
                        model_params = {"group_col": DemographyPerson.gender.name},
                        preprocess = False, asinh_target = False,
                        description = "Mean per gender")
    
    HH_TYPE_MEAN = Model(estimator = GroupedMeanRegressor,
                         model_params = {"group_col": CompositionHousehold.type_hh.name,
                                         "recode": HH_TYPE_GROUPS},
                         preprocess = False, asinh_target = False,
                         description = "Mean per household type, regrouped")
 