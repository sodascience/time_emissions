import polars as pl




# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates = None):
    # file location
    file = "Onderwijs/HOOGSTEOPLTAB/2015/HOOGSTEOPL2015TABV3"

    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "OPLNIVSOI2016AGG4HGMETNIRWO": pl.Categorical}              # opleidingsniveau (SOI 2016) in 18 categorieen


    # build lazy dataframe pipeline
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified)
        
        # select relevant columns
        .select(["RINPERSOON", 
                 "OPLNIVSOI2016AGG4HGMETNIRWO"])

        # load in dataframe
        .collect()
    )


    print(df)

    return df
