# R version 4.2.3 (2023-03-15 ucrt)

# this R-Script creates the CBS to EXIOBASE mapping table (0/1)
# as an input, it needs:
  # CBS_COICOP2018_variables.csv - a mapping of CBS variables to COICOP 2018 variables
  # EXIOBASE_COICOP2018.csv - a mapping of COICOP 2018 to EXIOBASE variables

setwd("..")

library(tidyverse) # Version 2.0.0

# read in data
cbs_coicop <- read.csv("data/Mapping_csv/CBS_COICOP2018_variables.csv", sep = ";")
exiobase_coicop <- read.csv("data/Mapping_csv/EXIOBASE_COICOP2018.csv", sep = ";", header = FALSE)

# create mapping dataframe
mapping <- data.frame(exiobase_var = exiobase_coicop$V2, exiobase_description = exiobase_coicop$V3, cbs_matches = "")
mapping[,cbs_coicop$CBS_detailed] <- 0


for(i in 1:nrow(mapping)){ # loop through exiobase variables
  exiobase_var <- mapping$exiobase_var[i]
  print(exiobase_var)
  
  for(j in 4:ncol(mapping)){ # loop through CBS variables
    cbs_var <- names(mapping)[j]
    cbs_var_name <- cbs_coicop$CBS_detailedDescription[which(cbs_coicop$CBS_detailed == cbs_var)] # get the variable label of the CBS variable
    
    # find which COICOP 2018 variables match to the CBS variables
    matches_cbsCoicop <- cbs_coicop[which(cbs_coicop$CBS_detailed == cbs_var), "MATCHES_COICOP2018"]
    matches_cbsCoicop <- str_split(matches_cbsCoicop, ", ")[[1]] # split to get each individual match

    for(match_cbsCoicop in matches_cbsCoicop){ # loop through the matches of CBS to COICOP 2018
      match_cbsCoicop <- paste("c", match_cbsCoicop, sep = "")
      
      # check whether the COICOP 2018 match of CBS also matches to the EXIOBASE variable of this loop
      
      # get list of COICOP variables that match to the EXIOBASE variable of this loop
      matches_exiobaseCoicop <- exiobase_coicop[which(exiobase_coicop$V2 == exiobase_var), 4:ncol(exiobase_coicop)]
      
      # check if the current-loop match of CBS to COICOP 2018 is in the list of matches from this EXIOBASE variable to COICOP 2018
      # if true, then the the CBS variable of this loop matches to the EXIOBASE variable of this loop
      if(match_cbsCoicop %in% matches_exiobaseCoicop){
        mapping[i, cbs_var] <- 1 # if true, then change the number of the mapping to 1
        
        mapping[i, "cbs_matches"] <- paste(mapping[i, "cbs_matches"], cbs_var_name, sep = "; ")
      }
    }
  }
}

exiobase_matches <- data.frame(cbs_vars = names(mapping)[4:ncol(mapping)], exiobase_matches = "")

for(i in 1:nrow(exiobase_matches)){
  cbs_var <- exiobase_matches$cbs_vars[i]
  
  matches <- which(mapping[cbs_var] == 1) # get all exiobase variables that match
  matches <- mapping$exiobase_description[matches] # get exioase variable names that match
  matches_str <- paste(matches, collapse = '; ') # collapse to string
  
  exiobase_matches$exiobase_matches[i] <- matches_str
}

# add exiobase_matches as row to mapping df (using a helper df)
helper_df <- data.frame(exiobase_var = NA, exiobase_description = NA, cbs_matches = NA)
helper_df[,exiobase_matches$cbs_vars] = exiobase_matches$exiobase_matches

mapping <- rbind(helper_df, mapping)

rm(helper_df)


# save as csv
write.csv(mapping, file = "data/Mapping_csv/CBS_EXIOBASE_automatic.csv")
