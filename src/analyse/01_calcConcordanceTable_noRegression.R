require(tidyverse)
require(reshape2)
require(foreign)
require(readxl)
require(limSolve)

options(scipen = 999)

# load household data

# carbon emissions
df_co2 <- read.csv("F:/Documents/Data/carbonEmissions_households.csv")
names(df_co2)[1] <- "RINPERSOONHKW"
df_co2$RINPERSOONHKW <- str_pad(as.character(df_co2$RINPERSOONHKW), 9, side = "left", pad = "0") # make sure that RINPERSOONHKW is in the correct format

# time use (predicted)
df_time <- read.csv("F:/Documents/Data/timeUse_households.csv")
df_time$RINPERSOONHKW <- str_pad(as.character(df_time$RINPERSOONHKW), 9, side = "left", pad = "0") # make sure that RINPERSOONHKW is in the correct format


# There are x households that were not to find in the koppelpersoonhuishoudentab
# So we do not know which RINPERSOON people lived in the households of those breadwinners.
# Therefore I will exclude them now
df_co2 <- df_co2 %>% subset(RINPERSOONHKW %in% df_time$RINPERSOONHKW)


# combine data
df_combined <- inner_join(df_co2, df_time)



# load mapping data
df_mapping_home <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_home")
df_mapping_home <- df_mapping_home[-1, -2] # remove descriptions of time and budget variables

df_mapping_out <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_out")
df_mapping_out <- df_mapping_out[-1, -2] # remove descriptions of time and budget variables

df_mapping_transport <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_transport")
df_mapping_transport <- df_mapping_transport[-1, -2] # remove descriptions of time and budget variables

df_mapping <- merge(df_mapping_home, df_mapping_out)
df_mapping <- merge(df_mapping, df_mapping_transport)


# rename columns to activity_... to not have numbers as variable names
names(df_mapping)[2:ncol(df_mapping)] <- paste("activity_", names(df_mapping)[2:ncol(df_mapping)], sep = "")


variables_budget <- df_mapping$Variable
df_mapping <- df_mapping %>% select(-1) # remove variable name


# make everything numeric
df_mapping <- as.data.frame(lapply(df_mapping, as.numeric))



# turn weights into relative terms (row sums should add up to 1)
df_mapping <- round(df_mapping/rowSums(df_mapping, na.rm = T), 4)


row.names(df_mapping) <- variables_budget



# save as csv
write.csv(df_mapping, "F:/Documents/Data/mapping_budget-TBO_noRegression.csv", na = "0")
