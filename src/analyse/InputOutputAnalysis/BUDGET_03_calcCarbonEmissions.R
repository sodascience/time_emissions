library(readxl)
library(tidyverse)


# read budget data
budget_df <- read.csv("F:/Documents/Data/budget_df.csv")


# read carbon intensities
co2_intensity_df <- data.frame(read_excel("F:/Documents/Data/CBS_carbonIntensities.xlsx", ))
row.names(co2_intensity_df) <- co2_intensity_df$Variable
co2_intensity_df <- co2_intensity_df %>% select(-Variable)

co2_intensity_df <- data.frame(t(co2_intensity_df)) # turn into dataframe
co2_intensity_matrix <- as.matrix(co2_intensity_df) # turn into matrix

# repeat the one row of co2 intensities to match the dimensions of budget_df
co2_intensity_repeat <- co2_intensity_matrix[rep(1:nrow(co2_intensity_matrix), each = nrow(budget_df)), ] 


# turn expenses data into matrix
budget_matrix <- as.matrix(budget_df[, which(names(budget_df) %in% names(co2_intensity_df))])


# Multiply expenses from budget_df with carbon intensities
co2_df <- as.data.frame(budget_matrix * co2_intensity_repeat)


# add identifier
row.names(co2_df) <- budget_df$RINPERSOON
co2_df$RINPERSOONHKW <- budget_df$RINPERSOON


# clean up
rm(budget_matrix, co2_intensity_matrix, co2_intensity_repeat)


# calculate total CO2 per household
co2_df$total <- rowSums(co2_df)



# export to csv
write.csv(co2_df, "F:/Documents/Data/carbonEmissions_households.csv")
write_parquet(co2_df, "F:/Documents/Data/carbonEmissions_households.parquet")
