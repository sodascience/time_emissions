import polars as pl
import src.utils.helpers as helpers

from config.file_paths import secmbus_loc as file_loc
from config.file_paths import ref_year

if not file_loc.exists():
    raise FileNotFoundError(f"The file does not exist: {file_loc}")



# LOAD DATA --------------------------------------------------------------------

def load_data(features, ref_dates):
    # add additional variables to features
    # these variables are used for parsing only
    additional_vars = {"AANVSECM":   pl.String,
                       "EINDSECM":     pl.String}

    features.update(additional_vars)

    lf = helpers.load_lf(file_loc, features)

    year_start = pl.date(ref_year, 1, 1)
    year_end = pl.date(ref_year, 12, 31)

    # build lazy dataframe pipeline                                                                                                                                                                                                                                          
    lf = (
        lf
        
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
    )

    # load in dataframe
    df = lf.collect()

    print(df)

    return df