import polars as pl
import pathlib

import dataset_scripts.gbahuishoudenbus as gbahuishoudenbus
import dataset_scripts.koppelpersoonhuishouden as koppelpersoonhuishouden
import dataset_scripts.gbapersoontab as gbapersoontab
import dataset_scripts.hoogsteopltab as hoogsteopltab
import dataset_scripts.inpatab as inpatab
import dataset_scripts.secmbus as secmbus
import dataset_scripts.vehtab as vehtab
import dataset_scripts.gbaadresobjectbus as gbaadresobjectbus
import dataset_scripts.energieverbruiktab as energieverbruiktab


import helpers

demo_file_loc = pathlib.Path(__file__).resolve().parents[1]/"data"/"true"/"df_demographics"
demo_file_loc.parent.mkdir(parents = True, exist_ok = True)


# GBAHUISHOUDENBUS -------------------------------------------------------------
# contains all people registered in the Netherlands and their household
# this forms the basis for the demographics for this study

# load data
df = gbahuishoudenbus.load_data(file_type = "csv")




# KOPPELPERSOONHUISHOUDEN ------------------------------------------------------
# connects RINPERSOON with RINPERSOONHKW for all income and expenditure data

df_new = koppelpersoonhuishouden.load_data()

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



# save basics in parquet file --------------------------------------------------
df.write_parquet(demo_file_loc + "_base.parquet")

# read basics
df = pl.read_parquet(demo_file_loc + "_base.parquet")



# reference dates for all other data (start and end of respective household)
df_ref_dates = df.select(["RINPERSOON", "DATUMAANVANGHH", "DATUMEINDEHH"])

print(df.sort(["HUISHOUDNR"]))




# GBAPERSOONTAB ----------------------------------------------------------------
# contains all people registered in the Netherlands and their household

df_new = gbapersoontab.load_data()

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



# HOOGSTEOPLTAB ----------------------------------------------------------------

df_new = hoogsteopltab.load_data()

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



# INPATAB ----------------------------------------------------------------------

df_new = inpatab.load_data()

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



df = inpatab.aggregate_data(df)

print("Successfully aggregated household income")
print(df)



# SECMBUS ----------------------------------------------------------------------

df_new = secmbus.load_data(ref_dates = df_ref_dates)

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



# VEHTAB -----------------------------------------------------------------------

df_new = vehtab.load_data()

df = df.join(df_new, on = "RINPERSOONHKW", how = "left")

print("Successfully merged df and df_new")
print(df)



# GBAADRESOBJECTBUS ------------------------------------------------------------

df_new = gbaadresobjectbus.load_data(ref_dates = df_ref_dates)

df = df.join(df_new, on = "RINPERSOON", how = "left")

print("Successfully merged df and df_new")
print(df)



# ENERGIEVERBRUIKTAB -----------------------------------------------------------

df_new = energieverbruiktab.load_data(ref_dates = df_ref_dates)

df = df.join(df_new, on = "RINOBJECTNUMMER", how = "left")

print("Successfully merged df and df_new")
print(df)



# WRITE DEMOGRAPHICS FILE ------------------------------------------------------

df.write_parquet(demo_file_loc + ".parquet")
print(f"Successfully wrote {demo_file_loc}.parquet")

helpers.print_schema(df)