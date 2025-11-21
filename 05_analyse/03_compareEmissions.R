# this script generates graphs to compare the individual carbon emissions
# of people living in households that participated in the budget survey 
# based on predictions by ML and baseline models (trained on full time-use survey)

library(tidyverse)
library(nanoparquet)
library(ggthemes)
library(stringr)

options(scipen = 999)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")



# read emissions per individual
df_emissions_baseline <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_baseline_perActivity.parquet") %>%
  groupActivities(output_days = 1)
df_emissions_ML <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_ML_perActivity.parquet")%>%
  groupActivities(output_days = 1)



# read demographics
df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet")
df_demographics <- df_demographics %>%
  subset(RINPERSOON %in% df_emissions_baseline$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"))

  


# turn into longer dataframes
df_emissions_baseline_long <- df_emissions_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "baseline")

df_emissions_ML_long <- df_emissions_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "ML")



# combine
df_emissions <- df_emissions_baseline_long %>%
  inner_join(df_emissions_ML_long)

df_emissions_long <- df_emissions %>%
  pivot_longer(c(baseline, ML), names_to = "model", values_to = "emissions") %>%
  mutate(category = factor(str_to_title(category), levels = unique(str_to_title(category)))) %>%
  inner_join(df_demographics) 




# boxplots for all categories
plot <- df_emissions_long %>%
  ggplot(mapping = aes(x = category, y = emissions, color = model, fill = model)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  ylim(quantile(df_emissions_long$emissions, 0.05), quantile(df_emissions_long$emissions, 0.95)) +
  labs(x = NULL,
       y = "Emissions (kg CO2 equ. / day)",
       color = "Model",
       fill = "Model") +
  theme_modelComparison

plot

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals__boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")




# boxplots for all categories
plot <- df_emissions_long %>%
  ggplot(mapping = aes(x = category, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  ylim(quantile(df_emissions_long$emissions, 0.05), quantile(df_emissions_long$emissions, 0.95)) +
  labs(x = NULL,
       y = "Emissions (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender") +
  theme_gender +
  facet_wrap(~ model)

plot

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals__boxplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")



# density plots per category
for(cat in unique(df_emissions_long$category)){
  print(cat)
  
  # create plot
  df_plot <- df_emissions_long %>% 
    subset(category %in% cat)
  
  plot <- ggplot(df_plot, mapping = aes(x = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
    geom_density(alpha = 0.3) +
    xlim(quantile(df_plot$emissions, 0.05), quantile(df_plot$emissions, 0.95)) +
    labs(
      title = paste("Emissions from:", str_to_title(cat), "time"),
      x = "Emissions (kg CO2 equ. / day)",
      y = "Density",
      color = "Gender",
      fill = "Gender"
    ) +
    theme_gender +
    facet_wrap(~ model)
  
  print(plot)
  
  filename <- paste0("F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals_", cat, "_densityplot_gender.png")
  ggsave(filename = filename, 
         plot = plot,
         width = 30,
         height = 20,
         units = "cm")
  
  print(paste("saved", filename))
  
  
  plot <- ggplot(df_plot, mapping = aes(x = model, y = emissions, color = GBAGESLACHT, fill = GBAGESLACHT)) +
    geom_violin(alpha = 0.3,
                position = position_dodge(width = 0.75),
                width = 0.5) +
    geom_boxplot(alpha = 0.3, 
                 outliers = FALSE,
                 position = position_dodge(width = 0.75),
                 width = 0.5) +
    ylim(quantile(df_plot$emissions, 0.05), quantile(df_plot$emissions, 0.95)) +
    labs(
      title = paste("Emissions from:", str_to_title(cat), "time"),
      x = "Model",
      y = "Emissions (kg CO2 equ. / day)",
      color = "Gender",
      fill = "Gender"
    ) +
    theme_gender
  
  print(plot)
  
  filename <- paste0("F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals_", cat, "_violinplot_gender.png")
  ggsave(filename = filename, 
         plot = plot,
         width = 30,
         height = 20,
         units = "cm")
  
  print(paste("saved", filename))
}









# compute total emissions
df_emissions_baseline_total <- df_emissions_baseline %>%
  calc_totalActivities(total_name = "total_baseline")

df_emissions_ML_total <- df_emissions_ML %>%
  calc_totalActivities(total_name = "total_ML")

df_emissions_total <- df_emissions_baseline_total %>%
  inner_join(df_emissions_ML_total) %>%
  pivot_longer(c(total_baseline, total_ML), 
               names_to = c(".value", "model"),
               names_sep = "_") %>%
  inner_join(df_demographics) 



# boxplots for all categories
plot <- df_emissions_total %>%
  ggplot(mapping = aes(x = GBAGESLACHT, y = total, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_violin(alpha = 0.3,
              position = position_dodge(width = 0.75),
              width = 0.5) +
  geom_boxplot(alpha = 0.3, 
               outliers = FALSE,
               position = position_dodge(width = 0.75),
               width = 0.5) +
  ylim(quantile(df_emissions_total$total, 0.05), quantile(df_emissions_total$total, 0.95)) +
  labs(x = "Category",
       y = "Emissions (kg CO2 equ. / day)",
       color = "Gender",
       fill = "Gender") +
  theme_gender +
  facet_wrap(~ model)

plot

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/compare_emissions_individuals_total_boxplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")
