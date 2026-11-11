# R version 4.2.3 (2023-03-15 ucrt)

setwd("..")
options(scipen = 999)

# read data
y <- read.csv("data/EXIOBASE/IOT_2015_pxp/Y.txt", sep = "\t", header = F)

# prepare dataframe to only contain expenditures for NL
names(y) <- y[2,]
y <- y[-2,]
y <- y[, which(y[1,] == '' | y[1,] == 'NL')]
names(y)[1] <- 'sector'
y <- y[-c(1,2),]
row.names(y) <- NULL

# make columns numeric
for(col in 2:ncol(y)){
  y[, col] <- as.numeric(y[, col])
}

sectors <- unique(y$sector) # for reordering the df later

y <- aggregate(x = y[, 2:ncol(y)], by = list(y$sector), FUN = sum) # get the sum per sector

# reorder
names(y)[1] <- 'sector'
y <- y[match(sectors, y$sector),] # reorder

# get rows with zero consumption
zeroConsumption <- which(y$`Final consumption expenditure by households` == 0)
length(zeroConsumption)
print("Household expenditures is 0 in the following sectors:")
print(y[zeroConsumption, 'sector'])

# save y table for the Netherlands
row.names(y) <- NULL

# new variable names without spaces and weird chars
newNames <- c("sector", 
              "finalConsumptionExpenditure_households",
              "finalConsumptionExpenditure_NPISH",
              "finalConsumptionExpenditure_government",
              "grossFixedCapitalFormation",
              "changes_inventories",
              "changes_valuables",
              "exports")

names(y) <- newNames

write.csv(y, "data/EXIOBASE/IOT_2015_pxp/y_NL.csv")
write.table(y, "data/EXIOBASE/IOT_2015_pxp/y_NL_EXCEL.csv", row.names = F, sep = ";", dec = ",")



##### COMPARE TO OTHER YEARS #####

comparison <- data.frame(y$finalConsumptionExpenditure_households)
names(comparison) <- '2015'
row.names(comparison) <- y$sector


years <- c("2013", "2014", "2016", "2017")

for(year in years){
  # read data
  csv_name <- paste("data/EXIOBASE/IOT", year, "pxp/Y.txt", sep = '_')
  y <- read.csv(csv_name, sep = "\t", header = F)
  
  # prepare dataframe to only contain expenditures for NL
  names(y) <- y[2,]
  y <- y[-2,]
  y <- y[, which(y[1,] == '' | y[1,] == 'NL')]
  names(y)[1] <- 'sector'
  y <- y[-c(1,2),]
  row.names(y) <- NULL
  
  # make columns numeric
  for(col in 2:ncol(y)){
    y[, col] <- as.numeric(y[, col])
  }
  
  sectors <- unique(y$sector) # for reordering the df later
  
  y <- aggregate(x = y[, 2:ncol(y)], by = list(y$sector), FUN = sum) # get the sum per sector
  
  # reorder
  names(y)[1] <- 'sector'
  y <- y[match(sectors, y$sector),] # reorder
  
  # get rows with zero consumption
  zeroConsumption <- which(y$`Final consumption expenditure by households` == 0)
  length(zeroConsumption)
  print("Household expenditures is 0 in the following sectors:")
  print(y[zeroConsumption, 'sector'])
  
  # save y table for the Netherlands
  row.names(y) <- NULL
  
  # new variable names without spaces and weird chars
  newNames <- c("sector", 
                "finalConsumptionExpenditure_households",
                "finalConsumptionExpenditure_NPISH",
                "finalConsumptionExpenditure_government",
                "grossFixedCapitalFormation",
                "changes_inventories",
                "changes_valuables",
                "exports")
  
  names(y) <- newNames
  
  comparison[,year] <- y$finalConsumptionExpenditure_households
  
}

comparison <- comparison[,c("2013", "2014", "2015", "2016", "2017")]

write.csv(comparison, "data/EXIOBASE/y_NL_comparisons.csv")
write.table(comparison, "data/EXIOBASE/y_NL_comparisons_EXCEL.csv", row.names = F, sep = ";", dec = ",")

