import polars as pl
import pathlib

model_name = "ML"
# model_name = "baseline"
# model_name = "perCapita"

# READ TBO DATA ----------------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"TBO_aggregated.parquet"

lf_TBO = (
    pl.scan_parquet(save_path)
    .select("RINPERSOON")
)



# READ PREDICTED TIME-USE -------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}.parquet"

df = (
    pl.scan_parquet(save_path)
    .join(lf_TBO, on = "RINPERSOON", how = "semi") # only select RINPERSOONs that are also in lf_TBO
    .collect()
)

print(df)




# SAVE DATA ---------------------------------------------------------------------

save_path = pathlib.Path(__file__).resolve().parents[1]/"data"/"predicted"/f"timeUse_{model_name}_tboPPs.parquet"

df.write_parquet(save_path)
print(f"Successfully wrote {save_path}")