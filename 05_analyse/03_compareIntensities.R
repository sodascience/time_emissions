# this script generates graphs to compare the individual carbon intensities
# of people living in households that participated in the budget survey 
# based on predictions by ML and baseline models (trained on full time-use survey)

library(tidyverse)
library(nanoparquet)
library(ggthemes)
library(stringr)

options(scipen = 999)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")




# read intensity per individual
df_intensity_baseline <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_baseline.parquet")
df_intensity_ML <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_ML.parquet")



# read demographics
df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet")
df_demographics <- df_demographics %>%
  subset(RINPERSOON %in% df_intensity_baseline$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"))

  


# turn into longer dataframes
df_intensity_baseline_long <- df_intensity_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "baseline")

df_intensity_ML_long <- df_intensity_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "ML")



# combine
df_intensity <- df_intensity_baseline_long %>%
  inner_join(df_intensity_ML_long)

df_intensity_long <- df_intensity %>%
  pivot_longer(c(baseline, ML), names_to = "model", values_to = "intensity") %>%
  mutate(category = factor(category, levels = unique(category))) %>%
  inner_join(df_demographics, by = join_by(RINPERSOON))




# boxplots for all categories
plot <- df_intensity_long %>%
  ggplot(mapping = aes(x = category, y = intensity, color = model, fill = model)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  ylim(quantile(df_intensity_long$intensity, 0.05), quantile(df_intensity_long$intensity, 0.95)) +
  labs(x = "Category",
       y = "Intensity (kg CO2 equ./h)",
       color = "Model",
       fill = "Model") +
  theme_modelComparison

plot

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals__boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")




# boxplots for all categories
plot <- df_intensity_long %>%
  ggplot(mapping = aes(x = category, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  ylim(quantile(df_intensity_long$intensity, 0.05), quantile(df_intensity_long$intensity, 0.95)) +
  labs(x = "Category",
       y = "Intensity (kg CO2 equ./h)",
       color = "Gender",
       fill = "Gender") +
  theme_gender +
  facet_wrap(~ model)

plot

ggsave(filename = "F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals__boxplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")








# density plots per category
for(cat in unique(df_intensity_long$category)){
  print(cat)
  
  # create plot
  df_plot <- df_intensity_long %>% 
    subset(category %in% cat)
  
  plot <- ggplot(df_plot, mapping = aes(x = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
    geom_density(alpha = 0.3) +
    xlim(quantile(df_plot$intensity, 0.05), quantile(df_plot$intensity, 0.95)) +
    labs(
      title = paste("Intensities from:", str_to_title(cat), "time"),
      x = "Intensity (kg CO2 equ./h)",
      y = "Density",
      color = "Model",
      fill = "Model"
    ) +
    theme_gender +
    facet_wrap(~ model)
  
  print(plot)
  
  filename <- paste0("F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals_", cat, "_densityplot_gender.png")
  ggsave(filename = filename, 
         plot = plot,
         width = 30,
         height = 20,
         units = "cm")
  
  print(paste("saved", filename))
  
  
  
  plot <- ggplot(df_plot, mapping = aes(x = model, y = intensity, color = GBAGESLACHT, fill = GBAGESLACHT)) +
    geom_violin(alpha = 0.3,
                position = position_dodge(width = 0.75),
                width = 0.5) +
    geom_boxplot(alpha = 0.3, 
                 outliers = FALSE,
                 position = position_dodge(width = 0.75),
                 width = 0.5) +
    ylim(quantile(df_plot$intensity, 0.05), quantile(df_plot$intensity, 0.95)) +
    labs(
      title = paste("Intensities from:", str_to_title(cat), "time"),
      x = "Model",
      y = "Intensity (kg CO2 equ./h)",
      color = "Gender",
      fill = "Gender"
    ) +
    theme_gender
  
  print(plot)
  
  filename <- paste0("F:/Documents/R_code/plots/intensity_individuals/compare_intensity_individuals_", cat, "_violinplot_gender.png")
  ggsave(filename = filename, 
         plot = plot,
         width = 30,
         height = 20,
         units = "cm")
  
  print(paste("saved", filename))
}



