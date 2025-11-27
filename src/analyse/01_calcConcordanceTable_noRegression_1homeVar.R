require(tidyverse)
require(reshape2)
require(foreign)
require(readxl)
require(limSolve)

options(scipen = 999)




# load mapping data
df_mapping_home <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_home")
df_mapping_home <- df_mapping_home[-1, -2] # remove descriptions of time and budget variables

df_mapping_out <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_out")
df_mapping_out <- df_mapping_out[-1, -2] # remove descriptions of time and budget variables


variables_budget <- df_mapping_home$Variable


# check if home and out data are the same (if not, please use a different script)
df_mapping_home <- df_mapping_home %>%
  select(ends_with("_11")) %>%
  rename_with(~ sub("_11$", "", .x), .cols = ends_with("_11"))
df_mapping_out <- df_mapping_out %>%
  select(ends_with("_10")) %>%
  rename_with(~ sub("_10$", "", .x), .cols = ends_with("_10"))

if(!all.equal(df_mapping_home, df_mapping_out)){
  stop("Emission mappings of home and outside activities are not the same. Please consider using a different script, as this script will now merge them.")
}

df_mapping <- data.frame(variables_budget = variables_budget,
                         ((df_mapping_home == 1) | (df_mapping_out == 1)) *1L)
names(df_mapping)[2:ncol(df_mapping)] <- names(df_mapping_home)



df_mapping_transport <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_transport")
df_mapping_transport <- df_mapping_transport[-1, -2] # remove descriptions of time and budget variables
df_mapping_transport <- df_mapping_transport %>% rename(variables_budget = Variable)

# df_mapping <- merge(df_mapping_home, df_mapping_out)
df_mapping <- merge(df_mapping, df_mapping_transport)


# rename columns to activity_... to not have numbers as variable names
names(df_mapping)[2:ncol(df_mapping)] <- paste("activity_", names(df_mapping)[2:ncol(df_mapping)], sep = "")






# check which rows sum up to 0 (i.e. are not matched to anything)
for(row in 1:nrow(df_mapping)){
  var <- df_mapping$variables_budget[row]
  thisRow <- as.numeric(df_mapping[row, 2:ncol(df_mapping)])
  sum <- sum(thisRow, na.rm = TRUE)
  if(sum == 0){
    print(paste(var, sum, sep = ": "))
  }
}



df_mapping <- df_mapping %>% select(-variables_budget) # remove variable name


# make everything numeric
df_mapping <- as.data.frame(lapply(df_mapping, as.numeric))



# assign the activities that are not mapped to anything to a new activity called 'activity_home'
not_mapped <- which(rowSums(df_mapping[2:ncol(df_mapping)], na.rm = TRUE) == 0)
df_mapping$activity_home <- 0
df_mapping$activity_home[not_mapped] <- 1





# turn weights into relative terms (row sums should add up to 1)
df_mapping <- round(df_mapping/rowSums(df_mapping, na.rm = T), 4)


row.names(df_mapping) <- variables_budget



# save as csv
write.csv(df_mapping, "F:/Documents/Data/mapping_budget-TBO_noRegression_oneHomeVar.csv", na = "0")
