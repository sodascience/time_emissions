import polars as pl
import src.utils.helpers as helpers

survey_name = "expenditures"
id_var = "HUISHOUDNR"

features_ML = helpers.read_features(survey_name)
features_baseline = {"AANTALPERSHH": pl.Int64} # max 1 grouping feature


# EVALUATION PARAMETERS
eval_group_var = "TYPHH"
eval_exclude_var = None