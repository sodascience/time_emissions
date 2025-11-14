import polars as pl


# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates = None):
    # file location
    file = "InkomenBestedingen/INPATAB/INPA2015TABV4"

    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")


    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        # "RINPERSOONHKW": pl.String,
                        # "INPBELI": pl.Float64, # belastbaar inkomen persoon
                        # "INPEMEZ": pl.Categorical, # Economische zelfstandigheid van de persoon
                        "INPEMFO": pl.Categorical, # Financiële onafhankelijkheid van de persoon
                        "INPKKGEM": pl.Float64, # Gemiddelde koopkracht van de persoon in jaar t-1 en t, in prijspeil van jaar t.
                        # "INPPERSBRUT": pl.Float64, # Persoonlijk bruto inkomen
                        "INPPERSINK": pl.Float64, # Persoonlijk inkomen
                        "INPPINK": pl.Categorical, # Indicator persoon met inkomen
                        # "INPPOSHHK": pl.Categorical, # Positie van de persoon in het huishouden ten opzichte van de hoofdkostwinner
                        "INPSECJ": pl.Categorical,   # Sociaaleconomische categorie op jaarbasis
                        "INPT6325KGB": pl.Float64} # Kindgebonden budget


    # build lazy dataframe pipeline
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified, null_values = "9999999999")
        .select(schema_specified.keys())        # select relevant columns
        .collect()                              # load in dataframe
    )


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

