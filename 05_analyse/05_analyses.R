library(tidyverse)
library(nanoparquet)
library(paletteer)

source("F:/Documents/R_code/groupActivities.R")
source("F:/Documents/R_code/colors.R")

df_time <- read_parquet("F:/Documents/Data/predicted_timeUse_ML_budgetPPs.parquet") %>%
  groupActivities(output_days = 1)
df_emissions <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_ML_perActivity.parquet") %>%
  groupActivities(output_days = 1)
df_emissions_baseline <- read_parquet("F:/Documents/Data/carbonEmissions_individuals_baseline_perActivity.parquet") %>%
  groupActivities(output_days = 1)
df_intensity <- read_parquet("F:/Documents/Data/carbonIntensity_individuals_ML.parquet")

df_demographics <- read_parquet("F:/Documents/Data/df_demographics.parquet") %>%
  subset(RINPERSOON %in% df_emissions$RINPERSOON) %>%
  mutate(GBAGESLACHT = fct_recode(GBAGESLACHT, "Men" = "1", "Women" = "2"))


summary(df_time)
summary(df_emissions)
summary(df_intensity)


df_time <- df_time %>%
  inner_join(df_demographics)

df_emissions <- df_emissions %>%
  mutate(total = rowSums(select(., !RINPERSOON))) %>%
  inner_join(df_demographics)

df_emissions_baseline <- df_emissions_baseline %>%
  mutate(total = rowSums(select(., !RINPERSOON))) %>%
  inner_join(df_demographics)

df_intensity <- df_intensity %>%
  inner_join(df_demographics)





model <- lm(total ~ GBAGESLACHT, df_emissions)
summary(model)


ggplot(df_emissions, mapping = aes(x = GBAGESLACHT, y = total, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE,
               alpha = 0.3) +
  geom_violin(alpha = 0.3) +
  ylim(quantile(df_emissions$total, 0.05), quantile(df_emissions$total, 0.95)) +
  theme_gender





model <- lm(total ~ GBAGESLACHT, df_emissions_baseline)
summary(model)


ggplot(df_emissions_baseline, mapping = aes(x = GBAGESLACHT, y = total, color = GBAGESLACHT, fill = GBAGESLACHT)) +
  geom_boxplot(outliers = FALSE,
               alpha = 0.3) +
  geom_violin(alpha = 0.3) +
  ylim(quantile(df_emissions$total, 0.05), quantile(df_emissions$total, 0.95)) +
  theme_gender





library(lme4)

model_mixed <- lmer(total ~ GBAGESLACHT + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions)
summary(model_mixed)


model_mixed <- lmer(total ~ GBAGESLACHT * TYPHH + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions)
summary(model_mixed)


model_mixed <- lmer(transport ~ GBAGESLACHT * AANTALKINDHH + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions)
summary(model_mixed)




# baseline

model_mixed <- lmer(total ~ GBAGESLACHT + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions_baseline)
summary(model_mixed)


model_mixed <- lmer(total ~ GBAGESLACHT * TYPHH + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions_baseline)
summary(model_mixed)


model_mixed <- lmer(committed ~ GBAGESLACHT * AANTALKINDHH + (1 + GBAGESLACHT | RINPERSOONHKW),
                    data = df_emissions_baseline)
summary(model_mixed)









# model <- lm(total ~ GBAGESLACHT * AANTALKINDHH, df_emissions)
# summary(model)
# 
# library(emmeans)
# library(ggeffects)
# df_pred <- ggemmeans(model, terms = c("AANTALKINDHH", "GBAGESLACHT"))
# 
# ggplot(df_pred, aes(x = x, y = predicted, color = group)) +
#   geom_line() +
#   geom_ribbon(aes(ymin = conf.low, ymax = conf.high, fill = group),
#               alpha = 0.2, color = NA) +
#   labs(
#     x = "Number of children in household",
#     y = "Predicted emissions",
#     color = "Gender",
#     fill = "Gender"
#   ) +
#   soda_theme
