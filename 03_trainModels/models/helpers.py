import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor


def createPipeline(preprocess, model):
    """
    Create a sklearn pipeline with a preprocessing step and a model step.

    Args:
        preprocess: sklearn-compatible preprocessing object
        model: sklearn-compatible model object

    """

    base_pipe = Pipeline(steps = [
        ("preprocess", preprocess),
        ("model", model)
    ])

    pipe = TransformedTargetRegressor(
        regressor = base_pipe,
        func = np.log1p,                # take the log of each y variable (log(y+1) actually to avoid errors of log(0))
        inverse_func = np.expm1         # return to the original scaling of the y data so that the output is again in hours (not log(y+1))
    )

    # pipe.set_output(transform = "polars") # does not work with TransformedTargetRegressor 

    return(pipe)




def order_by_mean(x, descending = True):
    """
    Order the columns of a polars DataFrame by their mean value.

    Args:
        x: polars DataFrame
        descending: bool, whether to sort in descending order (default True)

    Returns:
        order: list of column indices ordered by mean value
    """


    sorted_vars = (x.mean()
               .transpose(include_header = True, header_name = "variable", column_names = ["mean"])
               .sort("mean", descending = descending)
               .get_column("variable")
               .to_list()
    )

    order = [x.columns.index(v) for v in sorted_vars]

    return order