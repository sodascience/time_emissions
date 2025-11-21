library(tidyverse)
library(nanoparquet)
library(paletteer)
library(writexl)


source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")

df_time_ML <- read_parquet("F:/Documents/Data/predicted_timeUse_ML_budgetPPs.parquet") %>%
  groupActivities(output_days = 1)

df_time_baseline <- read_parquet("F:/Documents/Data/predicted_timeUse_baseline_budgetPPs.parquet") %>%
  groupActivities(output_days = 1)

df_emissions_ML <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_ML_perActivity.parquet") %>%
  groupActivities(output_days = 1)

df_emissions_baseline <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_baseline_perActivity.parquet") %>%
  groupActivities(output_days = 1)

df_intensity_ML <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_ML.parquet")

df_intensity_baseline <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_baseline.parquet")




df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet") %>%
  subset(RINPERSOON %in% df_emissions_ML$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"),
         TYPHH = as.numeric(TYPHH),
         PLHH = as.numeric(PLHH),
         AANTALKINDHH = as.factor(AANTALKINDHH),
         type_hh = case_when(
           TYPHH == "1" ~ "One-person household",
           TYPHH %in% c("2", "3") ~ "Couple (no children)",
           TYPHH %in% c("4", "5") ~ "Couple (with children)",
           TYPHH %in% "6" ~ "One-parent household",
           TYPHH %in% c("7", "8") ~ "Other/Institutional household"
         ),
         position_hh = case_when(
           PLHH == "1" ~ "Child",
           PLHH == "2" ~ "Adult in one-person household",
           PLHH %in% c("3", "4") ~ "Adult in couple (no children)",
           PLHH %in% c("5", "6") ~ "Adult in couple (with children)",
           PLHH %in% "7" ~ "Adult in one-parent household",
           PLHH %in% c("7", "8") ~ "Adult in other/institutional household"
         )) %>%
  mutate(type_hh = factor(type_hh, levels = unique(type_hh)),
         position_hh = factor(position_hh, levels = unique(position_hh)))





df_time_ML_long <- df_time_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "time_ML") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)

df_time_baseline_long <- df_time_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "time_baseline") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)

df_emissions_ML_long <- df_emissions_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "emissions_ML") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)

df_emissions_baseline_long <- df_emissions_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "emissions_baseline") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)

df_intensity_ML_long <- df_intensity_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "intensity_ML") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)

df_intensity_baseline_long <- df_intensity_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "intensity_baseline") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics)






df_time_long <- df_time_ML_long %>%
  inner_join(df_time_baseline_long) %>%
  pivot_longer(c(time_ML, time_baseline), names_to = c(".value", "model"), names_sep = "_")

df_emissions_long <- df_emissions_ML_long %>%
  inner_join(df_emissions_baseline_long) %>%
  pivot_longer(c(emissions_ML, emissions_baseline), names_to = c(".value", "model"), names_sep = "_")

df_intensity_long <- df_intensity_ML_long %>%
  inner_join(df_intensity_baseline_long) %>%
  pivot_longer(c(intensity_ML, intensity_baseline), names_to = c(".value", "model"), names_sep = "_")






df_time_ML <- df_time_ML %>%
  inner_join(df_demographics)

df_time_baseline <- df_time_baseline %>%
  inner_join(df_demographics)

df_emissions_ML <- df_emissions_ML %>%
  mutate(total = rowSums(select(., !RINPERSOON))) %>%
  inner_join(df_demographics)

df_emissions_baseline <- df_emissions_baseline %>%
  mutate(total = rowSums(select(., !RINPERSOON))) %>%
  inner_join(df_demographics)

df_intensity_ML <- df_intensity_ML %>%
  inner_join(df_demographics)

df_intensity_baseline <- df_intensity_baseline %>%
  inner_join(df_demographics)




# BOXPLOTS ---------------------------------------------------------------------

## INTERACTIONS ----------------------------------------------------------------

### POSITION IN HOUSEHOLD ------------------------------------------------------

# inspect frequencies to make sure to not reveal personal info
df_freq <- df_time_long %>%
  subset(category == "committed") %>%
  group_by(GBAGESLACHT, position_hh) %>%
  summarize(n_pos = n()) 

write_xlsx(df_freq,
           path = "F:/Documents/Data/frequency_gender-PLHH.xlsx")




df_time_long_plot <- df_time_long %>%
  subset(category == "committed") 


plot_time <- df_time_long_plot %>%
  ggplot(mapping = aes(x = position_hh, y = time, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  theme_gender +
  facet_wrap(~ model) +
  theme(axis.text.x = element_text(angle = 45,
                                   hjust = 1)) +
  labs(title = "Time Spent on Committed Time by Gender and Position in Household",
       x = NULL,
       y = "Committed time-use (hours / day)",
       color = "Gender",
       fill = "Gender")

plot_time

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_individuals_comitted_boxplot_gender-PLHH.png", 
       plot = plot_time,
       width = 30,
       height = 25,
       units = "cm")



df_emissions_long_plot <- df_emissions_long %>%
  subset(category == "committed")

plot_emissions <- df_emissions_long_plot %>%
  ggplot(mapping = aes(x = position_hh, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  theme_gender +
  facet_wrap(~ model) +
  theme(axis.text.x = element_text(angle = 45,
                                   hjust = 1)) +
  labs(title = "Emissions from Committed Time by Gender and Position in Household",
       x = NULL,
       y = "Emissions from committed time (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender")


plot_emissions

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals_comitted_boxplot_gender-PLHH.png", 
       plot = plot_emissions,
       width = 30,
       height = 25,
       units = "cm")



df_intensity_long_plot <- df_intensity_long %>%
  subset(category == "committed")

plot_intensity <- df_intensity_long_plot %>%
  ggplot(mapping = aes(x = position_hh, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  theme_gender +
  facet_wrap(~ model) +
  theme(axis.text.x = element_text(angle = 45,
                                   hjust = 1)) +
  labs(title = "Carbon intensity from Committed Time by Gender and Position in Household",
       x = NULL,
       y = "Carbon intensity of committed time (kg CO2 equ. / hour)",
       color = "Gender",
       fill = "Gender")


plot_intensity

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals__boxplot_gender-PLHH.png", 
       plot = plot_intensity,
       width = 30,
       height = 20,
       units = "cm")










### YEAR OF BIRTH --------------------------------------------------------------

df_time_long_plot <- df_time_long %>%
  subset(category == "committed") 


plot_time <- df_time_long_plot %>%
  ggplot(mapping = aes(x = GBAGEBOORTEJAAR, y = time, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(min(df_time_long_plot$GBAGEBOORTEJAAR), 2004) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Time Spent on Committed Time by Gender and Year of Birth",
       x = "Year of birth",
       y = "Time-use (hours / day)",
       color = "Gender",
       fill = "Gender")

plot_time

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_individuals_comitted_smoothplot_gender-GBAGEBOORTEJAAR_smooth.png", 
       plot = plot_time,
       width = 30,
       height = 20,
       units = "cm")




plot_time <- df_time_long_plot %>%
  ggplot(mapping = aes(x = GBAGEBOORTEJAAR, y = time, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth(method = "lm") +
  xlim(min(df_time_long_plot$GBAGEBOORTEJAAR), 2004) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Time Spent on Committed Time by Gender and Year of Birth",
       x = "Year of birth",
       y = "Time-use (hours / day)",
       color = "Gender",
       fill = "Gender")

plot_time

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_individuals_comitted_smoothplot_gender-GBAGEBOORTEJAAR_lm.png", 
       plot = plot_time,
       width = 30,
       height = 20,
       units = "cm")



df_emissions_long_plot <- df_emissions_long %>%
  subset(category == "committed")

plot_emissions <- df_emissions_long_plot %>%
  ggplot(mapping = aes(x = GBAGEBOORTEJAAR, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(min(df_time_long_plot$GBAGEBOORTEJAAR), 2004) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Emissions from Committed Time by Gender and Year of Birth",
       x = "Year of birth",
       y = "Emissions (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender")


plot_emissions

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals_comitted_smoothplot_gender-GBAGEBOORTEJAAR.png", 
       plot = plot_emissions,
       width = 30,
       height = 20,
       units = "cm")



df_intensity_long_plot <- df_intensity_long %>%
  subset(category == "committed")

plot_intensity <- df_intensity_long_plot %>%
  ggplot(mapping = aes(x = GBAGEBOORTEJAAR, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Carbon intensity from Committed Time by Gender and Position in Household",
       x = "Year of birth",
       y = "Carbon intensity (kg CO2 equ. / hour)",
       color = "Gender",
       fill = "Gender")


plot_intensity

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals_comitted_smoothplot_gender-GBAGEBOORTEJAAR.png", 
       plot = plot_intensity,
       width = 30,
       height = 20,
       units = "cm")











### PURCHASING POWER -----------------------------------------------------------

df_time_long_plot <- df_time_long

plot_time <- df_time_long_plot %>%
  ggplot(mapping = aes(x = INPKKGEM, y = time, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Total Time-Use by Gender and Purchasing Power",
       x = "Purchasing power",
       y = "Time-use (hours / day)",
       color = "Gender",
       fill = "Gender")

plot_time

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_individuals__smoothplot_gender-INPKKGEM.png", 
       plot = plot_time,
       width = 30,
       height = 20,
       units = "cm")



df_emissions_long_plot <- df_emissions_long 

plot_emissions <- df_emissions_long_plot %>%
  ggplot(mapping = aes(x = INPKKGEM, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(quantile(df_emissions_long_plot$INPKKGEM, 0.05, na.rm = TRUE), quantile(df_emissions_long_plot$INPKKGEM, 0.95, na.rm = TRUE)) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Emissions by Gender and Purchasing Power",
       x = "Purchasing power",
       y = "Emissions (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender")


plot_emissions

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals__smoothplot_gender-INPKKGEM.png", 
       plot = plot_emissions,
       width = 30,
       height = 20,
       units = "cm")



df_intensity_long_plot <- df_intensity_long 

plot_intensity <- df_intensity_long_plot %>%
  ggplot(mapping = aes(x = INPKKGEM, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(quantile(df_emissions_long_plot$INPKKGEM, 0.05, na.rm = TRUE), quantile(df_emissions_long_plot$INPKKGEM, 0.95, na.rm = TRUE)) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Carbon intensity from Committed Time by Gender and Purchasing Power",
       x = "Purchasing power",
       y = "Carbon intensity (kg CO2 equ. / hour)",
       color = "Gender",
       fill = "Gender")


plot_intensity

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals__smoothplot_gender-INPKKGEM.png", 
       plot = plot_intensity,
       width = 30,
       height = 20,
       units = "cm")





### PERSONAL INCOME ------------------------------------------------------------

df_time_long_plot <- df_time_long

plot_time <- df_time_long_plot %>%
  ggplot(mapping = aes(x = INPPERSINK, y = time, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Total Time-Use by Gender and Personal Income",
       x = "Personal Income",
       y = "Time-use (hours / day)",
       color = "Gender",
       fill = "Gender")

plot_time

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_individuals__smoothplot_gender-INPPERSINK.png", 
       plot = plot_time,
       width = 30,
       height = 20,
       units = "cm")



df_emissions_long_plot <- df_emissions_long

plot_emissions <- df_emissions_long_plot %>%
  ggplot(mapping = aes(x = INPPERSINK, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(quantile(df_emissions_long_plot$INPPERSINK, 0.05), quantile(df_emissions_long_plot$INPPERSINK, 0.95)) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Emissions by Gender and Personal Income",
       x = "Personal income",
       y = "Emissions (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender")


plot_emissions

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals__smoothplot_gender-INPPERSINK.png", 
       plot = plot_emissions,
       width = 30,
       height = 20,
       units = "cm")



df_intensity_long_plot <- df_intensity_long 

plot_intensity <- df_intensity_long_plot %>%
  ggplot(mapping = aes(x = INPPERSINK, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_smooth() +
  xlim(quantile(df_intensity_long_plot$INPPERSINK, 0.05), quantile(df_intensity_long_plot$INPPERSINK, 0.95)) +
  theme_gender +
  facet_wrap(~ model) +
  labs(title = "Carbon intensity by Gender and Personal Income",
       x = "Personal income",
       y = "Carbon intensity (kg CO2 equ. / hour)",
       color = "Gender",
       fill = "Gender")


plot_intensity

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals__smoothplot_gender-INPPERSINK.png", 
       plot = plot_intensity,
       width = 30,
       height = 20,
       units = "cm")




