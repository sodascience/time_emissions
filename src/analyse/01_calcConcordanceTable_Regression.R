require(tidyverse)
require(reshape2)
require(foreign)
require(readxl)
require(limSolve)

options(scipen = 999)

# load household data

# carbon emissions
df_co2 <- read.csv("F:/Documents/Data/carbonEmissions.csv")
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
df_mapping_intercept <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_intercept")
df_mapping_intercept <- df_mapping_intercept[-1, -2] # remove descriptions of time and budget variables

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







# create dataframe to store model weights in 
df_mapping_weights <- merge(df_mapping_intercept, df_mapping)
df_mapping_weights <- df_mapping_weights %>% select(-1) # remove variable name
df_mapping_weights <- as.data.frame(lapply(df_mapping_weights, as.numeric))
row.names(df_mapping_weights) <- df_mapping$Variable




# get time variables that each expenditure variable is mapped to respectively
for(expenditure in 1:nrow(df_mapping)){ # loop through rows
# for(expenditure in 29){ # for testing: loop through rows
  expenditure_name <- df_mapping$Variable[expenditure] # get name of expenditure
  
  # check which activities are mapped to expenditure
  activities <- which(df_mapping[expenditure,] == 1) # check which columns are = 1
  activities <- names(df_mapping)[activities] # get the activity names
  
  if("Intercept" %in% activities){
    activities <- activities[-grep("Intercept", activities)] # remove intercept
  }
  
  if(length(activities) > 0){
    # create dataframe for analysis that contains the expenditure variable and the mapped activities (without locations)
    df_selection <- cbind(df_combined[c(expenditure_name,activities)])
    
    # create formula
    formula <- paste(activities, collapse = " + ") # collapse activities into one formula string
    
    # add "0 +" if there should be no intercept
    if(df_mapping_intercept[expenditure, "Intercept"] == 0){
      formula <- paste("0", formula, sep = " + ")
    }
    
    formula <- as.formula(paste(expenditure_name, "~", formula)) # turn into formula
    print(formula)
    
    # run model
    # model <- lm(formula, data = df_selection)
    
    # run non-negative least squares regression as it makes no sense if regression weights are >0
    
    a <- as.matrix(model.matrix(formula, data = df_selection))
    b <- unlist(df_selection[1])
    model_nnls <- nnls::nnls(a, b)
   
    # store the weights in a mapping table
    if(df_mapping_intercept[expenditure, "Intercept"] == 0){ # without intercept
      df_mapping_weights[expenditure_name, activities] <- t(model_nnls$x)
    } else{ # with intercept
      df_mapping_weights[expenditure_name, c("Intercept", activities)] <- t(model_nnls$x)
    }
  }
}


# turn regression weights into relative terms (row sums should add up to 1)
df_mapping_weights <- round(df_mapping_weights/rowSums(df_mapping_weights, na.rm = T), 4)


# save as csv
write.csv(df_mapping_weights, "F:/Documents/Data/mapping_budget-TBO_noRegression.csv", na = "0")
