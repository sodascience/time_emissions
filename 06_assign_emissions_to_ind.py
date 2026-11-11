# NOTE
# This script needs the weighted mapping table of expenditures to time-use
# the mapping table is calculated in the following R-Script:
# F:\Documents\time_emissions\src\input_output_analysis\calc__mapping_exp_timeuse_weighted.R
# please first run that script before running this one








from src.input_output_analysis.assign_emissions import *
from config.surveys import *


# expenditure sample
for exp_model in (None, Surveys.EXPENDITURES.model, Surveys.EXPENDITURES.baseline):
    for time_model in (Surveys.TIMEUSE.model, Surveys.TIMEUSE.baseline):
        household_path = get_household_path(exp_model, survey_sample = Surveys.EXPENDITURES)
        if not household_path.exists():
            write_household_emissions(household_path, exp_model, survey_sample = Surveys.EXPENDITURES)
        output_folder = get_individual_folder(household_path, time_model, survey_sample = Surveys.EXPENDITURES)
        write_individual_emissions(household_path = household_path, time_model = time_model, output_folder = output_folder, survey_sample = Surveys.EXPENDITURES)

# population
for year in YEARS:
    household_path = get_household_path(Surveys.EXPENDITURES.model, year = year)
    if not household_path.exists():
        write_household_emissions(household_path, Surveys.EXPENDITURES.model, year = year)
    output_folder = get_individual_folder(household_path, Surveys.TIMEUSE.model, year = year)
    write_individual_emissions(household_path = household_path, time_model = Surveys.TIMEUSE.model, output_folder = output_folder, year = year)