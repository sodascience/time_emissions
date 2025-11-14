import polars as pl

# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates = None):
    file = "Bevolking/GBAPERSOONTAB/2015/GBAPERSOON2015TABV1" 

    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")


    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "GBAGEBOORTELAND": pl.Categorical,          # Geboorteland
                        "GBAGESLACHT" : pl.Categorical,             # Geslacht
                        "GBAGEBOORTEJAAR" : pl.Int64,               # Geboortejaar
                        # "GBAGEBOORTEMAAND" : pl.Categorical,  
                        "GBAHERKOMSTGROEPERING" : pl.Categorical,   # Migratieachtergrond (CBS definitie)
                        "GBAGENERATIE" : pl.Categorical}            # Generatie


    # build lazy dataframe pipeline
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified)
        .select(schema_specified.keys())        # select relevant columns
        .collect()                              # load in dataframe
    )

    print(df)

    return(df)

