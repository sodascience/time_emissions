import polars as pl
import src.utils.helpers as helpers

from config.file_paths import gbapersoontab_loc as file_loc

if not file_loc.exists():
    raise FileNotFoundError(f"The file does not exist: {file_loc}")



# LOAD DATA --------------------------------------------------------------------

def load_data(features):
    lf = helpers.load_lf(file_loc, features)

    df = lf.collect()

    print(df)

    return(df)