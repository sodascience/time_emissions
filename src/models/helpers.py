import numpy as np
import polars as pl
import warnings
from pathlib import Path
import joblib

from sklearn.metrics import mean_squared_error, mean_absolute_error, median_absolute_error
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, FunctionTransformer
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline




def load_preprocessor(features):

    # transformer for categorical features
    cat_features = [k for k, v in features.items() if v in (pl.Categorical, pl.Boolean)]
    print(f"Categorical features: {cat_features}")

    cat_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy = 'constant', fill_value = 'missing')),
        ('encoder', OneHotEncoder(handle_unknown = 'infrequent_if_exist', 
                                  drop = 'if_binary',
                                  sparse_output = False))
    ])

    # cat_transformer = OneHotEncoder(handle_unknown = "infrequent_if_exist",
    #                                 drop = "if_binary",            # avoid redundant category for 2-level features
    #                                 sparse_output = False)

    # cat_transformer = OrdinalEncoder()

    # passthrough for categorical variables not possible because "passthrough" converts pl.Categorical somehow so that they are not categorical anymore,
    # this way, native support does not work correctly anymore. 
    # Instead, you can simply pass the model, without preprocessing in the pipeline below
    # cat_transformer = "passthrough"



    # transformer for numerical features
    num_features = [k for k, v in features.items() if v in (pl.Float64, pl.Int64)]
    print(f"Numerical features: {num_features}")

    num_transformer = SimpleImputer(strategy = 'mean')
    # num_transformer = "passthrough"

    # combine transformers with each other
    preprocess = ColumnTransformer(
        transformers = [('cat', cat_transformer, cat_features), 
                        ('num', num_transformer, num_features)],
        remainder = "passthrough"                                          # drop any columns that are not in prep.features
    )

    return preprocess






def load_pipe(features, model, log_transform = True, order_regressorChain = "random"):
    preprocess = load_preprocessor(features = features)
    model = model

    pipe = Pipeline(steps = [
        ("preprocess", preprocess),
        ("model", model)
    ])

    if log_transform:
        # transform targets as follows:
        # replace negative values with 0
        # take the log of each y variable (log(y+1) actually to avoid errors of log(0))
        pipe = TransformedTargetRegressor(
            regressor = pipe,
            func = safe_log1p,                
            inverse_func = np.expm1,         # return to the original scaling of the y data so that the output is again in hours (not log(y+1))
            check_inverse = False
        )

    else:
        pipe.set_output(transform = "polars") # does not work with TransformedTargetRegressor 

    return pipe
    # return model



def safe_log1p(y):
    """
    Clip negatives to 0 and log-transform, warning once if negatives are present
    """

    if np.any(y < 0):
        warnings.warn(
            f"Negative target values deteccted and set to 0 before log1p transform "
            f"({np.sum(y < 0)} total across all outputs.)",
            UserWarning
        )

    return np.log1p(np.clip(y, a_min = 0, a_max = None))
        



def order_by_mean(x, descending = True):
    sorted_vars = (x.mean()
               .transpose(include_header = True, header_name = "variable", column_names = ["mean"])
               .sort("mean", descending = descending)
               .get_column("variable")
               .to_list()
    )

    order = [x.columns.index(v) for v in sorted_vars]

    return order



def check_unknownCategories(x, model):
    preprocessor = model.regressor_.named_steps["preprocess"]

    ohe = preprocessor.named_transformers_["cat"]

    for col, cats in zip(ohe.feature_names_in_, ohe.categories_):
        # print(f"{col}: known categories = {cats}")

        if col in x.columns:
            unknowns = set(x[col].unique()) - set(cats)
            if unknowns:
                print(f"Unknown categories in {col}: {unknowns}")







# MODEL EVALUATIONS --------------------------------------------------------

def evaluate_model(y_true: pl.DataFrame, y_pred, plot = True, excludevar_loc = None):
    mse = list(mean_squared_error(y_true, y_pred, multioutput = 'raw_values'))
    if excludevar_loc is not None:
        mse.pop(excludevar_loc)
    mse_sum = np.array(mse).sum()

    mae = list(mean_absolute_error(y_true, y_pred, multioutput = 'raw_values'))
    if excludevar_loc is not None:
        mae.pop(excludevar_loc)
    mae_sum = np.array(mae).sum()

    mdae = list(median_absolute_error(y_true, y_pred, multioutput = 'raw_values'))
    if excludevar_loc is not None:
        mdae.pop(excludevar_loc)
    mdae_sum = np.array(mdae).sum()

    if plot:
        plt.hist(mdae, bins = 15)
        plt.show()

    print(f'Errors of Machine learning (sum of all target errors):')
    print(f'Mean Squared Error: \t\t: {mse_sum}')
    print(f'Mean Absolute Error: \t\t: {mae_sum}')
    print(f'Median Absolute Error: \t\t: {mdae_sum}')
 
    dict = {"mse": mse_sum,
            "mae": mae_sum,
            "mdae": mdae_sum}
    
    return dict




def evaluate_model_groups(df_true: pl.DataFrame, y_pred: pl.DataFrame, grouping_var: str, plot = True, excludevar_loc = None, excel = True):
    group_evals = dict()

    groups = df_true[grouping_var].unique()

    for group in groups:
        print("\n")
        print(group)


        # indices = df_true.loc[(df_true[grouping_var] == group)].index

        y_true_group = (df_true.filter(df_true[grouping_var] == group)
                        .select(y_pred.columns))
        y_pred_group = (y_pred.filter(df_true[grouping_var] == group))
        
        group_evals[group] = evaluate_model(y_true = y_true_group,
                                            y_pred = y_pred_group,
                                            plot = plot,
                                            excludevar_loc = excludevar_loc)
    
    if excel:
        ordered_groups = sorted(group_evals.keys())

        mse_str = "; ".join(
            str(round(group_evals[group]['mse'], 4))
            for group in ordered_groups
        )
        mae_str = "; ".join(
            str(round(group_evals[group]['mae'], 4))
            for group in ordered_groups
        )
        mdae_str = "; ".join(
            str(round(group_evals[group]['mdae'], 4))
            for group in ordered_groups
        )

        print(f"Evaluation metrics for {grouping_var} (values: ", ", ".join(ordered_groups), ")")        
        print(f"{mse_str};{mae_str};{mdae_str};")


    return group_evals
        