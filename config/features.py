import polars as pl

from config.mappings import *
from src.process_demographics.agg_functions import *



class Chains(Namespace):
    kind = Variable

    age = since(Variables.GBAGEBOORTEJAAR, Variables.GBAGEBOORTEMAAND)

    # income: the wage, and each yearly amount of INPATAB spread over the months of its flag
    unemployment_flag       = Variables.XKOPPELWERKLUITKSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    unemployment            = (Variables.INPT5210WW + Variables.INPT5220WA).move(to = PERSON | HH_SPELL | MONTH, 
                                                                                 condition = unemployment_flag, 
                                                                                 weight = COVER, agg_method = SUM)
    
    sickness_flag           = Variables.XKOPPELZIEKTEAOSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    sickness                = (Variables.INPT5230ZW + Variables.INPT5240AO + Variables.INPT5250AOP).move(to = PERSON | HH_SPELL | MONTH, 
                                                                                                         condition = sickness_flag, 
                                                                                                         weight = COVER, agg_method = SUM)
    
    assistance_flag         = Variables.XKOPPELBIJSTANDSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    assistance              = Variables.INPT6290ABW.move(to = PERSON | HH_SPELL | MONTH, 
                                                         condition = assistance_flag, 
                                                         weight = COVER, agg_method = SUM)
    
    social_flag             = Variables.XKOPPELSOCVOORZOVSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    social                  = Variables.INPT6300DIV.move(to = PERSON | HH_SPELL | MONTH, 
                                                         condition = social_flag, 
                                                         weight = COVER, agg_method = SUM)
    
    pension_flag            = Variables.XKOPPELPENSIOENSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    pension                 = (Variables.INPT5260AOW + Variables.INPT5270AWW + Variables.INPT5280PEN).move(to = PERSON | HH_SPELL | MONTH, 
                                                                                                           condition = pension_flag, 
                                                                                                           weight = COVER, agg_method = SUM)
    
    other_work_flag         = Variables.XKOPPELOVACTIEFSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    other_work              = Variables.INPT1060OVE.move(to = PERSON | HH_SPELL | MONTH, 
                                                         condition = other_work_flag, 
                                                         weight = COVER, agg_method = SUM)
    
    student_flag            = Variables.XKOPPELSCHOLSTUDSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    student                 = Variables.INPT6330STU.move(to = PERSON | HH_SPELL | MONTH, 
                                                         condition = student_flag, 
                                                         weight = COVER, agg_method = SUM)
    
    wage_abroad_flag        = Variables.XKOPPELWERKNSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    wage_abroad             = Variables.INPYBIT2410P.move(to = PERSON | HH_SPELL | MONTH, 
                                                          condition = wage_abroad_flag, 
                                                          weight = COVER, agg_method = SUM)
    
    profit_flag             = Variables.XKOPPELZELFSTSECM.move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    profit                  = Variables.INPT2070WIN.move(to = PERSON | HH_SPELL | MONTH, 
                                                         condition = profit_flag, 
                                                         weight = COVER, agg_method = SUM)
    
    alimony                 = Variables.INPT8370ONT.move(to = PERSON | HH_SPELL | MONTH, 
                                                         weight = COVER, agg_method = SUM)

    wage                    = Variables.SLNINGLD.move(to = PERSON | HH_SPELL | MONTH, agg_method = SUM)
    income_month            = add_up(wage, unemployment, sickness, assistance, social, pension, other_work, student, wage_abroad, profit, alimony)

    # yearly: own income, plus the household-level items
    income_year_household   = (Variables.INPPERSBRUT - Variables.INPV0390BET + sum([
        Variables.INPT3080REN, Variables.INPT3100OBL, Variables.INPT3110DAB, Variables.INPT3120DIV,
        Variables.INPT6325KGB, Variables.INPT7340HRS, Variables.INPT7350REW, Variables.INPT7360TSK]))
    
    # work: self-employed or other active, in any secm spell of the month    
    self_employed           = (Variables.XKOPPELZELFSTSECM | Variables.XKOPPELOVACTIEFSECM).move(to = PERSON | HH_SPELL | MONTH, agg_method = VALUE.any())
    paid_work               = (wage > 0) | self_employed
    
    # dwelling: yearly use, divided by days present
    gas_month               = Variables.GAS.move(to = ADDRESS | MONTH, weight = pl.col("gas_fraction"),
                                                 via = Mappings.MONTHS)
    months_at_address       = since(key_as_value(Datasets.gbaadresobjectbus, Keys.GBADATUMAANVANGADRESHOUDING), in_ = "months", agg_method = VALUE.max())

    # wealth: renter, or owner with or without a mortgage, from the home value and the mortgage debt
    ownership               = Variables.VEHW1121WONH.combine(Variables.VEHW1210SHYH, lambda home, mortgage: (
        pl.when(home.is_null()).then(pl.lit(None, dtype = pl.String))
        .when(home == 0).then(pl.lit("renter"))
        .when(mortgage > 0).then(pl.lit("owner_mortgage"))
        .otherwise(pl.lit("owner_outright"))))



class HouseholdFeatures(Namespace):
    kind = Feature
    unit = HH_SPELL | MONTH


class PersonFeatures(Namespace):
    kind = Feature
    unit = PERSON | HH_SPELL | MONTH



# --- Household composition ---
class CompositionPerson(PersonFeatures):
    position_in_hh          = Feature(Variables.PLHH, description = "Position in the household")


class CompositionHousehold(HouseholdFeatures):
    type_hh                 = Feature(Variables.TYPHH,                      # the data of this variable is at the individual unit, even though the information is about households
                                      agg_method = FIRST,             # therefore, we take the most common value for each household
                                      description = "Type of household")
    
    n_persons_hh            = Feature(Variables.AANTALPERSHH,               # the data of this variable is at the individual unit, even though the information is about households
                                      agg_method = MEAN,                    # therefore, we take the mean value for each household
                                      description = "Number of people living in household")
    
    n_children_hh           = Feature(Variables.AANTALKINDHH,               # the data of this variable is at the individual unit, even though the information is about households
                                      agg_method = MEAN,                    # therefore, we take the mean value for each household
                                      description = "Number of children living in household")
    
    age_youngest_child_hh   = Feature(since(Variables.GEBJAARJONGSTEKINDHH, Variables.GEBMAANDJONGSTEKINDHH),   # the data of this variable is at the individual unit, even though the information is about households
                                      agg_method = MEAN,                                                        # therefore, we take the mean value for each household
                                      description = "Age of youngest child living in household at reference month")
    
    age_oldest_child_hh     = Feature(since(Variables.GEBJAAROUDSTEKINDHH, Variables.GEBMAANDOUDSTEKINDHH),     # the data of this variable is at the individual unit, even though the information is about households
                                      agg_method = MEAN,                                                        # therefore, we take the mean value for each household
                                      description = "Age of oldest child living in household at reference month")


# --- Demography ---
class DemographyPerson(PersonFeatures):
    age                     = Feature(Chains.age, 
                                      description = "Age in completed years at reference month.")

    age_parents_mean        = Feature(mean_of(since(Variables.GBAGEBOORTEJAARMOEDER, Variables.GBAGEBOORTEMAANDMOEDER),
                                              since(Variables.GBAGEBOORTEJAARVADER, Variables.GBAGEBOORTEMAANDVADER)),
                                      description = "Average age of parents of an individual in completed years at reference month.",
                                      batches = 4)
    
    gender                  = Feature(Variables.GBAGESLACHT, 
                                      description = "Registered gender of a person")
    
    country_origin          = Feature(group_countries(Variables.GBAHERKOMSTGROEPERING), 
                                      description = "Country of origin of an individual")
    
    migration_generation    = Feature(Variables.GBAGENERATIE, 
                                      description = "Migration generation")
    

class DemographyHousehold(HouseholdFeatures):
    age_median_hh           = Feature(DemographyPerson.age, 
                                      condition = pl.col("age") >= 25, agg_method = MEDIAN,
                                      description = "Median age of members that are 25 or older")
    
    gender_prop_women       = Feature(DemographyPerson.gender,
                                      condition = pl.col("age") >= 12, agg_method = share("woman"),
                                      description = "Share of women among members that are 12 or older")

    country_origin_morocco      = Feature(DemographyPerson.country_origin,
                                          agg_method = share("morocco"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with Morocco as country of origin")
    
    country_origin_turkey       = Feature(DemographyPerson.country_origin,
                                          agg_method = share("turkey"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with Turkey as country of origin")
    
    country_origin_suriname     = Feature(DemographyPerson.country_origin,
                                          agg_method = share("suriname"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with Suriname as country of origin")
    
    country_origin_carribean    = Feature(DemographyPerson.country_origin,
                                          agg_method = share("carribean"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with the (former) Dutch Carribean islands as country of origin")
    
    country_origin_nonwestern   = Feature(DemographyPerson.country_origin,
                                          agg_method = share("nonwestern"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with a non Western country as country of origin")
    
    country_origin_western      = Feature(DemographyPerson.country_origin,
                                          agg_method = share("western"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                          description = "Share of non-child members with a Western country as country of origin")
    
    migration_generation_1  = Feature(DemographyPerson.migration_generation,
                                      agg_method = share("first"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                      description = "Share of non-child members with migration generation 1")
    
    migration_generation_2  = Feature(DemographyPerson.migration_generation,
                                      agg_method = share("second"), condition = Variables.PLHH != "1",          # not a child of this hh (because children are usually per definition the same country of origin as parents)
                                      description = "Share of non-child members with migration generation 2")
    

# --- Dwelling and energy ---
class DwellingHousehold(HouseholdFeatures):
    gas                     = Feature(Chains.gas_month, 
                                      weight = COVER,
                                      agg_method = SUM,
                                      description = "Gas usage in cubic metres of the household")

    electricity             = Feature(Variables.ELEK,
                                      weight = COVER,
                                      agg_method = SUM,
                                      description = "Electricity usage in kWh of the household")
    
    district_heating        = Feature(variable = Variables.STADSW,
                                      agg_method = VALUE.any(),
                                      description = "Whether district heating is available at this address.")

    # type_home               = Feature(variable = Variables.WONINGT,
    #                                   agg_method = MOST_COMMON,
    #                                   description = "Type of home")
    
    months_at_address       = Feature(Chains.months_at_address,
                                      agg_method = MEDIAN, condition = Variables.PLHH != "1",
                                      description = "Median number of months that the non-child members live at this address.")
    

# --- Education ---
class EducationPerson(PersonFeatures):
    edu_level               = Feature(Variables.OPLNIVSOI2016AGG4HBMETNIRWO,
                                      description = "Educational level of highest completed education.")


class EducationHousehold(HouseholdFeatures):
    edu_level_medium        = Feature(EducationPerson.edu_level,
                                      agg_method = share("medium"), condition = Chains.age >= 25,
                                      description = "Share of members at least 25 years old with highest completed education 'medium'")
    
    edu_level_high          = Feature(EducationPerson.edu_level,
                                      agg_method = share("high"), condition = Chains.age >= 25,
                                      description = "Share of members at least 25 years old with highest completed education 'high'")


# --- Work ---
class WorkPerson(PersonFeatures):
    n_jobs                  = Feature(key_as_value(Datasets.spolisbus, Keys.IKVID),
                                      agg_method = VALUE.n_unique(), fill = 0,
                                      description = "Number of jobs of an individual",
                                      batches = 8)
    
    temp_contract           = Feature(highest_paid(Variables.SCONTRACTSOORT),
                                      "Contract of the highest-paid job",
                                      batches = 4)
    
    type_job                = Feature(highest_paid(Variables.SSOORTBAAN),
                                      description = "Type of the highest-paid job",
                                      batches = 4)
    
    reason_lower_income     = Feature(Variables.SCDINCINKVERM,
                                      agg_method = LONGEST,
                                      description = "Longest reason in the month for a lower wage",
                                      batches = 4)
    
    self_employed           = Feature(Chains.self_employed, fill = False,
                                      description = "Self-employed",
                                      batches = 4)
    
    n_days_worked           = Feature(Variables.SAANTSV.move(to = PERSON | HH_SPELL | MONTH, weight = COVER, agg_method = SUM), fill = 0,
                                      description = "Social insurance days",
                                      batches = 4)
    
    n_hours_worked          = Feature(Variables.SREGULIEREUREN.move(to = PERSON | HH_SPELL | MONTH, weight = COVER, agg_method = SUM), fill = 0,
                                      description = "Regular hours worked",
                                      batches = 4)
    
    n_hours_overtime        = Feature(Variables.SOVERWERKUREN.move(to = PERSON | HH_SPELL | MONTH, weight = COVER, agg_method = SUM), fill = 0,
                                      description = "Overtime hours worked",
                                      batches = 4)
    
    compensated_travel_costs    = Feature(Variables.SREISK.move(to = PERSON | HH_SPELL | MONTH, weight = COVER, agg_method = SUM), fill = 0,
                                          description = "Travel costs reimbursed by employers",
                                          batches = 4)
    
    company_car             = Feature(Variables.SAUTOVANDEZAAK > 0, fill = False,
                                      agg_method = SUM,
                                      description = "Company car for private use",
                                      batches = 4)
    
    ses_category            = Feature(Variables.SECM, 
                                      agg_method = LONGEST,
                                      description = "Longest socio-economic category",
                                      batches = 4)
    

class WorkHousehold(HouseholdFeatures):
    n_people_paidWork       = Feature(Chains.paid_work,
                                      agg_method = SUM, 
                                      description = "Members employed or self-employed",
                                      batches = 4)
    
    temp_contract_share     = Feature(WorkPerson.temp_contract,
                                      agg_method = share("temporary"),
                                      description = "Share of employees with a temporary contract",
                                      batches = 4)
    
    reason_lower_income_unpaid      = Feature(written(WorkPerson.reason_lower_income),
                                              agg_method = count("unpaid"),
                                              description = "Number of members whoms wage is reduced due to unpaid leave")
    
    reason_lower_income_sickness    = Feature(written(WorkPerson.reason_lower_income),
                                              agg_method = count("sickness"),
                                              description = "Number of members whoms wage is reduced due to sickness")
    
    n_days_worked_sum       = Feature(WorkPerson.n_days_worked,
                                      agg_method = SUM,
                                      description = "Sum of social insurance days",
                                      batches = 4)
    
    n_hours_worked_sum      = Feature(WorkPerson.n_hours_worked,
                                      agg_method = SUM,
                                      description = "Sum of regular hours worked",
                                      batches = 4)
    
    n_hours_overtime_sum    = Feature(WorkPerson.n_hours_overtime,
                                      agg_method = SUM,
                                      description = "Sum of overtime hours worked",
                                      batches = 4)
    
    compensated_travel_costs_sum    = Feature(WorkPerson.compensated_travel_costs,
                                              agg_method = SUM,
                                              description = "Sum of travel costs reimbursed by employers",
                                              batches = 4)
    
    company_car_sum         = Feature(WorkPerson.company_car,
                                      agg_method = SUM,
                                      description = "Sum of members with a company car for private use",
                                      batches = 4)
    
    # members per category
    ses_category_dga        = Feature(WorkPerson.ses_category,
                                      agg_method = count("dga"),
                                      description = "Number of household members that are dga",
                                      batches = 4)
    
    ses_category_self_employed  = Feature(WorkPerson.ses_category,
                                          agg_method = count("self_employed"),
                                          description = "Number of household members that are self-employed",
                                          batches = 4)

    ses_category_benefits   = Feature(WorkPerson.ses_category,
                                      agg_method = count("benefits"),
                                      description = "Number of household members that receive benefits",
                                      batches = 4)
    
    ses_category_sick_disabled  = Feature(WorkPerson.ses_category,
                                          agg_method = count("sick_disabled"),
                                          description = "Number of household members that receive social assistance for sickness or disability",
                                          batches = 4)
    
    ses_category_pension    = Feature(WorkPerson.ses_category,
                                      agg_method = count("pension"),
                                      description = "Number of household members that receive pension",
                                      batches = 4)
    
    ses_category_student    = Feature(WorkPerson.ses_category,
                                      agg_method = count("student"),
                                      description = "Number of household members that are student",
                                      batches = 4)
    
    ses_category_no_income  = Feature(WorkPerson.ses_category,
                                      agg_method = count("no_income"),
                                      description = "Number of household members that have no_income",
                                      batches = 4)


# --- income ---
class IncomePerson(PersonFeatures):
    income_month            = Feature(Chains.income_month,
                                      description = "Gross income in the month: wage, and yearly incomes spread",
                                      batches = 16)
    
    income_year             = Feature(Variables.INPPERSBRUT - Variables.INPV0390BET,
                                      description = "Gross income in the year, minus alimony paid",
                                      batches = 4)


class IncomeHousehold(HouseholdFeatures):
    income_month_hh         = Feature(written(IncomePerson.income_month),
                                      agg_method = SUM,
                                      description = "Gross income of all members in the month with the household level incomes")
    
    income_year_hh          = Feature(Chains.income_year_household,
                                      agg_method = SUM,
                                      description = "Gross income of all members in the year",
                                      batches = 4)
    
    housing_allowance       = Feature(Variables.INPT7340HRS,
                                      agg_method = SUM,
                                      description = "Housing allowance per year")
    


# --- wealth ---
class WealthHousehold(HouseholdFeatures):
    home_ownership          = Feature(Chains.ownership.move(to = PERSON | YEAR, agg_method = FIRST),
                                      agg_method = FIRST,
                                      description = "Renter, owner with or without mortgage",
                                      batches = 4)
    
    assets_home             = Feature(Variables.VEHW1121WONH.move(to = PERSON | YEAR, agg_method = FIRST), 
                                      agg_method = FIRST)
    
    debts_home              = Feature(Variables.VEHW1210SHYH.move(to = PERSON | YEAR, agg_method = FIRST),
                                      agg_method = FIRST)
    
    financial_assets        = Feature(Variables.VEHW1110FINH.move(to = PERSON | YEAR, agg_method = FIRST),
                                      agg_method = FIRST)
    
    debts_not_home          = Feature((Variables.VEHW1200STOH - Variables.VEHW1210SHYH).move(to = PERSON | YEAR, agg_method = FIRST),
                                      agg_method = FIRST,
                                      batches = 4)
    
    net_wealth              = Feature(Variables.VEHW1000VERH.move(to = PERSON | YEAR, agg_method = FIRST), 
                                      agg_method = FIRST)
    
    welfare_percentile      = Feature(Variables.VEHP100WELVAART.move(to = PERSON | YEAR, agg_method = FIRST),
                                      agg_method = FIRST)





TABLES          = HouseholdFeatures.__subclasses__() + PersonFeatures.__subclasses__()
TABLE_NAMES     = {HouseholdFeatures.unit:  "household_month",
                   PersonFeatures.unit:     "person_household_month"}

def features_of(unit: Unit) -> list[Feature]:
    """Every feature of one output table, from all theme classes with that unit"""
    return [f for t in TABLES if t.unit == unit for f in t.all()]