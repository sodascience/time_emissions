import polars as pl

import pyreadstat


# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates = None):
    # file location
    file = "IndustrieEnergie/ENERGIEVERBRUIKTABZK/ENERGIEVERBRUIK2015TABV1ZK"

    file_loc = "G:/" + file + ".sav"

    print(f"loading {file_loc} ...")


    schema_specified = {
        "RINOBJECTNUMMER": pl.String,
        "STADSW": pl.Boolean, 
        "GAS": pl.Float64, 
        "ELEK": pl.Float64
    }


    # build lazy dataframe pipeline
    df = (
        pyreadstat.read_sav(file_loc, output_format = "polars")[0]
        .select(schema_specified.keys())    # select relevant columns
        .with_columns([
            # loop through each var and cast the desired dtype
            pl.col(col).cast(dtype) if dtype != pl.Boolean else (pl.col(col) == "1").alias(col)
            for col, dtype in schema_specified.items()
        ])
    )


    print(df)

    return df