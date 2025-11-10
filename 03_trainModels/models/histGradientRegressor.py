import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder
from sklearn.multioutput import MultiOutputRegressor, RegressorChain
from sklearn.ensemble import HistGradientBoostingRegressor

import functions.prep_data as prep

import models.helpers as helpers


def load_preprocessor(features = prep.features):
    """
    Load preprocessor for HistGradientBoostingRegressor model.

    Args:
        features: dictionary of feature names and their types

    Returns:
        ColumnTransformer: preprocessor for the model
    """


    # transformer for categorical features
    cat_transformer = ("cat",
                    OneHotEncoder(handle_unknown = "ignore",
                                    drop = "if_binary",            # avoid redundant category for 2-level features
                                    sparse_output = False),               # create dense matrix for simplicity
                    [k for k, v in features.items() if v == pl.Categorical])

    # cat_transformer = ("cat",
    #                    OrdinalEncoder(),
    #                    [k for k, v in features.items() if v == pl.Categorical])

    # passthrough for categorical variables not possible because "passthrough" converts pl.Categorical somehow so that they are not categorical anymore,
    # this way, native support does not work correctly anymore. 
    # Instead, you can simply pass the model, without preprocessing in the pipeline below
    # cat_transformer = ("cat",
    #                    "passthrough",
    #                    [k for k, v in prep.features.items() if v == pl.Categorical])

    # transformer for numerical features
    num_transformer = ("num",
                       "passthrough",                               # keep numeric columns as is
                       [k for k, v in features.items() if (v == pl.Float64 | v == pl.Int64)])


    # combine transformers with each other
    preprocess = ColumnTransformer(
        transformers = [cat_transformer, num_transformer],
        remainder = "passthrough"                                          # drop any columns that are not in prep.features
    )

    return preprocess



def load_model(order_regressorChain = "random"):
    """
    Load HistGradientBoostingRegressor model.

    Args:
        order_regressorChain: order of targets for RegressorChain, "random" or list of target names

    Returns:
        MultiOutputRegressor: model for the pipeline
    """

    model = MultiOutputRegressor(
        HistGradientBoostingRegressor(
            random_state = 42,
            categorical_features = "from_dtype" # from scikit-learn 1.2
        )
    )

    # model = RegressorChain(
    #     HistGradientBoostingRegressor(
    #         random_state = 42 # ,
    #         # categorical_features = "from_dtype" # from scikit-learn 1.2
    #     ),
    #     order = order_regressorChain
    # )

    return model



def load_pipe(features = prep.features, order_regressorChain = "random"):
    """
    Load pipeline for HistGradientBoostingRegressor model.

    Args:
        features: dictionary of feature names and their types
        order_regressorChain: order of targets for RegressorChain, "random" or list of target names

    Returns:
        Pipeline: pipeline for the model
    """
    

    preprocess = load_preprocessor(features = features)
    model = load_model(order_regressorChain = order_regressorChain)

    pipe = helpers.createPipeline(preprocess, model)

    return pipe
    # return model


