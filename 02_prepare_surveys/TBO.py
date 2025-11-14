import polars as pl

# import pyreadstat
from metasyn import MetaFrame

import helpers


# LOAD DATA --------------------------------------------------------------------

file = "TBO_aggregated"

# file location
file_loc = "F:/Documents/Data/TBO_aggregated.csv"
metaframe_loc = "metaframes/" + file + ".json"

print(f"loading {file_loc} ...")



# specify most common dtype
schema_specified = helpers.specify_dtypes(file_loc, startswith_str = "activity", dtype = pl.Float64)

# specify other dtypes
schema_specified.update({"RINPERSOON" : pl.String,
                         "enq_datum" : pl.String
                        })


# build lazy dataframe pipeline
df = (
    pl.scan_csv(file_loc, schema_overrides = schema_specified)
    .select(schema_specified.keys())        # select relevant columns
    .with_columns([                         # convert enq_datum to date
    pl.col("enq_datum").str.strptime(pl.Date, format = "%d%m%Y")
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
