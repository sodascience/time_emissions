import polars as pl



# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates = None, household_ids = None):
    file = "InkomenBestedingen/VEHTAB/VEH2015TABV2"

    # file location
    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOONHKW" : pl.String,
                        "VEHW1100BEZH": pl.Float64,         # bezittingen van het huishouden
                        "VEHW1200STOH": pl.Float64,         # schulden van het huishouden
                        "VEHW1121WONH": pl.Float64          # eigen woning van het huishouden
                        # "VEHWVEREXEWH": pl.Float64        # vermogen van het huishouden exclusief eigen woning
                        }
    
    print(schema_specified)


    # build lazy dataframe pipeline
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified, null_values = "99999999999")
        .select(schema_specified.keys()) # select relevant columns

        # # join with household ids
        # .join(household_ids.lazy(), left_on = "RINPERSOONHKW", right_on = "RINPERSOON" , how = "left")
        
        # .sort(["HUISHOUDNR"])

        # load in dataframe
        .collect()
    )


    print(df)


    return df

