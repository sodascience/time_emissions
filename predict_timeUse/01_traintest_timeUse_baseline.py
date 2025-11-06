import polars as pl

import functions.prep_data as prep
import functions.eval_data as eval

# model
import models.baseline_model


# LOAD DATA ------------------------------------------------------------------

df_true = prep.load_df()
# contains hours per week per activity

print(df_true)



# y_names: list of variable names of y variables (to be predicted)
y_names = [col for col in df_true.columns if col.startswith("activity_")]

# create x and y dataframes for ease of access
x_train = (df_true
           .filter(pl.col("split_sample") == "train")
           .select(prep.features.keys())
           )

y_train = (df_true
           .filter(pl.col("split_sample") == "train")
           .select(y_names)
           )

print(x_train)
print(y_train)






# MODEL ----------------------------------------------------------------------

# fit baseline model (gender means)
baseline_model = models.baseline_model.GroupMeanRegressor(group_feature = "GBAGESLACHT")
baseline_model.fit(x_train, y_train)

# save model
import joblib
joblib.dump(baseline_model, "baseline_model_train.joblib")

# load model
import joblib
print("Loading model from files ...")
baseline_model = joblib.load("baseline_model_train.joblib")





# PREDICT TRAINING DATA -------------------------------------------------------

print("Predicting training data ...")
y_train_pred = baseline_model.predict(x_train)
y_train_pred = pl.DataFrame(y_train_pred)
print(y_train_pred)
print(y_names)
y_train_pred.columns = y_names





# PREDICT TEST DATA -----------------------------------------------------------

x_test = (df_true
           .filter(pl.col("split_sample") == "test")
           .select(prep.features.keys())
           )

y_test = (df_true
           .filter(pl.col("split_sample") == "test")
           .select(y_names)
           )

print("Predicting test data ...")
y_test_pred = baseline_model.predict(x_test)
y_test_pred = pl.DataFrame(y_test_pred)
y_test_pred.columns = y_names                                          # assign column names (targets)

print(y_test_pred)





# EVALUATE MODELS -------------------------------------------------------------


# training data
print("\n\nModel evaluation training data:")
eval.evaluate_model_groups(df_true = df_true.filter(pl.col("split_sample") == "train"),
                           y_pred = y_train_pred,
                           grouping_var = "GBAGESLACHT",
                           plot = True)



# test data
print("\n\nModel evaluation test data:")
eval.evaluate_model_groups(df_true = df_true.filter(pl.col("split_sample") == "test"),
                           y_pred = y_test_pred,
                           grouping_var = "GBAGESLACHT",
                           plot = True,
                           excel = True)









# SAVE TEST PREDICTIONS ---------------------------------------------------------------
# add RINPERSOON to y_test_pred
RIN_test = (df_true
    .filter(pl.col("split_sample") == "test")
    .select("RINPERSOON")
)
y_test_pred = y_test_pred.with_columns(pl.Series("RINPERSOON", RIN_test))

# reorder columns to have RINPERSOON first
cols = ["RINPERSOON"] + [c for c in y_test_pred.columns if c != "RINPERSOON"]
y_test_pred = y_test_pred[cols]

print(y_test_pred)



filename = "F:/Documents/Data/predicted_timeUse_baseline_tboPPs_testData.parquet"
y_test_pred.write_parquet(filename)

print(f"Successfully wrote {filename}")
