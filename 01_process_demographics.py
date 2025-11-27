import polars as pl
from pathlib import Path
import src.utils.helpers as helpers

# python scripts to import data from files
# each CBS dataset has it's own script 
# so that dataset specific variables can be parsed correctly
import src.process_demographics.gbahuishoudenbus as gbahuishoudenbus
import src.process_demographics.koppelpersoonhuishouden as koppelpersoonhuishouden
import src.process_demographics.gbapersoontab as gbapersoontab
import src.process_demographics.hoogsteopltab as hoogsteopltab
import src.process_demographics.inpatab as inpatab
import src.process_demographics.secmbus as secmbus
import src.process_demographics.vehtab as vehtab
import src.process_demographics.gbaadresobjectbus as gbaadresobjectbus
import src.process_demographics.energieverbruiktab as energieverbruiktab



# CONFIG -----------------------------------------------------------------------

# save paths for demographics file
demo_file_loc = Path("processed_data", "true", "demographics.parquet")
demo_file_loc.parent.mkdir(parents = True, exist_ok = True)



# READ FEATURES -----------------------------------------------------------------
features_dict = helpers.read_features()




# LOAD DATA ---------------------------------------------------------------------

## GBAHUISHOUDENBUS -------------------------------------------------------------
# contains all people registered in the Netherlands and their household
# this forms the basis for the demographics for this study

df = gbahuishoudenbus.load_data(features_dict = features_dict)




## KOPPELPERSOONHUISHOUDEN ------------------------------------------------------
# connects RINPERSOON with RINPERSOONHKW for all income and expenditure data

df_new = koppelpersoonhuishouden.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



## save basics in parquet file --------------------------------------------------

new_demo_file_loc = demo_file_loc.with_name(f"{demo_file_loc.stem}_base{demo_file_loc.suffix}")
df.write_parquet(new_demo_file_loc)

# read basics
df = pl.read_parquet(new_demo_file_loc)



## create df for reference dates ------------------------------------------------
# reference dates for all other data (start and end of respective household)

df_ref_dates = df.select(["RINPERSOON", "DATUMAANVANGHH", "DATUMEINDEHH"])



## GBAPERSOONTAB ----------------------------------------------------------------
# contains all people registered in the Netherlands

df_new = gbapersoontab.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



## HOOGSTEOPLTAB ----------------------------------------------------------------
# contains data on highest education level per person

df_new = hoogsteopltab.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



## INPATAB ----------------------------------------------------------------------
# contains data on personal income

df_new = inpatab.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



# aggregate personal to household income
df = inpatab.aggregate_data(df)
print("Successfully aggregated household income")
print(df)



## SECMBUS ----------------------------------------------------------------------
# contains data on socio-economic status of person

df_new = secmbus.load_data(features_dict = features_dict, ref_dates = df_ref_dates)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



## VEHTAB -----------------------------------------------------------------------
# contains data on personal assets

df_new = vehtab.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINPERSOONHKW", how = "left")
print("Successfully merged df and df_new")
print(df)



## GBAADRESOBJECTBUS ------------------------------------------------------------
# contains data on addresses

df_new = gbaadresobjectbus.load_data(features_dict = features_dict, ref_dates = df_ref_dates)

df = df.join(df_new, on = "RINPERSOON", how = "left")
print("Successfully merged df and df_new")
print(df)



## ENERGIEVERBRUIKTAB -----------------------------------------------------------
# contains data on energy usage (gas, electricity)

df_new = energieverbruiktab.load_data(features_dict = features_dict)

df = df.join(df_new, on = "RINOBJECTNUMMER", how = "left")
print("Successfully merged df and df_new")
print(df)



## WRITE DEMOGRAPHICS FILE ------------------------------------------------------

df.write_parquet(demo_file_loc)
print(f"Successfully wrote {demo_file_loc}")




df = pl.read_parquet(demo_file_loc)
helpers.print_schema(df)

nonexistent_features_dict = {var: dtype for (var, dtype) in features_dict.items() if var not in df.columns}
print(nonexistent_features_dict)


# TODO add functions to add aggregated variables (e.g. household income, number of people with x, ...)



# CREATE DF_DEMOGRAPHICS PER SURVEY --------------------------------

import config.timeuse as survey
helpers.select_demo_features(df, survey)


import config.expenditures as survey
helpers.select_demo_features(df, survey)
