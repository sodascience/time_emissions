# R version 4.2.3 (2023-03-15 ucrt)

setwd("..")
options(scipen = 999)

library(tidyverse) # Version 2.0.0

##### PREP DATA #####

##### Read mapping data #####

# read data from manual mapping
mapping <- read.csv("data/Mapping_csv/CBS_EXIOBASE_manual.csv", sep = ";", dec = ",", skip = 1)
names(mapping) <- mapping[1,]
mapping <- mapping[-1,]

# prep dataset
mapping <- select(mapping, - cbs_matches)
row.names(mapping) <- mapping$exiobase_var



##### Transform mapping #####

# create matrix from CBS variables to be used in the RAS
# only select rows in which final consumption expenditures of households (from EXIOBASE) is > 0
ras <- mapping[which(mapping$finalConsumptionExpenditure_households > 0), 4:ncol(mapping)]

# remove any unnecessary columns
ras <- select(ras, starts_with("BOBEST"))


# scale manual mapping so that the rowSums are = 1
# strong relation => weighting should be 2.6 times larger than moderate and 6.5 times larger than weak
# moderate relation => weighting should be 2.5 times larger than weak
# weak relation

for(row in 1:nrow(ras)){
  # get all matches regardless of strength into a dataframe
  matches_cols <- which(ras[row, ] != 0)
  matches <- data.frame(ras[row, matches_cols])
  names(matches) <- names(ras[matches_cols])
  
  # get weak matches
  weak <- matches[which(matches == 'weak')]
  matches[which(matches == 'weak')] <- 1/length(weak) # assign a value to weak matches
  nominator <- max(1, length(weak)) # so that you will never divide by 0
  
  # assign a proportionate value to moderate matches (2.5 times each of the values of the weak matches)
  matches[which(matches == 'moderate')] <- 2.5*(1/nominator)
  
  # assign a proportionate value to strong matches (6.5 times each of the values of the weak matches)
  matches[which(matches == 'strong')] <- 6.5*(1/nominator)
  
  # scale to rowSum = 1
  matches <- matches/rowSums(matches)
  
  # update values in RAS table
  ras[row, matches_cols] <- matches
  
}

# make ras numeric
ras <- ras %>% mutate_if(is.character, as.numeric)

# clean up
rm(matches, weak, matches_cols, nominator, row)






##### Set desired row & column sums #####

# set desired row sums (exiobase expenditures)
desired_rowSums <- 
desired_rowSums <- mapping$finalConsumptionExpenditure_households
desired_rowSums <- as.numeric(gsub(",", ".", desired_rowSums)) # make numeric
desired_rowSums <- data.frame(desired_rowSums[which(desired_rowSums > 0)])
row.names(desired_rowSums) <- row.names(mapping[which(mapping$finalConsumptionExpenditure_households > 0),])

# exiobase units are in million dollars => change the unit
desired_rowSums <- desired_rowSums * 1000000
desired_rowSums <- desired_rowSums * 0.9015 # average $ - ???, exchange rate in 2015
# calculate total EXIOBASE expenditures
exiobase_totalExpenditures <- as.numeric(colSums(desired_rowSums))



# set desired col sums (CBS expenditures)
desired_colSums <- data.frame(read.csv("~/Research/S1_genderedFootprints/Code/IO_Analysis/Mapping_csv/CBS/expenditureSums.csv", row.names = 1))
desired_colSums <- desired_colSums %>% select(1)
names(desired_colSums) <- "colSums"
desired_colSums <- t(desired_colSums)

# calculate total CBS expenditures
cbs_totalExpenditures <- as.numeric(rowSums(desired_colSums))

diff_factor <- exiobase_totalExpenditures/cbs_totalExpenditures # ~98%
# desired_colSums <- desired_colSums*diff_factor # scale up

rm(diff_factor, cbs_totalExpenditures, exiobase_totalExpenditures)




##### RAS #####

# initiate loops
rows_end = FALSE
cols_end = FALSE
i <- 1


while(!(rows_end & cols_end)){
  
  print(paste("iteration:", i), quote = F)
  
  
  
  
  # calc column sums
  colSums <- colSums(ras, na.rm = T)
  
  # calc adjustment factors and put them in the right format (named numeric vector)
  adjustmentCols <- data.frame(t(desired_colSums/colSums))
  names_adjustmentCols <- row.names(adjustmentCols)
  adjustmentCols <- deframe(adjustmentCols)
  names(adjustmentCols) <- names_adjustmentCols
  rm(names_adjustmentCols)
  
  # make sure that none is NA or infinite
  adjustmentCols[!is.finite(adjustmentCols)] <- 0
  print(paste("average column adjustment:", mean(adjustmentCols, na.rm = T)), quote = F)
  
  # adjust cell values of RAS based on column adjustment factor
  ras <- t(t(ras)*adjustmentCols)  
  
  
  
  
  
  
  # calc row sums
  rowSums <- rowSums(ras, na.rm = T)
  
  # calc adjustment factors and put them in the right format (named numeric vector)
  adjustmentRows <- data.frame(desired_rowSums/rowSums)
  names_adjustmentRows <- row.names(adjustmentRows)
  adjustmentRows <- deframe(adjustmentRows)
  names(adjustmentRows) <- names_adjustmentRows
  rm(names_adjustmentRows)
  
  adjustmentRows[!is.finite(adjustmentRows)] <- 0
  print(paste("average row adjustment:", mean(adjustmentRows)), quote = F)
  
  # adjust cell values of RAS based on row adjustment factor
  ras <- ras * adjustmentRows
  
  
  
  if(i > 1){
    # compare adjustment factors of this iteration to previous one
    if(isTRUE(all.equal(round(adjustmentCols, 2), adjustmentCols_previous))){
      cols_end = T
      cat("The adjustment factors of columns do not change anymore. \n")
    }
    
    if(isTRUE(all.equal(round(adjustmentRows, 2), adjustmentRows_previous))){
      rows_end = T
      cat("The adjustment factors of rows do not change anymore. \n")
    }
  }
  
  
  adjustmentCols_previous <- round(adjustmentCols, 2)
  adjustmentRows_previous <- round(adjustmentRows, 2)
  
  i <- i+1
}




# prepare dataframe to save as csv
ras <- data.frame(round(ras, 4))
ras <- ras[ , order(names(ras))]

ras[, ncol(ras)+1] <- rowSums(ras, na.rm = T) # add row sums
names(ras)[ncol(ras)] <- "rowSum"

ras[nrow(ras)+1, ] <- colSums(ras, na.rm = T) # add column sums
ras[nrow(ras), ncol(ras)] <- NA # remove sum of row sums

# add exioase variables and their descriptions
exiobase_var <- unique(c(mapping$exiobase_var, "colSum"))
exiobase_description <- unique(c(mapping$exiobase_description, ""))

row.names(ras)[nrow(ras)] <- "colSum"
ras <- cbind(row.names(ras), ras)
names(ras)[1] <- "exiobase_var"


# bind columns together
exiobase <- data.frame(exiobase_var, exiobase_description)
ras <- merge(exiobase, ras, all = TRUE)
row.names(ras) <- ras$exiobase_var



# add desired sums
ras[which(!is.na(ras$rowSum)),ncol(ras) + 1] <- desired_rowSums
names(ras)[ncol(ras)] <- "desired_rowSums"


ras[nrow(ras) + 1, grepl("BOBEST", names(ras))] <- desired_colSums
row.names(ras)[nrow(ras)] <- "desired_colSums"


# re-order rows
ras <- ras %>% arrange(factor(exiobase_var, levels = mapping$exiobase_var))



# get the adjustment factor
ras[nrow(ras)+1,3:ncol(ras)] <- as.numeric(ras["colSum", 3:ncol(ras)]/ras["desired_colSums", 3:ncol(ras)])
row.names(ras)[nrow(ras)] <- "adjustment"
ras["adjustment", is.na(ras["adjustment", ])] <- 0



# save data
write.csv(ras, "data/Mapping_csv/manual_RAS_CBS-EXIOBASE.csv", row.names = F, na = "0")
write.table(ras, "data/Mapping_csv/manual_RAS_CBS-EXIOBASE_EXCEL.csv", row.names = F, sep = ";", dec = ",", na = "0")
