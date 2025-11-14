import polars as pl
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, median_absolute_error
import matplotlib.pyplot as plt


home_location_default = 113


def evaluate_model(y_true: pl.DataFrame, y_pred, plot = True, home_location = home_location_default):
    """
    Evaluate model performance by calculating error metrics excluding variable that tracks the time someone spends at home.

    Args:
        y_true (pl.DataFrame): True target values.
        y_pred (pl.DataFrame): Predicted target values.
        plot (bool): Whether to plot histogram of median absolute errors.
        home_location (int): Index of the variable that tracks time spent at home to exclude from evaluation.

    Returns:
        dict: Dictionary containing evaluation metrics (MSE, MAE, MDAE) excluding home location variable.
    
    """

    mse = list(mean_squared_error(y_true, y_pred, multioutput = 'raw_values'))
    mse.pop(home_location)
    mse_sum = np.array(mse).sum()
    mae = list(mean_absolute_error(y_true, y_pred, multioutput = 'raw_values'))
    mae.pop(home_location)
    mae_sum = np.array(mae).sum()
    mdae = list(median_absolute_error(y_true, y_pred, multioutput = 'raw_values'))
    mdae.pop(home_location)
    mdae_sum = np.array(mdae).sum()

    if plot:
        plt.hist(mdae, bins = 15)
        plt.show()

    print(f'Errors of Machine learning (sum of all target errors):')
    print(f'Mean Squared Error: \t\t: {mse_sum}')
    print(f'Mean Absolute Error: \t\t: {mae_sum}')
    print(f'Median Absolute Error: \t\t: {mdae_sum}')
    print(f'Median Absolute Error in days per week: \t: {mdae_sum/24}')
 
    dict = {"mse": mse_sum,
            "mae": mae_sum,
            "mdae": mdae_sum}
    
    return dict




def evaluate_model_groups(df_true: pl.DataFrame, y_pred: pl.DataFrame, grouping_var: str, plot = True, home_location = home_location_default, excel = True):
    """
    Evaluate model performance by groups defined by grouping_var.
    
    Args:
        df_true (pl.DataFrame): DataFrame containing true target values and grouping variable.
        y_pred (pl.DataFrame): DataFrame containing predicted target values.
        grouping_var (str): Column name in df_true to group by.
        plot (bool): Whether to plot histogram of median absolute errors for each group.
        home_location (int): Index of the variable that tracks time spent at home to exclude from evaluation.
        excel (bool): Whether to print results in a format suitable for Excel.

    Returns:
        group_evals (dict): Dictionary containing evaluation metrics for each group.
    
    """

    group_evals = dict()

    groups = df_true[grouping_var].unique()

    for group in groups:
        print("\n")
        print(group)


        y_true_group = (df_true.filter(df_true[grouping_var] == group)
                        .select(y_pred.columns))
        y_pred_group = (y_pred.filter(df_true[grouping_var] == group))
        
        group_evals[group] = evaluate_model(y_true = y_true_group,
                                            y_pred = y_pred_group,
                                            plot = plot,
                                            home_location = home_location)
    
    if excel:
        print("\nFor Excel")
        mse_genders = (f"{round(group_evals['1']['mse'], 4)};{round(group_evals['2']['mse'], 4)}")
        mae_genders = (f"{round(group_evals['1']['mae'], 4)};{round(group_evals['2']['mae'], 4)}")
        mdae_genders = (f"{round(group_evals['1']['mdae'], 4)};{round(group_evals['2']['mdae'], 4)}")
        print(f"{mse_genders};{mae_genders};{mdae_genders};")


    return group_evals
        
