import polars as pl

from config.datasets import *


def _inpa(description: str) -> Variable:
    """A yearly amount of INPATAB, in euros; 9999999999 missing"""
    return Variable(dataset = Datasets.inpatab, dtype = pl.Float64,
                    codebook = {"9999999999": None}, description = description)

def _secm_flag(description: str) -> Variable:
    """A flag of the SECM spells: true in the months of the status, blank otherwise."""
    return Variable(dataset = Datasets.secmbus, dtype = pl.Boolean, codebook = {"": None},
                    description = description)

def _veh(description: str) -> Variable:
    """A part of a household's wealth (vehtab), in euros"""
    return Variable(dataset = Datasets.vehtab, dtype = pl.Float64,
                    codebook = {"99999999999": None}, description = description)


class Variables(Namespace):
    """Every value colun the pipeline reads; each is named after its attribute"""
    kind = Variable

    # --- gbapersoontab --- 
    GBAGESLACHT             = Variable(dataset = Datasets.gbapersoontab, 
                                       dtype = pl.Enum(["man", "woman"]),
                                       codebook = {"1": "man", "2": "woman", "-": None}, 
                                       description = "Gender as registered in the population register. For people who changed their gender, only the last known gender is recorded. People of unknown gender are reccorded as women.")
    
    GBAGEBOORTEJAAR         = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int16, 
                                       codebook = {"----": None}, description = "Year of birth.")
    
    GBAGEBOORTEMAAND        = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int8, 
                                       codebook = {"--": None}, description = "Month of birth.")
    
    GBAGEBOORTEJAARMOEDER   = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int16, 
                                       codebook = {"----": None}, description=  "Year of birth of the mother.")
    
    GBAGEBOORTEMAANDMOEDER  = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int8, 
                                       codebook = {"--": None}, description=  "Month of birth of the mother.")
    
    GBAGEBOORTEJAARVADER    = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int16, 
                                       codebook = {"----": None}, description=  "Year of birth of the father.")
    
    GBAGEBOORTEMAANDVADER   = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Int8, 
                                       codebook = {"--": None}, description=  "Month of birth of the father.")
    
    GBAHERKOMSTGROEPERING   = Variable(dataset = Datasets.gbapersoontab, dtype = pl.Categorical, 
                                       description = "Migration background: For people who are not born in the Netherlands (1st generation migrants), the person's own coutnry of birth is recorded. People born in the Netherlands, but for whom (at least) one parent was born outside of the Netherlands (2nd generation migrants), the mother's (otherwise the father's) country of birth is recorded.")
    
    GBAGENERATIE            = Variable(dataset = Datasets.gbapersoontab, 
                                       dtype = pl.Enum(["none", "first", "second"]), 
                                       codebook = {"0": "none", "1": "first", "2": "second", "-": None}, 
                                       description = "Whether the person has a Dutch background, or a first- or second-generation migration background.")


    # --- gbahuishoudenbus ---
    TYPHH                   = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Categorical,
                                       description = "Type of household, such as single person, married or unmarried couple with or without children, single parent, other or institutional household [the latter is excluded in our data].")

    PLHH                    = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Categorical,
                                       description = "Position of the person in the household, such as child living at home, single person, partner, single parent or member of an institutional household [the latter is excluded in our data].")
    
    AANTALPERSHH            = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int16, 
                                       description = "Number of persons in household.")
    
    AANTALKINDHH            = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int16, 
                                       description = "Number of children living at home, including adopted and stepchildren of any age but not foster children.")
    
    GEBMAANDJONGSTEKINDHH   = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int8, 
                                       codebook = {"--": None}, description = "Birth month of the youngest child living at home.")
    
    GEBJAARJONGSTEKINDHH    = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int16, 
                                       description = "Birth year of the youngest child living at home.")
    
    GEBMAANDOUDSTEKINDHH    = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int8, 
                                       codebook = {"--": None}, description = "Birth month of the oldest child living at home.")
    
    GEBJAAROUDSTEKINDHH     = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Int16, 
                                       description = "Birth year of the oldest child living at home.")
    
    DATUMEINDEHH            = Variable(dataset = Datasets.gbahuishoudenbus, dtype = pl.Date,
                                       description = "End of household spell")


    # --- gbaadresobjectbus ---
    GBADATUMEINDEADRESHOUDING = Variable(dataset = Datasets.gbaadresobjectbus, dtype = pl.Date, 
                                         description = "Date that a household moved away from this address.")


    # --- energieverbruiktab ---
    GAS                     = Variable(dataset = Datasets.energieverbruiktab, dtype = pl.Float64, 
                                       description = "Annual natural gas use of the dwelling in m3.")
    
    ELEK                    = Variable(dataset = Datasets.energieverbruiktab, dtype = pl.Float64, 
                                       description = "Annual electricity use of the dwelling in kWh.")

    STADSW                  = Variable(dataset = Datasets.energieverbruiktab, dtype = pl.Boolean, 
                                       description = "Whether district heating is available at this address.")
    
    # WONINGT                 = Variable(dataset = Datasets.energieverbruiktab, dtype = pl.Categorical, 
    #                                    codebook = {"O": None}, description = "Type of home, such as apartment, house, ...")

    
    # --- hoogsteopltab ---
    OPLNIVSOI2016AGG4HBMETNIRWO     = Variable(dataset = Datasets.hoogsteopltab, 
                                               dtype = pl.Enum(["low", "medium", "high"]), 
                                               codebook = {"1110": "low", "1111": "low", "1112": "low", "1210": "low", "1211": "low", "1212": "low", "1213": "low", "1220": "low", "1221": "low", "1222": "low", 
                                                           "2110": "medium", "2111": "medium", "2112": "medium", "2120": "medium", "2121": "medium", "2130": "medium", "2131": "medium", "2132": "medium", 
                                                           "3110": "high", "3111": "high", "3112": "high", "3113": "high", "3210": "high", "3211": "high", "3212": "high", "3213": "high", 
                                                           "9999": None},
                                               description = "Highest completed level of education in 18 categories (SOI 2016), corrected for education that registers do not observe.")

    # --- secmbus --- 
    SECM                    = Variable(dataset = Datasets.secmbus, 
                                       dtype = pl.Enum(["employee", "dga", "self_employed", "benefits", "sick_disabled",
                                                        "pension", "student", "no_income"]),
                                       codebook = {"11": "employee", "12": "dga", 
                                                   "13": "self_employed", "14": "self_employed", "15": "self_employed",
                                                   "21": "benefits", "22": "benefits", "23": "benefits",
                                                   "24": "sick_disabled", "25": "pension",
                                                   "26": "student", "31": "student", "32": "no_income"},
                                       description = "Main socio-economic category in the month, based on the largest income source and school enrolment.")
    
    XKOPPELWERKNSECM        = _secm_flag("Whether the person works as an employee, in the Netherlands or abroad.")    
    XKOPPELDGASECM          = _secm_flag("Whether the person's main job is a director-major shareholder'.")    
    XKOPPELZELFSTSECM       = _secm_flag("Whether the person has profit from own business.")    
    XKOPPELOVACTIEFSECM     = _secm_flag("Whether the person has income from other work, such as freelance work.")    
    XKOPPELWERKLUITKSECM    = _secm_flag("Whether the person receives an unemployment benefit.")    
    XKOPPELZIEKTEAOSECM     = _secm_flag("Whether the person receives a sickness or disability benefit.")    
    XKOPPELBIJSTANDSECM     = _secm_flag("Whether the person receives social assistance.")    
    XKOPPELSOCVOORZOVSECM   = _secm_flag("Whether the person receives another social provision, such as Wajong or a war pension.")    
    XKOPPELPENSIOENSECM     = _secm_flag("Whether the person receives a pension, including state pension, survivors' benefit and pensions from abroad.")    
    XKOPPELSCHOLSTUDSECM    = _secm_flag("Whether the person is registered as a pupil or student.")
    
    EINDSECM                = Variable(dataset = Datasets.secmbus, dtype = pl.Date,
                                       description = "End of the SECM spell")


    # --- spolisbus ---
    SLNINGLD                = Variable(dataset = Datasets.spolisbus, dtype = pl.Float64, 
                                       description = "Gross cash wage paid by the employer, including employee pension contributions.")
    
    SAANTSV                 = Variable(dataset = Datasets.spolisbus, dtype = pl.Float64, 
                                       description = "Number of social insurance days for which a wage was paid.")
    
    SREGULIEREUREN          = Variable(dataset = Datasets.spolisbus, dtype = pl.Float32,
                                       description = "Approximate hours actually worked, excluding overtime, public holidays, and general and age-related leave days.")
    
    SOVERWERKUREN           = Variable(dataset = Datasets.spolisbus, dtype = pl.Float32, 
                                       description = "Extra hours worked on top of the usual hours and paid at a higher hourly rate.")
    
    SREISK                  = Variable(dataset = Datasets.spolisbus, dtype = pl.Float64, 
                                       description = "Tax-free travel allowance from the employer for business trips and commuting.")
    
    SAUTOVANDEZAAK          = Variable(dataset = Datasets.spolisbus, dtype = pl.Int8,
                                       description = "Whether the employee has a company car available for private use.")
    
    SCONTRACTSOORT          = Variable(dataset = Datasets.spolisbus, 
                                       dtype = pl.Enum(["temporary", "permanent"]),
                                       codebook = {"B": "temporary", "O": "permanent", "N": None}, 
                                       description = "Whether the employee has a fixed-term (temporary) or permanent contract.")
    
    SSOORTBAAN              = Variable(dataset = Datasets.spolisbus, dtype = pl.Categorical, 
                                       description = "Type of job, such as director-major shareholder, intern, temporary agency worker or on-call worker.")
    
    SCDINCINKVERM           = Variable(dataset = Datasets.spolisbus, 
                                       dtype = pl.Enum(["pregnancy", "birth", "unpaid", "strike", "sickness"]), 
                                       codebook = {"B": "pregnancy", "G": "birth", "O": "unpaid", "S": "strike", "Z": "sickness", "-": None}, 
                                       description = "Reason why the wage is temporarily lower than agreed, such as unpaid leave or sickness.")
    
    SDATUMEINDEIKO          = Variable(dataset = Datasets.spolisbus, dtype = pl.Date, format = "%Y%m%d",
                                       description = "End of the payroll period")
    

    # --- inpatab ---

    # yearly amounts, spread over the months in features.py
    INPT5210WW              = _inpa("Gross unemployment insurance benefit (WW).")
    INPT5220WA              = _inpa("Gross unemployment benefit for civil servants (wachtgeld).")    
    INPT5230ZW              = _inpa("Gross sickness benefit (ZW) paid directly by the benefit agency, as most sickness pay runs through the wage.")    
    INPT5240AO              = _inpa("Gross disability insurance benefit (WAO, WIA and WAZ).")    
    INPT5250AOP             = _inpa("Gross disability insurance benefit from personal insurances.")    
    INPT5260AOW             = _inpa("Gross state old-age pension (AOW).")    
    INPT5270AWW             = _inpa("Gross survivors' benefit (ANW).")    
    INPT5280PEN             = _inpa("Supplementary pensions and annuities, including pensions paid from abroad.")    
    INPT6290ABW             = _inpa("Gross social assistance benefit (bijstand).")    
    INPT6300DIV             = _inpa("Other social provisions, such as benefits for young disabled people (Wajong), older unemployed workers (IOAW, IOAZ) and war pensions.")
    INPT6330STU             = _inpa("Student grant for students aged 18 and over")
    INPT1060OVE             = _inpa("Income from work outside an employment contract, such as freelance work, after costs.")
    INPT2070WIN             = _inpa("Profit from own business.")
    INPYBIT2410P            = _inpa("Wages from current employment abroad, as reported in the income tax return.")
    INPT8370ONT             = _inpa("Alimony received from an ex-partner (child support is not observed).")
    INPT6320KB              = _inpa("Universal child benefit, recorded on the child's own record.")

    # received by one member for the whole household
    INPT3080REN             = _inpa("Interest received on savings and bank accounts. [only to be used at household level]")
    INPT3100OBL             = _inpa("Interest received on bonds, minus interest paid when buying them. [only to be used at household level]")
    INPT3110DAB             = _inpa("Dividends from a substantial shareholding of at least 5% in a company. [only to be used at household level]")
    INPT3120DIV             = _inpa("Other dividends received, from Dutch and foreign shares. [only to be used at household level]")
    INPT6325KGB             = _inpa("Income-dependent child budget (kindgebonden budget). [received at the household level]")
    INPT7340HRS             = _inpa("Housing allowance for renters with a low income (huurtoeslag). [received at the household level]")
    INPT7350REW             = _inpa("Government contribution towards the costs of owning a home. [received at the household level]")
    INPT7360TSK             = _inpa("Allowance towards the study costs of children under 18. [received at the household level]")
    
    # yearly totals
    INPPERSBRUT             = _inpa("Personal gross income from work, own business, benefits, and alimony received, excluding child benefits.")
    INPV0390BET             = _inpa("Alimony paid to an ex-partner (child support is not observed).")
    INPV3900INK             = _inpa("Income tax owed over the year, after general tax credits.")


    # --- vehtab ---
    VEHW1000VERH            = _veh("Net wealth, i.e. total assets minus total debts.")
    VEHW1110FINH            = _veh("Financial assets, i.e. bank and savings balances plus bonds and listed shares")
    VEHW1121WONH            = _veh("Value of the owner-occupied home the household lives in.")    
    VEHW1200STOH            = _veh("Total debts, including mortgage, student debt, and other debts.")
    VEHW1210SHYH            = _veh("Mortgage debt on the owner-occupied home, minus capital already saved for repayment.")
    
    VEHP100WELVAART         = Variable(dataset = Datasets.vehtab, dtype = pl.Int8, 
                                       codebook = {"-1": None, "-2": None}, 
                                       description = "Percentile group (1-100) of financial welfare, bbased on standardised income and wealth combined.")


    # --- landaktueelref ---
    ETNGRP                  = Variable(dataset = Datasets.landaktueelref, dtype = pl.Categorical,
                                       codebook = {"0": "native", "1": "morocco", "2": "turkey", "3": "suriname", "4": "carribean", "5": "nonwestern", "6": "western", "7": None},
                                       description = "Ethnic grouping of a country")
    


    # --- gas profile ---
    gas_fraction            = Variable(dataset = Datasets.gas_profile, dtype = pl.Float64,
                                       description = "Fraction of yearly gas use per month")


    # --- expenditures survey ---
    BOSTARTDATUM            = Variable(dataset = Datasets.expenditures, dtype = pl.Date,
                                       description = "Start date of expenditure survey")
    
    BOGEWICHT               = Variable(dataset = Datasets.expenditures, dtype = pl.Float64,
                                       description = "Weight of household in expenditure survey")
    

    # --- timeuse survey ---
    invul_datum             = Variable(dataset = Datasets.timeuse, dtype = pl.Date,
                                       description = "Start date of time-use survey.")
    
    tbo_eindgewicht_7dagen  = Variable(dataset = Datasets.timeuse, dtype = pl.Float64,
                                       description = "Weight of household in time-use survey (for those that have completed 7 days)")
