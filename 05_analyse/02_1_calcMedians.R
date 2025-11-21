library(tidyverse)
library(nanoparquet)
library(paletteer)
library(xlsx)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")

df_time_ML <- read_parquet("F:/Documents/Data/predicted_timeUse_ML_budgetPPs.parquet") %>%
  groupActivities(output_days = 1) 

df_time_baseline <- read_parquet("F:/Documents/Data/predicted_timeUse_baseline_budgetPPs.parquet") %>%
  groupActivities(output_days = 1) 

df_time_perCapita <- read_parquet("F:/Documents/Data/predicted_timeUse_perCapita_budgetPPs.parquet") %>%
  groupActivities(output_days = 1) 

df_emissions_ML <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_ML_perActivity.parquet") %>%
  groupActivities(output_days = 1)

df_emissions_baseline <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_baseline_perActivity.parquet") %>%
  groupActivities(output_days = 1)

df_emissions_perCapita <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_perCapita_perActivity.parquet") %>%
  groupActivities(output_days = 1)

df_intensity_ML <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_ML.parquet")

df_intensity_baseline <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_baseline.parquet")

df_intensity_perCapita <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_perCapita.parquet")



# read demographics
df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet")
df_demographics <- df_demographics %>%
  subset(RINPERSOON %in% df_emissions_ML$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"))




# turn into longer dataframes
df_time_ML_long <- df_time_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "hours_ML") %>%
  mutate(category = factor(category, levels = unique(category)))

df_time_baseline_long <- df_time_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "hours_baseline") %>%
  mutate(category = factor(category, levels = unique(category)))

df_time_perCapita_long <- df_time_perCapita %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "hours_perCapita") %>%
  mutate(category = factor(category, levels = unique(category)))

df_emissions_ML_long <- df_emissions_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "emissions_ML") %>%
  mutate(category = factor(category, levels = unique(category)))

df_emissions_baseline_long <- df_emissions_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "emissions_baseline") %>%
  mutate(category = factor(category, levels = unique(category)))

df_emissions_perCapita_long <- df_emissions_perCapita %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "emissions_perCapita") %>%
  mutate(category = factor(category, levels = unique(category)))

df_intensity_ML_long <- df_intensity_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "intensity_ML") %>%
  mutate(category = factor(category, levels = unique(category)))

df_intensity_baseline_long <- df_intensity_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "intensity_baseline") %>%
  mutate(category = factor(category, levels = unique(category)))

df_intensity_perCapita_long <- df_intensity_perCapita %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "intensity_perCapita") %>%
  mutate(category = factor(category, levels = unique(category)))



df_ML <- df_time_ML_long %>%
  inner_join(df_emissions_ML_long) %>%
  inner_join(df_intensity_ML_long) %>%
  inner_join(df_demographics)

df_baseline <- df_time_baseline_long %>%
  inner_join(df_emissions_baseline_long) %>%
  inner_join(df_intensity_baseline_long) %>%
  inner_join(df_demographics)

df_perCapita <- df_time_perCapita_long %>%
  inner_join(df_emissions_perCapita_long) %>%
  inner_join(df_intensity_perCapita_long) %>%
  inner_join(df_demographics)



df <- df_baseline %>%
  inner_join(df_ML) %>%
  inner_join(df_perCapita) %>%
  pivot_longer(cols = c(hours_perCapita, hours_baseline, hours_ML, 
                        emissions_perCapita, emissions_baseline, emissions_ML, 
                        intensity_perCapita, intensity_baseline, intensity_ML), 
               names_to = c(".value", "model"), 
               names_sep = "_") 


df_sum <- df %>%
  group_by(GBAGESLACHT, category, model) %>%
  summarize(median_hours = median(hours, na.rm = TRUE),
            median_emissions = median(emissions, na.rm = TRUE),
            median_intensity = median(intensity, na.rm = TRUE)) %>%
  ungroup() %>%
  mutate(category = fct_rev(category),
         model = factor(model, levels = c("perCapita", "baseline", "ML")))



# save data
write_parquet(df_sum, "F:/Documents/Data/medians_gender.parquet")
write.xlsx(df_sum, 
           file = "F:/Documents/Data/medians_gender.xlsx",
           sheetName = "medians")
