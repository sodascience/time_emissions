import polars as pl

import functions.prep_data as prep
import functions.eval_data as eval


# model
import models.histGradientRegressor as model


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

# load pipe
pipe = model.load_pipe(features = prep.features)

print("Fitting model to data ...")
pipe.fit(x, y)

# save model
import joblib
joblib.dump(pipe, "pipe.joblib")



# load model
import joblib
print("Loading model from files ...")
pipe = joblib.load("pipe.joblib")





# PREDICT DATA -------------------------------------------------------

print("Predicting training data ...")
y_pred = pipe.predict(x)
y_pred = pl.DataFrame(y_pred)
y_pred.columns = y_names





# EVALUATE MODELS -------------------------------------------------------------

# training data
print("\n\nModel evaluation training data:")
eval.evaluate_model_groups(df_true,
                           y_pred = y_pred,
                           grouping_var = "GBAGESLACHT",
                           plot = True)

