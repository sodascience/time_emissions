import polars as pl

import functions.prep_data as prep
import functions.eval_data as eval


model = "ML"
# model = "baseline"
# model = "perCapita"



# MODEL IMPORTS ----------------------------------------------------------------
if model == "ML":
    import models.histGradientRegressor as model

if model == "baseline":
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

if model == "ML":
    # load pipe
    model = model.load_pipe(features = prep.features)

if model == "baseline":
    # load pipe
    model = model.GroupMeanRegressor(group_feature = "GBAGESLACHT")

if model == "perCapita":
    # load pipe
    model = model.MeanRegressor()


print("Fitting model to data ...")
model.fit(x, y)

# save model to models folder
print("Saving model to file ...")

import joblib
model_filename = "models/model_" + model + ".joblib"
joblib.dump(model, model_filename)



# load model
print("Loading model from files ...")

import joblib
model_filename = "models/model_" + model + ".joblib"
model = joblib.load(model_filename)




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

