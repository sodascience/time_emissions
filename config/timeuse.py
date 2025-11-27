import polars as pl
import src.utils.helpers as helpers

survey_name = "timeuse"
id_var = "RINPERSOON"

features_ML = helpers.read_features(survey_name)
features_baseline = {"GBAGESLACHT": pl.Categorical} # max 1 grouping feature


# EVALUATION PARAMETERS
eval_group_var = "GBAGESLACHT"
eval_exclude_var = None