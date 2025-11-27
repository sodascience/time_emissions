import polars as pl
import src.utils.helpers as helpers

from config.file_paths import gbahuishoudenbus_loc as file_loc
from config.file_paths import ref_year

if not file_loc.exists():
    raise FileNotFoundError(f"The file does not exist: {file_loc}")



# LOAD DATA --------------------------------------------------------------------

def load_data(features):
    lf = helpers.load_lf(file_loc, features)

    # if people belong to multiple households in one year, 
    # select the household that existed for the longest within the ref year
    
    year_start = pl.date(ref_year, 1, 1)
    year_end = pl.date(ref_year, 12, 31)

    lf = (
        lf
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
            duration = 1 + (pl.col("DATUMEINDEHH") - pl.col("DATUMAANVANGHH")).dt.total_days()
        )

        # per person, keep the household with the longest duration
        .sort(["RINPERSOON", "duration"],
            descending = [False, True])
        .unique(subset = ["RINPERSOON"], keep = "first")

        # drop columns that are not needed anymore
        .drop(["duration"])
    )

    df = lf.collect()

    print("Successfully read in the following dataframe:")
    print(df)

    return df