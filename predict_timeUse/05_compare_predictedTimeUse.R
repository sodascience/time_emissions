# this script generates graphs to compare the predicted time-use of 
# ML and baseline models in the test dataset (20% of time-use survey)

library(tidyverse)
library(nanoparquet)
library(ggthemes)
library(stringr)

options(scipen = 999)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")

# read time per individual & group activities
df_time_baseline <- read_parquet("F:/Documents/Data/predicted_timeUse_baseline_tboPPs_testData.parquet") 
df_time_ML <- read_parquet("F:/Documents/Data/predicted_timeUse_ML_tboPPs_testData.parquet")
df_time_true <- read_parquet("F:/Documents/Data/TBO_aggregated.parquet") %>%
  subset(RINPERSOON %in% df_time_baseline$RINPERSOON)

df_errors_baseline <- df_time_baseline
df_errors_baseline[-1] <- abs(df_errors_baseline[-1] - df_time_true[-c(1,2)])

df_errors_ML <- df_time_ML
df_errors_ML[-1] <- abs(df_errors_ML[-1] - df_time_true[-c(1,2)])







df_time_baseline <- df_time_baseline %>%
  groupActivities(output_days = 1)

df_time_ML <- df_time_ML %>%
  groupActivities(output_days = 1)

df_time_true <- df_time_true %>%
  groupActivities(output_days = 1)

df_errors_baseline <- df_errors_baseline %>%
  groupActivities(output_days = 1)

df_errors_ML <- df_errors_ML %>%
  groupActivities(output_days = 1)



# turn into longer dataframes
df_time_true_long <- df_time_true %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "true")

df_time_baseline_long <- df_time_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "baseline")

df_time_ML_long <- df_time_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "ML")

df_errors_baseline_long <- df_errors_baseline %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "baseline")

df_errors_ML_long <- df_errors_ML %>%
  pivot_longer(!RINPERSOON, names_to = "category", values_to = "ML")



categories <- (df_time_true_long$category)

# combine
df_time <- df_time_true_long %>%
  inner_join(df_time_baseline_long) %>%
  inner_join(df_time_ML_long)

df_time_long <- df_time %>%
  pivot_longer(c(true, baseline, ML), names_to = "model", values_to = "timeUse") %>%
  mutate(category = factor(str_to_title(category), levels = unique(str_to_title(categories))))

df_errors <- df_errors_baseline_long %>%
  inner_join(df_errors_ML_long)

df_errors_long <- df_errors %>%
  pivot_longer(c(baseline, ML), names_to = "model", values_to = "error") %>%
  mutate(category = factor(str_to_title(category), levels = unique(str_to_title(categories))))









# Calculate total time and error

df_time_baseline_total <- df_time_baseline %>%
  calc_totalActivities(total_name = "total_baseline")

df_time_ML_total <- df_time_ML %>%
  calc_totalActivities(total_name = "total_ML")

df_time_true_total <- df_time_true %>%
  calc_totalActivities(total_name = "total_true")

df_errors_baseline_total <- df_errors_baseline %>%
  calc_totalActivities(total_name = "total_baseline")

df_errors_ML_total <- df_errors_ML %>%
  calc_totalActivities(total_name = "total_ML")



df_time_total <- df_time_baseline_total %>%
  inner_join(df_time_ML_total) %>%
  inner_join(df_time_true_total) %>%
  pivot_longer(c(total_baseline, total_ML, total_true),
               names_to = c(".value", "model"),
               names_sep = "_")

df_errors_total <- df_errors_baseline_total %>%
  inner_join(df_errors_ML_total)%>%
  pivot_longer(c(total_baseline, total_ML),
               names_to = c(".value", "model"),
               names_sep = "_")




# PREDICTED TIME-USE -----------------------------------------------------------

## TOTAL -----------------------------------------------------------------------

plot <- ggplot(df_time_total, aes(x = total, color = model, fill = model)) +
  geom_density(alpha = 0.3) +
  xlim(quantile(df_time_total$total, 0.05), quantile(df_time_total$total, 0.95)) +
  theme_modelComparison +
  labs(title = "Total Time-use",
       x = "Time-use (hours/day)",
       y = "Density",
       color = "Model",
       fill = "Model")

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_total_densityplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")




plot <- ggplot(df_errors_total, aes(x = total, color = model, fill = model)) +
  geom_density(alpha = 0.3) +
  # geom_histogram(alpha = 0.3, position = "identity") +
  xlim(quantile(df_errors_total$total, 0.05), quantile(df_errors_total$total, 0.95)) +
  theme_modelComparison +
  labs(title = "Total Absolute Error of Time-Use",
       x = "Absolute Error (hours/day)",
       y = "Density",
       color = "Model",
       fill = "Model")

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_error_total_densityplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")




plot <- ggplot(df_errors_total, aes(x = model, y = total, color = model, fill = model)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  # xlim(quantile(df_errors_total$total, 0.05), quantile(df_errors_total$total, 0.95)) +
  theme_modelComparison +
  theme(legend.position = "none") +
  labs(title = "Total Absolute Error of Time-Use",
       x = "Model",
       y = "Absolute Error (hours/day)",
       color = NULL,
       fill = NULL)

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_error_total_boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")



## PER CATEGORY ----------------------------------------------------------------

# boxplots for all categories
plot <- df_time_long %>%
  ggplot(mapping = aes(x = category, y = timeUse, color = model, fill = model)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  labs(x = NULL,
       y = "Time-use (hours / day)",
       color = "Model",
       fill = "Model") +
  theme_modelComparison

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse__boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")



# density plots per category
for(cat in unique(df_time_long$category)){
  print(cat)
  
  # create plot
  df_plot <- df_time_long %>% 
    subset(category %in% cat)
  
  plot <- ggplot(df_plot, mapping = aes(x = timeUse, color = model, fill = model)) +
    geom_density(alpha = 0.3) +
    xlim(quantile(df_plot$timeUse, 0.05), quantile(df_plot$timeUse, 0.95)) +
    labs(
      title = paste("Time spent on:", str_to_title(cat), "time"),
      x = "Time-use (hours / day)",
      y = "Density",
      color = "Model",
      fill = "Model"
    ) +
    theme_modelComparison
  
  print(plot)
  
  filename <- paste0("F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse_", cat, "_densityplot.png")
  ggsave(filename = filename, 
         plot = plot,
         width = 30,
         height = 20,
         units = "cm")
  
  print(paste("saved", filename))
}




# ERRORS -----------------------------------------------------------------------

# boxplots for all categories
plot <- df_errors_long %>%
  ggplot(mapping = aes(x = category, y = abs(error), color = model, fill = model)) +
  geom_boxplot(outliers = FALSE, alpha = 0.3) +
  labs(x = NULL,
       y = "Absolute error (hours / day)",
       color = "Model",
       fill = "Model") +
  theme_modelComparison

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_error_timeUse__boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")



## COMPARE PER GENDER ----------------------------------------------------------

df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet")

df_demographics <- df_demographics %>%
  subset(RINPERSOON %in% df_time_baseline$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"))

df_plot <- df_time_long %>%
  inner_join(df_demographics)

# boxplots for all categories
plot <- df_plot %>%
  ggplot(mapping = aes(x = category, y = timeUse, color = model, fill = model)) +
  geom_boxplot(alpha = 0.3, 
               outliers = FALSE,
               position = position_dodge(width = 0.75),
               width = 0.5) +
  ylim(quantile(df_plot$timeUse, 0.05), quantile(df_plot$timeUse, 0.95)) +
  labs(x = NULL,
       y = "Time-use (hours / day)",
       color = "Model",
       fill = "Model") +
  theme_modelComparison +
  facet_wrap(~GBAGESLACHT)

plot



# boxplots for all categories
plot <- df_plot %>%
  ggplot(mapping = aes(x = category, y = timeUse, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(alpha = 0.3, 
               outliers = FALSE,
               position = position_dodge(width = 0.75),
               width = 0.5) +
  ylim(quantile(df_plot$timeUse, 0.05), quantile(df_plot$timeUse, 0.95)) +
  labs(x = NULL,
       y = "Time-use (hours / day)",
       color = "Gender",
       fill = "Gender") +
  theme_gender +
  theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
  facet_wrap(~ model)
  

plot


ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_timeUse__boxplot_gender.png", 
       plot = plot,
       width = 40,
       height = 20,
       units = "cm")



# errors

df_plot <- df_errors_long %>%
  inner_join(df_demographics)

# boxplots for all categories
plot <- df_plot %>%
  ggplot(mapping = aes(x = category, y = error, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(alpha = 0.3, 
               outliers = FALSE,
               position = position_dodge(width = 0.75),
               width = 0.5) +
  ylim(quantile(df_plot$error, 0.05), quantile(df_plot$error, 0.95)) +
  labs(x = NULL,
       y = "Absolute error",
       color = "Gender",
       fill = "Gender") +
  theme_gender +
  facet_wrap(~model)

plot


ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_error_timeUse__boxplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")
