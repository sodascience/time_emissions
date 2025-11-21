require(tidyverse)
require(foreign)
require(readxl)
require(data.table)
require(nanoparquet)

options(scipen = 999)

models <- c("baseline", "ML") # "perCapita")


##### read data #####
# read emissions per household
df_co2_households <- read_parquet("F:/Documents/Data/carbonEmissions_households.parquet")


# create matching df to match RINPERSOON to RINPERSOONHKW
df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet") %>%
  select(RINPERSOON, RINPERSOONHKW, GBAGEBOORTEJAAR) 


for(model in models){
  # read time per individual
  filename <- paste0("F:/Documents/Data/predicted_timeUse_", model, "_budgetPPs.parquet")
  df_time_individuals <- read_parquet(filename)
  row.names(df_time_individuals) <- df_time_individuals$RINPERSOON
  
  df_demographics <- df_demographics %>%
    subset(RINPERSOON %in% df_time_individuals$RINPERSOON)
  
  
  # calculate time-use per household
  # add RINPERSOONHKW to df_time_individuals to then aggregate per household
  df_time_individuals <- left_join(df_time_individuals, df_demographics)
  
  # set time-use to 0 for children < 10 years
    # a) because children < 10 did not participate in TBO survey
    # b) because children < 10 cannot really choose what they do
    # Their emissions will be distributed to all other HH members (assuming that they care for these children)
  df_time_individuals <- df_time_individuals %>%
    mutate(across(starts_with("activity_"),
                  ~ if_else(GBAGEBOORTEJAAR > 2005, 0, .)))
    
  
  df_time_households <- df_time_individuals %>%
    group_by(RINPERSOONHKW) %>%
    summarize(across(
      where(is.numeric),
      ~ sum(.x, na.rm = TRUE),
      .names = "{.col}"
    )) %>%
    ungroup()
  
  row.names(df_time_households) <- df_time_households$RINPERSOONHKW
  
  # some RINPERSOONHKWs from df_co2_households are missing in df_demographics
  # so, I will delete these and only keep RINPERSOONs from households where RINPERSOONHKW is in df_demographics
  df_co2_households <- df_co2_households %>%
    subset(RINPERSOONHKW %in% df_demographics$RINPERSOONHKW)
  
  # only keep those RINPERSOONHKWs in df_time_individuals that are also in df_co2_households
  df_time_individuals <- df_time_individuals %>%
    subset(RINPERSOONHKW %in% df_co2_households$RINPERSOONHKW)
    
  
  
  
  
  # read mapping of expenses to time
  df_mapping <- read.csv("F:/Documents/Data/mapping_budget-TBO_noRegression_oneHomeVar.csv")
  row.names(df_mapping) <- NULL
  
  
  
  
  
  ##### calculate relative time #####
  
  # extend household dataframe to match the size of df_time_individuals
  df_time_households_extended <- df_demographics %>%
    inner_join(df_time_households, by = "RINPERSOONHKW") %>%
    subset(RINPERSOONHKW %in% df_co2_households$RINPERSOONHKW)
  
  # calculate the relative time-use spent on activities by each hh member
  df_time_individuals_relative <- df_time_individuals %>% 
    select(starts_with("activity")) %>%
    mutate(across(
      where(is.numeric), 
      ~replace_na(. / df_time_households_extended[[cur_column()]], 0)))
    
    
  
  
  ##### calculate individual carbon emissions #####
  
  # time-use is time spent on activities per week
  # CO2 emissions are per year
  # so, I will convert emissions to per week (easier to interpret)
  # I do this with the matrix to only have numerical columns
  
  # turn into matrices
  matrix_co2_households <- (as.matrix(df_co2_households %>% select(starts_with("BOBEST")))
                            / 365 * 7) # emissions per week
  matrix_mapping <- as.matrix(df_mapping %>% select(starts_with("activity")))
  
  # perform matrix multiplications to get individual relative expenditures
  df_co2_households_perActivities <- matrix_co2_households %*% matrix_mapping
  df_co2_households_perActivities <- as.data.frame(df_co2_households_perActivities)
  
  # extend df_co2_households_perActivities to match size of df_time_individuals_relative
  df_co2_households_perActivities$RINPERSOONHKW <- as.character(df_co2_households$RINPERSOONHKW)
  df_co2_households_perActivities_extended <- df_demographics %>%
    inner_join(df_co2_households_perActivities, by = "RINPERSOONHKW")
  row.names(df_co2_households_perActivities_extended) <- df_co2_households_perActivities_extended$RINPERSOON
  df_co2_households_perActivities_extended <- df_co2_households_perActivities_extended %>% select(starts_with("activity"))
  
  
  # multiply df_co2_households_perActivities with relative time-use
  df_co2_individuals_perActivity <- df_co2_households_perActivities_extended * df_time_individuals_relative
  row.names(df_co2_individuals_perActivity) <- row.names(df_co2_households_perActivities_extended)
  
  df_co2_individuals_perActivity$RINPERSOON <- row.names(df_co2_households_perActivities_extended)
  
  
  
  
  
  # save as csv
  filename <- paste0("F:/Documents/Data/carbonEmissions_individuals_", model, "_perActivity.csv")
  write.csv(df_co2_individuals_perActivity, filename, 
            na = "0")
  
  
  filename <- paste0("F:/Documents/Data/carbonEmissions_individuals_", model, "_perActivity.parquet")
  write_parquet(df_co2_individuals_perActivity, filename)
  
  
  
  
  
  
  # CALCULATE INTENSITIES --------------------------------------------------------
  
  # group activities
  
  source("F:/Documents/R_code/groupActivities.R")
  df_co2_individuals_superactivities <- groupActivities(df_co2_individuals_perActivity)
  
  df_time_individuals_superactivities <- groupActivities(df_time_individuals)
  
  # save as csv
  filename <- paste0("F:/Documents/Data/carbonEmissions_individuals_", model, "_perSuperactivity.csv")
  write.csv(df_co2_individuals_superactivities, filename, 
            na = "0")
  
  
  filename <- paste0("F:/Documents/Data/carbonEmissions_individuals_", model, "_perSuperactivity.parquet")
  write_parquet(df_co2_individuals_superactivities, filename)
  
  
  
  
  
  # calculate intensity per superactivity per individual
  df_intensity_individuals <- (df_co2_individuals_superactivities %>% select(!RINPERSOON)) / (df_time_individuals_superactivities %>% select(!RINPERSOON))
  df_intensity_individuals$RINPERSOON <- df_time_individuals$RINPERSOON
  
  # save as csv
  filename <- paste0("F:/Documents/Data/carbonIntensity_individuals_", model, ".csv")
  write.csv(df_intensity_individuals, filename)
  
  filename <- paste0("F:/Documents/Data/carbonIntensity_individuals_", model, ".parquet")
  write_parquet(df_intensity_individuals, filename)
  
  
  
}
