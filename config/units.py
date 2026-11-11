import polars as pl

from src.utils.core import *

class Keys(Namespace):
    """All key columns, by name"""

    kind = Key

    # persons
    RINPERSOON          = Key(dtype = pl.UInt32, description = "Person ID")
    RINPERSOONS         = Key(dtype = pl.Categorical, description = "Person ID type")

    # breadwinners
    RINPERSOONHKW       = Key(dtype = pl.UInt32, description = "Breadwinner ID")
    RINPERSOONSHKW      = Key(dtype = pl.Categorical, description = "Breadwinner ID type")

    # households
    HUISHOUDNR          = Key(dtype = pl.UInt64, description = "Household ID")
    DATUMAANVANGHH      = Key(dtype = pl.Date, description = "Start of the household spell")

    # addresses
    RINOBJECTNUMMER     = Key(dtype = pl.String, description = "Address ID")
    SOORTOBJECTNUMMER   = Key(dtype = pl.Categorical, description = "Address ID Type")
    GBADATUMAANVANGADRESHOUDING = Key(dtype = pl.Date, format = "%Y%m%d", description = "Start of the residence spell")

    # jobs
    IKVID               = Key(dtype = pl.String, description = "Job ID")
    SDATUMAANVANGIKO    = Key(dtype = pl.Date, format = "%Y%m%d",
                              codebook = {"88888888": "{year}0101",    # began before this year
                                          "99999999": None},           # no payments: not a spell
                              description = "Start of the payroll spell")
    
    # secm
    AANVSECM            = Key(dtype = pl.Date, format = "%Y%m%d", description = "Start of the SECM spell")

    # country
    LAND                = Key(dtype = pl.String, description = "Country code")

    # time
    year = Key(dtype = pl.Int16, description = "Calendar year")
    month = Key(dtype = pl.Int8, description = "Calendar month")



# time
YEAR        = Unit(Keys.year)
MONTH       = Unit(Keys.year, Keys.month)

# entities
PERSON      = Unit(Keys.RINPERSOON, Keys.RINPERSOONS)
BREADWINNER = Unit(Keys.RINPERSOONHKW, Keys.RINPERSOONSHKW)
HH_SPELL    = Unit(Keys.HUISHOUDNR, Keys.DATUMAANVANGHH)
ADDRESS     = Unit(Keys.RINOBJECTNUMMER, Keys.SOORTOBJECTNUMMER)
ADDRESS_SPELL = ADDRESS | Unit(Keys.GBADATUMAANVANGADRESHOUDING)
JOB_SPELL   = Unit(Keys.IKVID, Keys.SDATUMAANVANGIKO)
SECM_SPELL  = Unit(Keys.AANVSECM)