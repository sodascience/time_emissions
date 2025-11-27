library(tidyverse)
library(nanoparquet)
library(paletteer)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")

df_sum <- read_parquet("F:/Documents/Data/medians_gender.parquet") %>%
  mutate(median_hours_text = round(median_hours, 2),
         median_emissions_text = round(median_emissions, 2),
         median_intensity_text = round(median_intensity, 2)) %>%
  subset(model != "perCapita")


# make plot
plot <- ggplot(df_sum, mapping = aes(x = GBAGESLACHT, y = median_hours, color = category, fill = category)) +
  geom_bar(stat = "identity") +
  geom_text(aes(label = median_hours_text),
            position = position_stack(vjust = 0.5),
            color = "white",
            size = 3.5) +
  labs(title = "Median Time-Use",
       x = "Gender",
       y = "Time-use (hours / day)",
       color = "Category",
       fill = "Category") +
  theme +
  facet_wrap(~ model)

plot

ggsave(filename = "F:/Documents/R_code/plots/predicted_timeUse/compare_predicted_timeUse__barplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")


# make plot
plot <- ggplot(df_sum, mapping = aes(x = GBAGESLACHT, y = median_emissions, color = category, fill = category)) +
  geom_bar(stat = "identity") +
  geom_text(aes(label = median_emissions_text),
            position = position_stack(vjust = 0.5),
            color = "white",
            size = 3.5) +
  labs(title = "Median emissions",
       x = "Gender",
       y = "Emissions (kg CO2 equ. / day)",
       color = "Category",
       fill = "Category") +
  theme +
  facet_wrap(~ model)

plot

ggsave(filename = "F:/Documents/R_code/plots/emissions_individuals/comparison_emissions_individuals__barplot_gender.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")

