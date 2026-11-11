import polars as pl

from config.surveys import *

# --- calculate population expenditures per expenditure category ---
exp_df = Surveys.EXPENDITURES.read_responses().collect()
sums = exp_df.select(pl.col(Surveys.EXPENDITURES.target_pattern) * pl.col(Surveys.EXPENDITURES.weight.name)).sum()
sums = sums.unpivot(variable_name = "variable", value_name = "weighted_sum")
sums.write_parquet(OUT / "input_output_analysis/expenditures_population_sums.parquet")


# --- now, do the input-output analysis with the offline script ---
# the result should be a (csv) file emission_intensity_per_expenditure
