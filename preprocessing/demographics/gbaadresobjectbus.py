import polars as pl



# LOAD DATA --------------------------------------------------------------------


def load_data(ref_dates = None):
    # file location
    file = "Bevolking/GBAADRESOBJECTBUS/GBAADRESOBJECT2015BUSV1"

    file_loc = "G:/" + file + ".csv"

    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "GBADATUMAANVANGADRESHOUDING": pl.String,
                        "GBADATUMEINDEADRESHOUDING": pl.String,
                        "RINOBJECTNUMMER": pl.String}


    year_start = pl.date(2015, 1, 1)
    year_end = pl.date(2015, 12, 31)

    # build lazy dataframe pipeline
    df = (
        pl.scan_csv(file_loc, schema_overrides = schema_specified)

        # select relevant columns
        .select(schema_specified.keys())

        # convert to date
        .with_columns(
            [pl.col("GBADATUMAANVANGADRESHOUDING").str.strptime(pl.Date, format = "%Y%m%d"),
            pl.col("GBADATUMEINDEADRESHOUDING").str.strptime(pl.Date, format = "%Y%m%d")]
        )

        # filter dates
        .filter(
            (pl.col("GBADATUMAANVANGADRESHOUDING") <= year_end) &     # start before or in 2015
            (pl.col("GBADATUMEINDEADRESHOUDING") >= year_start)         # end in or after 2015
        )

        # join with reference dataframe
        .join(ref_dates.lazy(), on = "RINPERSOON", how = "inner")
        
        # clamp GBADATUMAANVANGADRESHOUDING and GBADATUMEINDEADRESHOUDING to reference dates from household
        .with_columns(
            GBADATUMAANVANGADRESHOUDING = pl.max_horizontal(pl.col("GBADATUMAANVANGADRESHOUDING"), pl.col("DATUMAANVANGHH")),
            GBADATUMEINDEADRESHOUDING = pl.min_horizontal(pl.col("GBADATUMEINDEADRESHOUDING"), pl.col("DATUMEINDEHH"))
        )

        # calculate duration of address per person within household reference dates
        .with_columns(
            duration = (pl.col("GBADATUMEINDEADRESHOUDING") - pl.col("GBADATUMAANVANGADRESHOUDING")).dt.total_days()
        )

        # per person, keep the SES with the longest duration
        .sort(["RINPERSOON", "duration"],
            descending = [False, True])
        .unique(subset = ["RINPERSOON"], keep = "first")

        # drop columns that are not needed anymore
        .drop(["DATUMAANVANGHH", "DATUMEINDEHH", "GBADATUMAANVANGADRESHOUDING", "GBADATUMEINDEADRESHOUDING", "duration"])
        

        # load in dataframe
        .collect()
    )


    print(df)

    return df

