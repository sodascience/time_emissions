import polars as pl
import pathlib

model_name = "ML"
# model_name = "baseline"
# model_name = "perCapita"

# READ BUDGET DATA --------------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"budget_df.parquet"

lf_budget = (
    pl.scan_parquet(save_path)
    .select("RINPERSOON")
    .rename({"RINPERSOON": "RINPERSOONHKW"})      # rename RINPERSOON to RINPERSOONHKW
)



# EXTEND BUDGET DATA ------------------------------------------------------------
# extend df_budget by adding all household members of households participating in the budget survey

# read df_demographics to match RINPERSOONHKWs to RINPERSOONs
save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"df_demographics.parquet"

lf_demographics = (
    pl.scan_parquet(save_path)
    .select(["RINPERSOON", "RINPERSOONHKW"])
)

# join by RINPERSOONHKW
lf_budget = lf_budget.join(lf_demographics, on = "RINPERSOONHKW")



# READ PREDICTED TIME-USE -------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}.parquet"

df = (
    pl.scan_parquet(save_path)
    .join(lf_budget, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df)




# SAVE DATA ---------------------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}_budgetPPs.parquet"

df.write_parquet(save_path)
print(f"Successfully wrote {save_path}")
