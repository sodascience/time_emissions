# Analyse household carbon emissions by household characteristics

library(tidyverse)
require(reshape2)
library(emmeans)
library(RColorBrewer)

knitr::opts_knit$set(scipen = 999, root.dir = "F:/Documents/R_code")
options(scipen = 999)

source("F:/Documents/R_code/groupExpenses.R")

df_co2 <- read.csv("F:/Documents/Data/carbonEmissions_households_withDemographics.csv", row.names = 1)
row.names(df_co2) <- str_pad(df_co2$RINPERSOON, 9, side = "left", pad = "0")

# group expenses using function from other script
df_co2_grouped <- groupExpenses(df_co2)

# remove individual expenses and instead add the grouped expenses to df_co2
df_co2 <- df_co2 %>%
  select(-starts_with("BOBEST")) %>%
  merge(df_co2_grouped, all = TRUE, by = "row.names") %>%
  select(-Row.names)

row.names(df_co2) <- str_pad(df_co2$RINPERSOON, 9, side = "left", pad = "0")



# construct variables to be included in the regression
df_co2 <- df_co2 %>%
  group_by(RINPERSOONHKW) %>%
  mutate(prop_women = sum(gender == "Woman" & age >= 15) / (sum(age >= 15)),
         prop_children = sum(age < 15) / hhSize,
         hhSize_ECU = 1 + 0.5*sum(age>=15) + 0.3*sum(age<15)) %>%
  ungroup() %>%
  mutate(hhSize = as.numeric(scale(as.numeric(df_co2$hhSize), scale = FALSE)), # center hhSize so that when controlling for hhSize, the main effect of the other variable will be at the average hhSize
         income_standardised = scale(as.numeric(df_co2$income_standardised), scale = FALSE))


summary(df_co2$total)
summary(df_co2$hhSize)
summary(df_co2$hhSize_ECU)
summary(df_co2$prop_women)
summary(df_co2$prop_children)
summary(df_co2$income_standardised)


# make household dataset
df_co2_hhs <- df_co2 %>% 
  subset(df_co2$RINPERSOON == df_co2$RINPERSOONHKW)



# REGRESSION -------------------------------------------------------------------

plot_trends <- function(model, ylab = ""){
  model_trends <- data.frame(emtrends(model, ~ prop_women, var = "hhSize_ECU", at = list(prop_women = c(0, 0.25, 0.5, 0.75, 1))))
  
  model_trends_pred <- data.frame(
    hhSize_ECU = rep(1:4, each = 5),
    prop_women = factor(model_trends$prop_women)) %>%
    mutate(total = hhSize_ECU * model_trends$hhSize_ECU.trend,
           total_lowerCI = hhSize_ECU * model_trends$lower.CL,
           total_upperCI = hhSize_ECU * model_trends$upper.CL)
  
  plot <- ggplot(model_trends_pred, mapping = aes(x = hhSize_ECU, y = total, color = prop_women, fill = prop_women)) +
    geom_smooth(method = "lm") +
    geom_ribbon(aes(ymin = total_lowerCI, ymax = total_upperCI), alpha = 0.2, color = NA) +
    scale_color_manual(values = brewer.pal(7, "Greens")[3:7],
                       name = "Proportion of Women\nin Household",
                       labels = c("0%", "25%", "50%", "75%", "100%")) +
    scale_fill_manual(values = brewer.pal(7, "Greens")[3:7],
                      name = "Proportion of Women\nin Household",
                      labels = c("0%", "25%", "50%", "75%", "100%")) +
    labs(title = "Household Characteristics Predict Emissions", 
         subtitle = "Controlling for household income",
         x = "Household Size",
         y = ylab) +
    theme_minimal()
  
  return(plot)
}


## total GHG emissions ---------------------------------------------------------

model <- lm(total ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Total GHG Emissions (in kg CO2)")



## admin GHG emissions ---------------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_admin = rowSums(select(., starts_with("admin"))))

model <- lm(total_admin ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Admin GHG Emissions (in kg CO2)")




## food GHG emissions ----------------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_food = rowSums(select(., starts_with("food"))))

model <- lm(total_food ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Food GHG Emissions (in kg CO2)")



## drinks GHG emissions ----------------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_drinks = rowSums(select(., starts_with("drinks"))))

model <- lm(total_drinks ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Dinks GHG Emissions (in kg CO2)")




## free time GHG emissions -----------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_freeTime = rowSums(select(., starts_with("freeTime"))))

model <- lm(total_freeTime ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Free Time GHG Emissions (in kg CO2)")




## free time services GHG emissions --------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_freeTimeServices = rowSums(select(., starts_with("freeTimeServices"))))

model <- lm(total_freeTimeServices ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Free Time Services GHG Emissions (in kg CO2)")





## housing GHG emissions -------------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_housing = rowSums(select(., starts_with("housing"))))

model <- lm(total_housing ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Housing GHG Emissions (in kg CO2)")





## medicalEdu GHG emissions ----------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_medicalEdu = rowSums(select(., starts_with("medicalEdu"))))

model <- lm(total_medicalEdu ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Medical & Education GHG Emissions (in kg CO2)")




## transport GHG emissions ----------------------------------------------------

df_co2_hhs <- df_co2_hhs %>%
  ungroup() %>%
  mutate(total_transport = rowSums(select(., starts_with("transport"))))

model <- lm(total_transport ~ income_standardised + hhSize_ECU * prop_women,
            data = df_co2_hhs)
summary(model)
car::Anova(model, type = 3)

plot_trends(model, "Transportation GHG Emissions (in kg CO2)")
