import polars as pl
import joblib
from pathlib import Path

import src.models.helpers as helpers



# CONFIGURATION --------------------------------------------------------------

# CHOOSE SURVEY
# import config.expenditures as survey            # expenditures
import config.timeuse as survey                 # timeuse


# CHOOSE MODEL
# model_name = "ML"
model_name = "baseline"



## IMPORTS ------------------------------------------------------------------

# define features based on model_name
if model_name == "ML":
    features = survey.features_ML

if model_name == "baseline":
    features = survey.features_baseline






# PREDICT DATA -------------------------------------------------------------------

## LOAD DATA ---------------------------------------------------------------------

x_file_loc = Path("processed_data", "true", "demographics.parquet")
df_demographics = pl.read_parquet(x_file_loc)

x = df_demographics.select(features.keys())



# read y_names
y_file_loc = Path("processed_data", "true", f"{survey.survey_name}.parquet")
y_names = (pl.scan_parquet(y_file_loc)
           .select(pl.exclude(survey.id_var))
           .collect_schema()
           .names()
)



## LOAD MODEL --------------------------------------------------------------------

print(f"Loading {model_name} model from files ...")
save_path = Path("trained_models", f"{survey.survey_name}_{model_name}.joblib")
pipe = joblib.load(save_path)



## CHECK UNKNOWN CATEGORIES ------------------------------------------------------

try:
    helpers.check_unknownCategories(x = x, model = pipe)
except:
    UserWarning(f"You can not check for unknown categories in a {model_name} model (yet).")



## PREDICT DATA ------------------------------------------------------------------

print(f"Predicting {survey.survey_name} ...")

y_pred = pipe.predict(x)
y_pred = pl.DataFrame(y_pred)
y_pred.columns = y_names # potentially redundant (in baseline)

print(f"Successfully predicted {survey.survey_name} data from {model_name} model")
print(y_pred)



# add id_var to y_pred
y_pred = y_pred.with_columns(pl.Series(survey.id_var, df_demographics[survey.id_var]))

# reorder columns to have RINPERSOON first
cols = [survey.id_var] + [c for c in y_pred.columns if c != survey.id_var]
y_pred = y_pred[cols]



## SAVE PREDICTED DATA -----------------------------------------------------------

save_path = Path("processed_data", "predicted", f"{survey.survey_name}_{model_name}.parquet")
save_path.parent.mkdir(parents = True, exist_ok = True)

y_pred.write_parquet(save_path)

print(f"Successfully wrote {save_path}")