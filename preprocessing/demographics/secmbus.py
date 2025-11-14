import polars as pl



# LOAD DATA --------------------------------------------------------------------

def load_data(ref_dates):
    # file location
    file = "InkomenBestedingen/SECMBUS/SECMBUS2021V1"

    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "AANVSECM": pl.String,
                        "EINDSECM": pl.String,
                        "SECM": pl.Categorical}


    year_start = pl.date(2015, 1, 1)
    year_end = pl.date(2015, 12, 31)

    # build lazy dataframe pipeline                                                                                                                                                                                                                                          
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified)

        # select relevant columns
        .select(schema_specified.keys())

        # convert to date
        .with_columns(
            [pl.col("AANVSECM").str.strptime(pl.Date, format = "%Y%m%d"),
            pl.col("EINDSECM").str.strptime(pl.Date, format = "%Y%m%d")]
        )

        # filter dates
        .filter( 
            (pl.col("RINPERSOON").is_not_null()) &
            (pl.col("AANVSECM") <= year_end) &            # start before or in 2015
            (pl.col("EINDSECM") >= year_start)              # end in or after 2015
        )

        # join with reference dataframe
        .join(ref_dates.lazy(), on = "RINPERSOON", how = "inner")
        
        # clamp AANVSECM and EINDSECM to reference dates from household
        .with_columns(
            AANVSECM = pl.max_horizontal(pl.col("AANVSECM"), pl.col("DATUMAANVANGHH")),
            EINDSECM = pl.min_horizontal(pl.col("EINDSECM"), pl.col("DATUMEINDEHH"))
        )

        # calculate duration of socio-economic status per person within household reference dates
        .with_columns(
            duration = (pl.col("EINDSECM") - pl.col("AANVSECM")).dt.total_days()
        )

        # per person, keep the SES with the longest duration
        .sort(["RINPERSOON", "duration"],
            descending = [False, True])
        .unique(subset = ["RINPERSOON"], keep = "first")

        # drop columns that are not needed anymore
        .drop(["duration", "DATUMAANVANGHH", "DATUMEINDEHH"])
        

        # load in dataframe
        .collect()
    )


    print(df)

    return df

