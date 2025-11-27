library(tidyverse)
require(reshape2)
library(nanoparquet)

knitr::opts_knit$set(scipen = 999, root.dir = "F:/Documents/R_code")
options(scipen = 999)

source("F:/Documents/R_code/groupExpenses.R")
source("F:/Documents/R_code/colors.R")

df_co2 <- read_parquet("F:/Documents/Data/carbonEmissions_households.parquet")

emission_means <- data.frame("variable" = names(df_co2), "emissions" = colMeans(df_co2, na.rm = TRUE))
write.table(emission_means, "F:/Documents/Data/carbonEmissions_households_means.csv", sep = ";", dec = ",", row.names = FALSE)
write_parquet(emission_means, "F:/Documents/Data/carbonEmissions_households_means.parquet")


df_administration <- groupExpenses_administration(df_co2)
print(summary(df_administration))
# plotExpenses(df_administration, 
#              limit_x = 500,
#              subtitle = "Administration",
#              saveAs = "density_administration_households.png")


df_food <- groupExpenses_food(df_co2)
# plotExpenses(df_food, 
#              limit_x = 5000,
#              subtitle = "Food",
#              saveAs = "density_food_households.png")


df_drinks <- groupExpenses_drinks(df_co2)
# plotExpenses(df_drinks, 
#              limit_x = 750,
#              subtitle = "Drinks",
#              saveAs = "density_drinks_households.png")


df_freeTime <- groupExpenses_freeTime(df_co2)
# plotExpenses(df_freeTime, 
#              limit_x = 1000,
#              subtitle = "Free Time",
#              saveAs = "density_freeTime_households.png")


df_freeTimeServices <- groupExpenses_freeTimeServices(df_co2)
# plotExpenses(df_freeTimeServices, 
#              limit_x = 1500,
#              subtitle = "Free Time Services",
#              saveAs = "density_freeTimeServices_households.png")


df_housing <- groupExpenses_housing(df_co2)
# plotExpenses(df_housing, 
#              limit_x = 6000,
#              subtitle = "Housing",
#              saveAs = "density_housing_households.png")


df_medicalEdu <- groupExpenses_medicalEdu(df_co2)
# plotExpenses(df_medicalEdu,
#              limit_x = 1000,
#              subtitle = "Medical Expenses & Education",
#              saveAs = "density_medicalEdu_households.png")


df_transport <- groupExpenses_transport(df_co2)
# plotExpenses(df_transport,
#              limit_x = 2000,
#              subtitle = "Transport",
#              saveAs = "density_transport_households.png")




df <- data.frame(
  food = rowSums(df_food) + rowSums(df_drinks),
  housing = rowSums(df_housing),
  freeTime = rowSums(df_freeTime) + rowSums(df_freeTimeServices),
  transport = rowSums(df_transport),
  other = rowSums(df_administration) + rowSums(df_medicalEdu)
) 

df <- df / 365

summary(df)

df_long <- df %>%
  mutate(RINPERSOONHKW = df_co2$RINPERSOONHKW) %>%
  pivot_longer(!RINPERSOONHKW,
               names_to = "category",
               values_to = "emissions") %>%
  mutate(category = factor(str_to_title(category), levels = unique(str_to_title(category))))




plot <- ggplot(df_long, mapping = aes(x = category, y = emissions, color = category, fill = category)) + 
  geom_violin(alpha = 0.3,
              position = position_dodge(width = 0.75),
              width = 0.5,
              show.legend = FALSE) +
  geom_boxplot(alpha = 0.3, 
               outliers = FALSE,
               position = position_dodge(width = 0.75),
               width = 0.5,
               show.legend = FALSE) +
  ylim(quantile(df_long$emissions, 0.05), quantile(df_long$emissions, 0.95)) +
  theme_expenseCategories +
  labs(
    title = "Household Carbon Emissions",
    x = NULL,
    y = "Emissions (kg CO2 equ. per day)",
    color = NULL, fill = NULL)
  # labs(title = "GHG footprint") + xlab("GHG Emissions (kg CO2 Equivalent)")

plot

ggsave(filename = "F:/Documents/R_code/plots/emissions_households/emissions_households__boxplot.png", 
       plot = plot,
       width = 30,
       height = 20,
       units = "cm")
