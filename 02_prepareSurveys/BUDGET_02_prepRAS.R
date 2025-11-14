options(scipen = 999)

library(foreign)
library(data.table)
library(tidyverse)

budget_df <- read.csv("F:/Documents/Data/budget_df.csv")
expenditure_vars <- budget_df %>% select(starts_with("BOBEST"))

expenditure_vars <- expenditure_vars*budget_df$BOGEWICHT

colSums <- colSums(expenditure_vars)
colSums <- data.frame(colSums)

write.csv(colSums, "~/Data/expenditureSums.csv")
