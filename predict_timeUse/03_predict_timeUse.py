import polars as pl

import functions.prep_data as prep

model_name = "ML"
# model_name = "baseline"
# model_name = "perCapita"


# LOAD DATA ------------------------------------------------------------------

df_demographics = pl.read_parquet("F:/Documents/Data/df_demographics.parquet")

x = df_demographics.select(prep.features.keys())

# read y column names
y_names = pl.read_parquet_schema("F:/Documents/Data/TBO_aggregated.parquet").keys()




# LOAD MODEL ----------------------------------------------------------

import joblib
print(f"Loading {model_name} model from files ...")

if model_name == "ML":
    pipe = joblib.load("pipe.joblib")

if model_name == "baseline":
    pipe = joblib.load("baseline_model.joblib")

if model_name == "perCapita":
    pipe = joblib.load("perCapita_model.joblib")




# PREDICT DATA -------------------------------------------------------

print("Predicting time-use ...")
y_pred = pipe.predict(x)
y_pred = pl.DataFrame(y_pred)
y_pred.columns = y_names # potentially redundant (in baseline)

print(y_pred)

# add RINPERSOON to y_pred
y_pred = y_pred.with_columns(pl.Series("RINPERSOON", df_demographics["RINPERSOON"]))

# reorder columns to have RINPERSOON first
cols = ["RINPERSOON"] + [c for c in y_pred.columns if c != "RINPERSOON"]
y_pred = y_pred[cols]




# SAVE PREDICTED DATA -------------------------------------------------

filename = "F:/Documents/Data/predicted_timeUse_" + model_name + ".parquet"
y_pred.write_parquet(filename)

print(f"Successfully wrote {filename}")




