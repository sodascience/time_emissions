import polars as pl

# READ BUDGET DATA --------------------------------------------------------------

lf_budget = (
    pl.scan_parquet("data/true/budget_df.parquet")
    .select("RINPERSOON")
    .rename({"RINPERSOON": "RINPERSOONHKW"})      # rename RINPERSOON to RINPERSOONHKW
)



# EXTEND BUDGET DATA ------------------------------------------------------------
# extend df_budget by adding all household members of households participating in the budget survey

# read df_demographics to match RINPERSOONHKWs to RINPERSOONs
lf_demographics = (
    pl.scan_parquet("data/true/df_demographics.parquet")
    .select(["RINPERSOON", "RINPERSOONHKW"])
)

# join by RINPERSOONHKW
lf_budget = lf_budget.join(lf_demographics, on = "RINPERSOONHKW")



# READ PREDICTED TIME-USE -------------------------------------------------------
# read predicted time-use of population

df_ML = (
    pl.scan_parquet("data/predicted/timeUse_ML.parquet")
    .join(lf_budget, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_ML)


# read baseline predictions

df_baseline = (
    pl.scan_parquet("data/predicted/timeUse_baseline.parquet")
    .join(lf_budget, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_baseline)


# read perCapita predictions

df_perCapita = (
    pl.scan_parquet("data/predicted/timeUse_perCapita.parquet")
    .join(lf_budget, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_perCapita)



# SAVE DATA ---------------------------------------------------------------------

# machine learning
filename = "data/predicted/timeUse_ML_budgetPPs.parquet"
df_ML.write_parquet(filename)
print(f"Successfully wrote {filename}")

# baseline
filename = "data/predicted/timeUse_baseline_budgetPPs.parquet"
df_baseline.write_parquet(filename)
print(f"Successfully wrote {filename}")

# perCapita
filename = "data/predicted/timeUse_perCapita_budgetPPs.parquet"
df_perCapita.write_parquet(filename)
print(f"Successfully wrote {filename}")