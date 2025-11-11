import polars as pl
import pathlib

import functions.prep_data as prep
import functions.eval_data as eval
import models.helpers as helpers

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

df_true = prep.load_df()

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




# FIT TRAINING DATA ----------------------------------------------------------

if model_name == "ML":
    # load pipe
    model = model.load_pipe(features = prep.features, 
                        order_regressorChain = helpers.order_by_mean(y_train))

if model_name == "baseline":
    # load pipe
    model = model.GroupMeanRegressor(group_feature = "GBAGESLACHT")

if model_name == "perCapita":
    # load pipe
    model = model.MeanRegressor()


print("Fitting model to data ...")
model.fit(x_train, y_train)

# save model
import joblib
save_path = pathlib.Path(__file__).resolve().parents[1]/"trained_models"/f"{model_name}_train.joblib"
save_path.parent.mkdir(parents = True, exist_ok = True)
joblib.dump(model, save_path)



# load model
print("Loading model from files ...")

import joblib
save_path = pathlib.Path(__file__).resolve().parents[1]/"trained_models"/f"{model_name}_train.joblib"
model = joblib.load(save_path)





# PREDICT TRAINING DATA -------------------------------------------------------

print("Predicting training data ...")
y_train_pred = model.predict(x_train)
y_train_pred = pl.DataFrame(y_train_pred)
y_train_pred.columns = y_names







# PREDICT TEST DATA -----------------------------------------------------------

# create x and y dataframes for ease of access
x_test = (df_true
           .filter(pl.col("split_sample") == "test")
           .select(prep.features.keys())
           )

y_test = (df_true
           .filter(pl.col("split_sample") == "test")
           .select(y_names)
           )

print("Predicting test data ...")
y_test_pred = model.predict(x_test)
y_test_pred = pl.DataFrame(y_test_pred)
y_test_pred.columns = y_names

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



save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}_tboPPs_testData.parquet"
save_path.parent.mkdir(parents = True, exist_ok = True)
y_test_pred.write_parquet(save_path)

print(f"Successfully wrote {save_path}")
