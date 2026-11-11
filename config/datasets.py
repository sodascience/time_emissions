from pathlib import Path

from config.units import *

RAW = Path("G:/")
CACHE = Path("H:/Maike/processed_data/cache")
OUT = Path("H:/Maike/processed_data")


class Datasets(Namespace):
    """Every delivered file; Datasets.all() lists them"""
    kind = Dataset
    
    # yearly tables - one file per year, named per delivery
    gbapersoontab = Dataset(
        unit = PERSON | YEAR,
        files = {2015: "Bevolking/GBAPERSOONTAB/2015/GBAPERSOON2015TABV1.csv",
                 2016: "Bevolking/GBAPERSOONTAB/2016/GBAPERSOONTAB2016V1.csv"},
        description = "Individual-level dataset with demographic information on all individuals in the Netherlands"
    )

    koppelpersoonhuishouden = Dataset(
        unit = PERSON | BREADWINNER | YEAR,
        files = {2015: "InkomenBestedingen/KOPPELPERSOONHUISHOUDEN/KOPPELPERSOONHUISHOUDEN2015.sav",
                 2016: "InkomenBestedingen/KOPPELPERSOONHUISHOUDEN/KOPPELPERSOONHUISHOUDEN2016.sav"},
        description = "Linkage dataset to link individuals to household breadwinners"
    )

    hoogsteopltab = Dataset(
        unit = PERSON | YEAR,
        files = {2015: "Onderwijs/HOOGSTEOPLTAB/2015/HOOGSTEOPL2015TABV3.csv",
                 2016: "Onderwijs/HOOGSTEOPLTAB/2016/HOOGSTEOPL2016TABV2.csv"},
        description = "Highest level of education completed"
    )

    inpatab = Dataset(
        unit = PERSON | YEAR,
        files = {2015: "InkomenBestedingen/INPATAB/INPA2015TABV4.csv",
                 2016: "InkomenBestedingen/INPATAB/INPA2016TABV5.csv"},
        description = "Income of individuals"
    )

    vehtab = Dataset(
        unit = BREADWINNER | YEAR,
        files = {2015: "InkomenBestedingen/VEHTAB/VEH2015TABV2.csv",
                 2016: "InkomenBestedingen/VEHTAB/VEH2016TABV3.csv"},
        description = "Household wealth"
    )

    energieverbruiktab = Dataset(
        unit = ADDRESS | YEAR,
        files = {2015: "IndustrieEnergie/ENERGIEVERBRUIKTABZK/ENERGIEVERBRUIK2015TABV1ZK.sav",
                 2016: "IndustrieEnergie/ENERGIEVERBRUIKTABZK/ENERGIEVERBRUIK2016TABV1ZK.sav"},
        description = "Energy usage of private apartments"
    )

    # buses - spells; one cumulative file per delivery, the delivery chosen per survey year
    gbahuishoudenbus = Dataset(
        unit = PERSON | HH_SPELL,
        files = {2015: "Bevolking/GBAHUISHOUDENSBUS/GBAHUISHOUDENS2015BUSV1.csv",
                 2016: "Bevolking/GBAHUISHOUDENSBUS/GBAHUISHOUDENS2016BUSV1.csv"},
        description = "Demographic information on all households in the Netherlands",
        start = "DATUMAANVANGHH",
        end = "DATUMEINDEHH"
    )

    gbaadresobjectbus = Dataset(
        unit = PERSON | ADDRESS_SPELL,
        files = {2015: "Bevolking/GBAADRESOBJECTBUS/GBAADRESOBJECT2015BUSV1.csv",
                 2016: "Bevolking/GBAADRESOBJECTBUS/GBAADRESOBJECT2016BUSV1.csv"},
        description = "Address information of individuals",
        start = "GBADATUMAANVANGADRESHOUDING",
        end = "GBADATUMEINDEADRESHOUDING"
    )

    secmbus = Dataset(
        unit = PERSON | SECM_SPELL,
        files = {2015: "InkomenBestedingen/SECMBUS/SECMBUS2024V1.csv",
                 2016: "InkomenBestedingen/SECMBUS/SECMBUS2024V1.csv"},
        description = "Socio-economic category of individuals",
        start = "AANVSECM",
        end = "EINDSECM"
    )

    spolisbus = Dataset(
        unit = PERSON | JOB_SPELL,
        files = {2015: "Spolis/SPOLISBUS/SPOLISBUS2015V4.parquet",
                 2016: "Spolis/SPOLISBUS/SPOLISBUS2016V4.parquet"},
        description = "Jobs and wages of individuals",
        start = "SDATUMAANVANGIKO",
        end = "SDATUMEINDEIKO"
    )

    # --- reference files ---
    landaktueelref = Dataset(
        unit = Unit(Keys.LAND),
        files = "K:/Utilities/Code_Listings/SSBreferentiebestanden/LANDAKTUEELREFV15.sav",
        description = "Mapping table for countries and ethnic groups"
    )

    gas_profile = Dataset(
        unit = MONTH,
        files = "H:/Maike/raw_data/gas_profile.csv",
        description = "NEDU gas profile (G1A) per month, actual temperatures"
    )


    # --- surveys ---
    expenditures = Dataset(
        unit = PERSON,
        # files = "G:/InkomenBestedingen/BUDGETONDERZOEK/2015/BUDGETONDERZOEK2015V4.sav",
        files = "H:/Maike/processed_data/surveys/EXPENDITURES/responses/responses.parquet",    # processed version of the data; to be exchanged with the raw version once the preprocessing of the survey goes via Python
        description = "expenditure survey"
    )

    timeuse = Dataset(
        unit = PERSON,
        # files = "G:/VrijetijdCultuur/TBO/2016/TBO2016V2.sav",
        files = "H:/Maike/processed_data/surveys/TIMEUSE/responses/responses.parquet",         # processed version of the data; to be exchanged with the raw version once the preprocessing of the survey goes via Python
        description = "time-use survey"
    )



# --- check whether all file paths exist ---
missing = []
for ds in Datasets.all():
    files = ds.files if isinstance(ds.files, dict) else{"all years": ds.files}
    for year, path in files.items():
        path = Path(RAW / path)
        if not path.exists():
            missing.append(f"{ds.name} ({year}): {path}")

if missing:
    lines = "\n".join(missing)
    raise FileNotFoundError(f"Missing dataset files: \n{lines}")