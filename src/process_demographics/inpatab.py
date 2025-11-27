import polars as pl
import src.utils.helpers as helpers

from config.file_paths import inpatab_loc as file_loc

if not file_loc.exists():
    raise FileNotFoundError(f"The file does not exist: {file_loc}")


# LOAD DATA --------------------------------------------------------------------

def load_data(features):
    lf = helpers.load_lf(file_loc, features)

    df = lf.collect()

    print(df)

    return df





def aggregate_data(df, by = "HUISHOUDNR"):
    # function to aggregate personal to household income

    df_hh = (
        df
        .group_by(by)
        .agg(
            pl.col("INPPERSINK").sum().alias("HHINK")
        )
    )

    df = df.join(df_hh, on = by, how = "left")

    return df