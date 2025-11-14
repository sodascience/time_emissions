import polars as pl
import pyreadstat


# LOAD DATA --------------------------------------------------------------------

def load_data():
    # file location
    file_loc = "G:/InkomenBestedingen/KOPPELPERSOONHUISHOUDEN/KOPPELPERSOONHUISHOUDEN2015.sav" 

    print(f"loading {file_loc} ...")



    # specify dtypes
    schema_specified = {"RINPERSOON" : pl.String,
                        "RINPERSOONHKW" : pl.String}


    # build lazy dataframe pipeline
    df = (
        pyreadstat.read_sav(file_loc,
                         output_format = "polars")[0].lazy()

        # select relevant columns
        .select(schema_specified.keys())
        
        # load in dataframe
        .collect()
    )

    # helpers.print_schema(df)
    print(df)

    return df
