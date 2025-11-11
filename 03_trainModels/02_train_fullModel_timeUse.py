import polars as pl
import pathlib

import functions.prep_data as prep
import functions.eval_data as eval

model_name = "ML"
# model_name = "baseline"
# model_name = "perCapita"


# MODEL IMPORTS ----------------------------------------------------------------
if model_name == "ML":
    import models.histGradientRegressor as model

if model_name == "baseline":
    import models.baseline_model as model

if model_name == "perCapita":
    import models.baseline_model as model



# LOAD DATA ------------------------------------------------------------------

df_true = prep.load_df(train_test = False)

# y_names: list of variable names of y variables (to be predicted)
y_names = [col for col in df_true.columns if col.startswith("activity_")]

# create x and y dataframes for ease of access
x = df_true.select(prep.features.keys())
y = df_true.select(y_names)

print(x)
print(y)




# FIT MODEL ----------------------------------------------------------

if model_name == "ML":
    # load pipe
    model = model.load_pipe(features = prep.features)

if model_name == "baseline":
    # load pipe
    model = model.GroupMeanRegressor(group_feature = "GBAGESLACHT")

if model_name == "perCapita":
    # load pipe
    model = model.MeanRegressor()


print("Fitting model to data ...")
model.fit(x, y)

# save model to models folder
print("Saving model to file ...")

import joblib
save_path = pathlib.Path(__file__).resolve().parents[1]/"trained_models"/f"{model_name}.joblib"
save_path.parent.mkdir(parents = True, exist_ok = True)
joblib.dump(model, save_path)



# load model
print("Loading model from files ...")

import joblib
save_path = pathlib.Path(__file__).resolve().parents[1]/"trained_models"/f"{model_name}.joblib"
model = joblib.load(save_path)




# PREDICT DATA -------------------------------------------------------

print("Predicting training data ...")
y_pred = model.predict(x)
y_pred = pl.DataFrame(y_pred)
y_pred.columns = y_names





# EVALUATE MODELS -------------------------------------------------------------

# training data
print("\n\nModel evaluation training data:")
eval.evaluate_model_groups(df_true,
                           y_pred = y_pred,
                           grouping_var = "GBAGESLACHT",
                           plot = True)

