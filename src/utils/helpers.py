import polars as pl
import pyreadstat
from pathlib import Path
# import csv
# import json


# def specify_dtypes(file_loc: str, startswith_str: str, dtype = pl.Float64):
#     """
#     Reads column names and specifies the most common dtype for all columns starting with startswith_str

#     Args:
#         file_loc:       file location string
#         startswith_str: specifies how column names of most common dtype start 
#         dtype:          polars datatype of most common column dtype (defaults to pl.Float64)
#     """

#     # read column names
#     with open(file_loc, "r") as f:
#         header = next(csv.reader(f))

#     # specify datatype for mostly used datatype
#     dtypes = {col: dtype for col in header if col.startswith(startswith_str)}

#     return dtypes


def read_features(survey_name = None):
    features = pl.read_csv(Path("config", "features.csv"),
                           encoding = "latin1",
                           ignore_errors = True)
    
    if survey_name is not None:
        features = features.filter(pl.col(survey_name))

    # turn into dictionary
    variables = features["variable"]
    dtypes = [getattr(pl, dtype) for dtype in features["dtype"]] # turn string into pl dtype

    features_dict = dict(zip(variables, dtypes))

    return features_dict




def select_demo_features(df, survey):
    # get features relevant for survey
    features_survey = [feature for feature in survey.features_ML.keys()]

    # select demographics relevant for survey (and id variable per unit)
    df_survey = (df
                .select([survey.id_var, *features_survey])
                .unique() # only keep unique rows
    )

    print(df_survey)

    from config.file_paths import demo_file_loc
    new_demo_file_loc = demo_file_loc.with_name(f"{demo_file_loc.stem}_{survey.survey_name}{demo_file_loc.suffix}")

    df_survey.write_parquet(new_demo_file_loc)
    print(f"Successfully wrote {new_demo_file_loc}")

    return(df_survey)





def load_lf(file_loc, features):
    print(f"loading {file_loc} ...")


    if(file_loc.suffix == ".csv"):
        existing_vars = pl.scan_csv(file_loc).collect_schema().names()

    if(file_loc.suffix == ".sav"):
        existing_vars = pyreadstat.read_sav(file_loc)[1].column_names

    print(f"The following variables exist in {file_loc}: {existing_vars}")

    # specify schema to be read
    # select feature labels that can be retrieved from the current dataset (existing_vars)
    schema_specified = {var: dtype for (var, dtype) in features.items() if var in existing_vars}
    
    print(f"Loading the following schema: {schema_specified}")


    # build lazy dataframe pipeline
    if(file_loc.suffix == ".csv"):
        lf = pl.scan_csv(file_loc, schema_overrides = schema_specified)

    if(file_loc.suffix == ".sav"):
        lf = (
            pyreadstat.read_sav(file_loc,
                                output_format = "polars")[0].lazy()

            # specify schema
            .with_columns([
                # loop through each var and cast the desired dtype
                pl.col(col).cast(dtype) if dtype != pl.Boolean else (pl.col(col) == "1").alias(col)
                for col, dtype in schema_specified.items()
            ])
        )


    # select relevant columns
    lf = lf.select(schema_specified.keys())

    return lf



def print_schema(df: pl.DataFrame, exclude_columns = {}):
    """
    Prints schema of polars DataFrame

    Args:
        df - polars dataframe for which schema should be printed
        exclude_columns - specifies columns to  be excluded in printed schema (e.g. those explicitly specified)
    """
    
    # specify columns to display
    columns = {col: dtype for col, dtype in df.schema.items() if col not in exclude_columns}

    rows = []
    for col, dtype in columns.items():
        # get preview values (the first 5 non-empty values of column in df)
        preview_values = (
            df.select(pl.col(col))  # select column
            .drop_nulls()           # drop null values
            .head(5)                # get first 5 values
            .to_series()
            .to_list()
        )
        # join as a semicolon-separated string
        preview_str = "; ".join(map(str, preview_values))
        # add to rows list
        rows.append({"column": col, "dtype": str(dtype), "preview": preview_str})

    # turn into dataframe for better readability
    schema = pl.DataFrame(rows)

    # specify number of rows and length of strings to be displayed
    with pl.Config(tbl_rows = schema.shape[0], fmt_str_lengths = 500): 
        print(schema)

    return schema




# def update_demographics(df, on_var = "RINPERSOON"):
#     demo_file_loc = "F:/Documents/Data/df_demographics"


#     # get schema of demographics 
#     with open(demo_file_loc + "_schema.json") as f:
#         demo_schema = json.load(f)

#     # read demographics columns
#     cols = pl.read_csv(demo_file_loc + ".csv", n_rows = 0).columns 
    
#     # for each column, list the corresponding dtype and turn it into a dtype object (instead of string)
#     demo_schema = [getattr(pl, demo_schema[c]) for c in cols] 



#     # get actual demographics file
#     df_demographics = pl.read_csv(demo_file_loc + ".csv", schema_overrides = demo_schema) # read demographics file
    
#     # update demographics with current data
#     df_demographics = df_demographics.join(df, on = on_var, how = "left") # join demographics data with data from this file
#     print(df_demographics)

#     # write demographics file
#     df_demographics.write_csv(demo_file_loc + ".csv")
#     print(f"Successfully updated {demo_file_loc}.csv")



#     # also save new df_demographics schema
#     demo_schema = {col: str(dtype) for col, dtype in df_demographics.schema.items()}
#     with open (demo_file_loc + "_schema.json", "w") as f:
#         json.dump(demo_schema, f)
        
#     print(f"Successfully updated {demo_file_loc}_schema.json")


#     return df_demographics

