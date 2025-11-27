import polars as pl
import src.utils.helpers as helpers

from config.file_paths import gbaadresobjectbus_loc as file_loc
from config.file_paths import ref_year

if not file_loc.exists():
    raise FileNotFoundError(f"The file does not exist: {file_loc}")



# LOAD DATA --------------------------------------------------------------------


def load_data(features, ref_dates):
    # add additional variables to features
    # these variables are used for parsing only
    additional_vars = {"GBADATUMAANVANGADRESHOUDING":   pl.String,
                       "GBADATUMEINDEADRESHOUDING":     pl.String}

    features.update(additional_vars)

    lf = helpers.load_lf(file_loc, features)

    year_start = pl.date(ref_year, 1, 1)
    year_end = pl.date(ref_year, 12, 31)

    # build lazy dataframe pipeline                                                                                                                                                                                                                                          
    lf = (
        lf

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
    )

        # load in dataframe
    df = lf.collect()

    print(df)

    return df