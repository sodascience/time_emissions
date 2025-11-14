import polars as pl
import pathlib

import functions.prep_data as prep

model_name = "ML"
# model_name = "baseline"
# model_name = "perCapita"


# LOAD DATA ------------------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"df_demographics.parquet"
df_demographics = pl.read_parquet(save_path)

x = df_demographics.select(prep.features.keys())

# read y column names
save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"TBO_aggregated.parquet"
y_names = pl.read_parquet_schema(save_path).keys()




# LOAD MODEL ----------------------------------------------------------

import joblib
print(f"Loading {model_name} model from files ...")

save_path = pathlib.Path(__file__).resolve().parents[1]/"trained_models"/f"{model_name}.joblib"
model = joblib.load(save_path)



# PREDICT DATA -------------------------------------------------------

print("Predicting time-use ...")
y_pred = model.predict(x)
y_pred = pl.DataFrame(y_pred)
y_pred.columns = y_names # potentially redundant (in baseline)

print(y_pred)

# add RINPERSOON to y_pred
y_pred = y_pred.with_columns(pl.Series("RINPERSOON", df_demographics["RINPERSOON"]))

# reorder columns to have RINPERSOON first
cols = ["RINPERSOON"] + [c for c in y_pred.columns if c != "RINPERSOON"]
y_pred = y_pred[cols]




# SAVE PREDICTED DATA -------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}.parquet"
save_path.parent.mkdir(parents = True, exist_ok = True)
y_pred.write_parquet(save_path)

print(f"Successfully wrote {save_path}")

