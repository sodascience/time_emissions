import polars as pl

# import pyreadstat
from metasyn import MetaFrame

import helpers


# if I had installed pyreadstat...
# file_loc = "G:/InkomenBestedingen/BUDGETONDERZOEK/2015/BUDGETONDERZOEK2015V4.sav"

# df = pd.read_spss(file_loc)
# df = pl.from_pandas(df)


# LOAD DATA --------------------------------------------------------------------

# file location
file = "InkomenBestedingen/BUDGETONDERZOEK/2015/BUDGETONDERZOEK2015V4"

file_loc = "F:/Documents/Data/raw/BUDGETONDERZOEK2015V4.csv"
metaframe_loc = "metaframes/" + file + ".json"

print(f"loading {file_loc} ...")



# specify most common dtype
schema_specified = helpers.specify_dtypes(file_loc, startswith_str = "BOBEST", dtype = pl.Float64)

# specify other dtypes
schema_specified.update({"RINPERSOON" : pl.String,
                         "BOSTARTDATUM" : pl.String,
                         "BOGEWICHT" : pl.Float64})


# build lazy dataframe pipeline
df = (
    pl.scan_csv(file_loc, schema_overrides = schema_specified)
    .select(schema_specified.keys())        # select relevant columns
    .with_columns([                         # convert BOSTARTDATUM to date
    pl.col("BOSTARTDATUM").str.strptime(pl.Date, format = "%Y%m%d")
    ])
    .collect()                              # load in dataframe
)


helpers.print_schema(df)
print(df)




# CREATE SYNTHESIZED DATASET ---------------------------------------------------

# create metaframe with information about df
mf = MetaFrame.fit_dataframe(df)
mf.save(metaframe_loc)
print(mf)

