import polars as pl
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split

import src.models.helpers as helpers



# CONFIGURATION --------------------------------------------------------------

# CHOOSE SURVEY
# import config.expenditures as survey            # expenditures
import config.timeuse as survey        # timeuse


# CHOOSE MODEL
# model_name = "ML"
model_name = "baseline"



## IMPORTS ------------------------------------------------------------------

# define features based on model_name
if model_name == "ML":
    features = survey.features_ML

if model_name == "baseline":
    features = survey.features_baseline






# LOAD DATA ------------------------------------------------------------------

x_file_loc = Path("processed_data", "true", f"demographics_{survey.survey_name}.parquet")
y_file_loc = Path("processed_data", "true", f"{survey.survey_name}.parquet")

# read parquet files
df_x = pl.read_parquet(x_file_loc)
df_y = pl.read_parquet(y_file_loc)

# join them to make sure they are in the same order
df = (df_x
      .join(df_y, on = survey.id_var, how = "inner")
      .sort(survey.id_var)
)

# split into train and test data
df_train, df_test = train_test_split(df,
                                     test_size = 0.2,
                                     random_state = 42)

x_names = features.keys()
x = df.select(x_names)
x_train = df_train.select(x_names)
x_test = df_test.select(x_names)

y_names = df_y.select(pl.exclude(survey.id_var)).columns
y = df.select(y_names)
y_train = df_train.select(y_names)
y_test = df_test.select(y_names)



# print datasets to check
print(x_train)
print(y_train)






# MODEL IMPORTS -------------------------------------------------------------

if model_name == "ML":
    from src.models.histGradientRegressor import model

    pipe = helpers.load_pipe(features = features, 
                             model = model,
                             log_transform = True,
                             order_regressorChain = helpers.order_by_mean(y_train))



if model_name == "baseline":
    import src.models.baseline_model as baseline_model

    # if no feature is specified, use the MeanRegressor
    if len(features) == 0:
        pipe = baseline_model.MeanRegressor()

    # if 1 feature is specified, use the GroupMeanRegressor
    if len(features) == 1: 
        group_feature = list(features.keys())[0]
        pipe = baseline_model.GroupMeanRegressor(group_feature = group_feature)
    
    # if more than 1 feature is specified, raise an error  
    else:
        raise ValueError(f"{model_name} model must have either 0 or 1 grouping feature")






# FIT TRAINING DATA ----------------------------------------------------------

print(f"Fitting {model_name} model to {survey.survey_name} training data ...")
pipe.fit(x_train, y_train)

# save model
save_path = Path("trained_models", f"{survey.survey_name}_{model_name}_train.joblib")
save_path.parent.mkdir(parents = True, exist_ok = True)
joblib.dump(pipe, save_path)



# load model
print(f"Loading {model_name} model from files ...")

save_path = Path("trained_models", f"{survey.survey_name}_{model_name}_train.joblib")
pipe = joblib.load(save_path)






# PREDICT DATA -----------------------------------------------------------------

## TRAINING DATA ---------------------------------------------------------------

print(f"Predicting {survey.survey_name} training data ...")
y_train_pred = pipe.predict(x_train)
y_train_pred = pl.DataFrame(y_train_pred)
y_train_pred.columns = y_names



## TEST DATA -------------------------------------------------------------------

print(f"Predicting {survey.survey_name} test data ...")
y_test_pred = pipe.predict(x_test)
y_test_pred = pl.DataFrame(y_test_pred)
y_test_pred.columns = y_names

print(y_test_pred)






# EVALUATE MODELS -------------------------------------------------------------

## TRAINING DATA ---------------------------------------------------------------

print("\n\nModel evaluation training data:")
helpers.evaluate_model_groups(df_true = df_train,
                           y_pred = y_train_pred,
                           excludevar_loc = survey.eval_exclude_var,
                           grouping_var = survey.eval_group_var,
                           plot = False)



## TEST DATA -------------------------------------------------------------------

print("\n\nModel evaluation test data:")
helpers.evaluate_model_groups(df_true = df_test,
                           y_pred = y_test_pred,
                           excludevar_loc = survey.eval_exclude_var,
                           grouping_var = survey.eval_group_var,
                           plot = False,
                           excel = True)






# SAVE TEST PREDICTIONS ---------------------------------------------------------------

# add RINPERSOON to y_test_pred
RIN_test = df_test.select(survey.id_var)

y_test_pred = y_test_pred.with_columns(pl.Series(survey.id_var, RIN_test))



# reorder columns to have RINPERSOON first
cols = [survey.id_var] + [c for c in y_names]
y_test_pred = y_test_pred[cols]

print(y_test_pred)



# save data
save_path = Path("processed_data", "predicted", f"{survey.survey_name}_{model_name}_testData.parquet")
save_path.parent.mkdir(parents = True, exist_ok = True)
y_test_pred.write_parquet(save_path)

print(f"Successfully wrote {save_path}")






# FIT MODEL TO FULL DATASET ------------------------------------------------------

print(f"Fitting {model_name} model to full {survey.survey_name} data ...")
pipe.fit(x, y)

# save model
save_path = Path("trained_models", f"{survey.survey_name}_{model_name}.joblib")
save_path.parent.mkdir(parents = True, exist_ok = True)

joblib.dump(pipe, save_path)
print(f"Successfully saved {save_path}")