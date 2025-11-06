import polars as pl

# READ TBO DATA ----------------------------------------------------------------

lf_TBO = (
    pl.scan_parquet("F:/Documents/Data/TBO_aggregated.parquet")
    .select("RINPERSOON")
)



# READ PREDICTED TIME-USE -------------------------------------------------------
# read predicted time-use of population

df_ML = (
    pl.scan_parquet("F:/Documents/Data/predicted_timeUse_ML.parquet")
    .join(lf_TBO, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_ML)


# read baseline predictions

df_baseline = (
    pl.scan_parquet("F:/Documents/Data/predicted_timeUse_baseline.parquet")
    .join(lf_TBO, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_baseline)


# read perCapita predictions

df_perCapita = (
    pl.scan_parquet("F:/Documents/Data/predicted_timeUse_perCapita.parquet")
    .join(lf_TBO, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_budget
    .collect()
)

print(df_perCapita)



# SAVE DATA ---------------------------------------------------------------------

# machine learning
filename = "F:/Documents/Data/predicted_timeUse_ML_tboPPs.parquet"
df_ML.write_parquet(filename)
print(f"Successfully wrote {filename}")

# baseline
filename = "F:/Documents/Data/predicted_timeUse_baseline_tboPPs.parquet"
df_baseline.write_parquet(filename)
print(f"Successfully wrote {filename}")

# perCapita
filename = "F:/Documents/Data/predicted_timeUse_perCapita_tboPPs.parquet"
df_perCapita.write_parquet(filename)
print(f"Successfully wrote {filename}")