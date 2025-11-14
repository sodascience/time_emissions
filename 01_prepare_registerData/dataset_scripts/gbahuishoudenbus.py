import polars as pl

import pyreadstat




# LOAD DATA --------------------------------------------------------------------

def load_data(file_type = "csv"):
    # file location
    file_loc = "G:/Bevolking/GBAHUISHOUDENSBUS/GBAHUISHOUDENS2015BUSV1." + file_type


    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "HUISHOUDNR" : pl.String,
                        "DATUMAANVANGHH": pl.String,
                        "DATUMEINDEHH": pl.String,
                        "TYPHH": pl.Categorical,            # type huishouden
                        "PLHH" : pl.Categorical,            # plaats van persoon in huishouden
                        "AANTALPERSHH" : pl.Int64,          # aantal personen in huishouden
                        "AANTALKINDHH" : pl.Int64,          # aantal kinderen in huishouden
                        "GEBJAARJONGSTEKINDHH" : pl.Int64,  # geboortejaar jongste kind in huishouden
                        "GEBJAAROUDSTEKINDHH" : pl.Int64}   # geboortejaar oudste kind in huishouden


    year_start = pl.date(2015, 1, 1)
    year_end = pl.date(2015, 12, 31)

    # if people belong to multiple households in one year, 
    # select the household that existed for the longest within the ref year


    # build lazy dataframe pipeline

    if file_type == "sav":
        df = pyreadstat.read_sav(file_loc, output_format = "polars")[0]

        print(df)

        lf = (
            df.lazy()
            
            # specify schema
            .with_columns([
                pl.col(col).cast(dtype) for col, dtype in schema_specified.items() if col in lf.columns    
            ])
        )
        
    else:
        lf = pl.scan_csv(file_loc, schema_overrides = schema_specified)

        
    df = (
        # select relevant columns
        lf.select(schema_specified.keys())

        # convert start & end of household to date
        .with_columns(
            [pl.col("DATUMAANVANGHH").str.strptime(pl.Date, format = "%Y%m%d"),
            pl.col("DATUMEINDEHH").str.strptime(pl.Date, format = "%Y%m%d")]
        )

        # keep households that span 2015
        .filter(
            (pl.col("DATUMAANVANGHH") <= year_end) &            # start before or in 2015
            (pl.col("DATUMEINDEHH") >= year_start)              # end in or after 2015
        )

        # clamp to 2015 window
        .with_columns(
            DATUMAANVANGHH = pl.max_horizontal(pl.col("DATUMAANVANGHH"), year_start),
            DATUMEINDEHH = pl.min_horizontal(pl.col("DATUMEINDEHH"), year_end)
        )

        # calculate duration of household membership per person
        .with_columns(
            duration = (pl.col("DATUMEINDEHH") - pl.col("DATUMAANVANGHH")).dt.total_days()
        )

        # per person, keep the household with the longest duration
        .sort(["RINPERSOON", "duration"],
            descending = [False, True])
        .unique(subset = ["RINPERSOON"], keep = "first")

        # drop columns that are not needed anymore
        .drop(["duration"])
        
        # load in dataframe
        .collect()
    )

    print("Successfully read in the following dataframe:")
    print(df)

    return df

