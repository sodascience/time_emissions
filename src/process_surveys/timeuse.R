require(tidyverse)
require(reshape2)
require(foreign)
require(readxl)
require(nanoparquet)


options(scipen = 999)
getwd()

# df_co2 <- read.csv("F:/Documents/Data/carbonEmissions.csv", row.names = 1)
df_time <- read.spss("G:/VrijetijdCultuur/TBO/2016/TBO2016V2.sav", to.data.frame = TRUE, use.value.labels = FALSE)
# df_time_meta <- read_excel("F:/Documents/Data/TBO_meta.xlsx", "activities_unique")
# df_time_meta_loc <- read_excel("F:/Documents/Data/TBO_meta.xlsx", "locations")

# df_mapping_intercept <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_intercept")
# df_mapping_intercept <- df_mapping_intercept[-1, -2] # remove descriptions of time and budget variables

# df_mapping_home <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_home")
# df_mapping_home <- df_mapping_home[-1, -2] # remove descriptions of time and budget variables
# 
# df_mapping_out <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_out")
# df_mapping_out <- df_mapping_out[-1, -2] # remove descriptions of time and budget variables
# 
# df_mapping_transport <- read_excel("F:/Documents/Data/mapping_budget-TBO.xlsx", "mapping_transport")
# df_mapping_transport <- df_mapping_transport[-1, -2] # remove descriptions of time and budget variables
# 
# df_mapping <- merge(df_mapping_home, df_mapping_out)
# df_mapping <- merge(df_mapping, df_mapping_transport)



primary_cols <- names(df_time)[which(grepl("ha[0-9+]", names(df_time)))]
secondary_cols <- names(df_time)[which(grepl("na[0-9+]", names(df_time)))]
location_cols <- names(df_time)[which(grepl("hl[0-9+]", names(df_time)))]





# create dfs from primary and secondary activities
df_time_primary <- df_time[c("RINPERSOON", primary_cols)] # select all primary activities
df_time_secondary <- df_time[c("RINPERSOON", secondary_cols)] # select all secondary activities
df_time_location <-  df_time[c("RINPERSOON", location_cols)] # select all locations



# pad activity codes with 0s so that e.g. activity 110 becomes activity 0110
# primary
df_time_primary[primary_cols] <- lapply(df_time_primary[primary_cols], function(x) {
  str_pad(as.character(x), width = 4, side = "left", pad = 0)
})
# secondary
df_time_secondary[secondary_cols] <- lapply(df_time_secondary[secondary_cols], function(x) {
  str_pad(as.character(x), width = 4, side = "left", pad = 0)
})






# add transport locations to the primary activities that are performed during transport so that we know which transport

df_time_transport <- df_time_location %>% mutate(across(-1, ~ ifelse(.>=20, paste0("_", .), "")))

for(col in 2:ncol(df_time_primary)){ # loop through cols
  primary_col <- df_time_primary[col]
  transport_col <- df_time_transport[col]
  
  # combine location with primary activity
  primary_combined <- cbind(primary_col, transport_col)
  primary_combined <- apply(primary_combined, MARGIN = 1, FUN = function(x) paste0(x[1], x[2]))
  df_time_primary[col] <- primary_combined
  
  # not combining it with secondary activity to not count the transport double
}



df_time_primary <- as.data.frame(lapply(df_time_primary, as.character)) # turn into char vectors
df_time_secondary <- as.data.frame(lapply(df_time_secondary, as.character)) # turn into char vectors









# get names of all activities
activities_primary <- sort(unique(unlist(df_time_primary[2:ncol(df_time_primary)])))
activities_secondary <- sort(unique(unlist(df_time_secondary[2:ncol(df_time_secondary)])))

all_activities <- sort(unique(c(activities_primary, activities_secondary)))







# make new df_activities to aggregate number of hours spent on each activity
df_activities <- as.data.frame(matrix(nrow = 2260, ncol = 1))
names(df_activities) <- "RINPERSOON"
df_activities$RINPERSOON <- df_time$RINPERSOON




# aggregate number of mentions per activity for primary and secondary activities
for(activity in all_activities){
  activity <- toString(activity)
  
  print(paste("Calculating total time for", activity))
  
  # count total number of loc_activity mentions in PRIMARY activities
  primaryTotal <- rowSums(df_time_primary == activity, na.rm = TRUE) # sum up number of times that a person spent in that loc_activity
  df_activities[[activity]] <- primaryTotal # make variable of location_activity
  
  # count total number of loc_activity mentions in SECONDARY activities
  secondaryTotal <- rowSums(df_time_secondary == gsub(",", "", activity), na.rm = TRUE)  # in secondary, there is no comma in the descriptions
  
  # add to total number
  df_activities[[activity]] <- df_activities[[activity]] + secondaryTotal
}










# aggregate all subactivities to activities
pattern <- "^[0-9]{3}[^0]" # subactivities are not ending in 0

act_matches <- df_activities %>% select(matches(pattern)) # get a df that contains all columns with variables that match subactivity pattern

# remove certain subactivities that I do want to keep
act_matches <- act_matches %>% select(-matches("^02[1|2|3]4")) # eating, snacking or drinking in horeca 
# as canteens have 0 emissions, I leave the eating at work out (i.e. treat it as if it was at home); also because many people bring their own lunch instead of going to a canteen


count_newActivities <- 0 # to count how many activities were created
count_deletedActivities <- 0 # to count how many subactivities were deleted

print(paste("df_activities currently has", ncol(df_activities), "columns."))


for(subactivity in names(act_matches)){
  activity <- sub("[1-9]$", "0", substr(subactivity, 1, 4)) # get activity from subactivity
  
  # if subactivity was performed on transportation, then add the transportation code again
  activity <- paste0(activity, substr(subactivity, 5, nchar(subactivity)))
  
  if(!(activity %in% names(df_activities))){ # if activity does not exist in df_activities yet
    df_activities[[activity]] <- 0 # create activity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", activity))
  }
  
  df_activities[activity] <- df_activities[activity] + df_activities[subactivity] # add number of mentions of subactivity to number of mentions of activity
  df_activities <- df_activities %>% select(-subactivity) # delete subactivity column from df_activities
  
  count_deletedActivities <- count_deletedActivities + 1
  
  print(paste(subactivity, "added to", activity)) # confirm output
}

print(paste(count_newActivities, "new activities were added to df_activities"))
print(paste(count_deletedActivities, "subactivities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))





# aggregate activities to superactivities
pattern <- "^[0-9]{2}[1-9]0" # activities are not ending in 00

act_matches <- df_activities %>% select(matches(pattern)) # get a df that contains all columns with variables that match subactivity pattern


# some activities do contain valuable information, so I want to keep them instead of aggregating
# in the following lines, I unselect the activities that I want to keep

act_matches <- act_matches %>% select(-matches("^0230")) # 0230 ("iets drinken")
act_matches <- act_matches %>% select(-matches("^03[1|2]0")) # 0310 ( "Wassen en aankleden") | 0320 ("Medische verzorging")

act_matches <- act_matches %>% select(-matches("^3310")) # 33x0 ("Kleren wassen")
act_matches <- act_matches %>% select(-matches("^34[3|4]0")) # 3430|3440 ("Huisdieren verzorgen | Hond uitlaten")
act_matches <- act_matches %>% select(-matches("^3540")) # 3540 ("Onderhoud en reparatie vervoersmiddelen")
act_matches <- act_matches %>% select(-matches("^36[1-8]0")) # 36x0 ("Boodschappen, commerciele, persoonlijke diensten")
act_matches <- act_matches %>% select(-matches("^38[2|3]0")) # 3820|3830 ("Hulp bij schoolwerk | Voorlezen, spelen met kind")

act_matches <- act_matches %>% select(-matches("^5140")) # 5140 ("Telefoneren")

act_matches <- act_matches %>% select(-matches("^7130")) # 7130 ("Correspondentie")
act_matches <- act_matches %>% select(-matches("^7330")) # 7330 ("Computer spelen)

act_matches <- act_matches %>% select(-matches("^9[0-8][1-9]0")) # 9xx0 (not 99x0)

# now, act_matches only contains the variables (activities) that I want to aggregate to superactivities


count_newActivities <- 0 # to count how many superactivities were created
count_deletedActivities <- 0 # to count how many activities were deleted


for(activity in names(act_matches)){
  superactivity <- sub("[1-9]0$", "00", substr(activity, 1, 4)) # get superactivity from activity
  
  # if activity was performed on transportation, then add the transportation code again
  superactivity <- paste0(superactivity, substr(activity, 5, nchar(activity)))
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  count_deletedActivities <- count_deletedActivities + 1
  
  print(paste(activity, "added to", superactivity)) # confirm output
}

print(paste(count_newActivities, "new superactivities were added to df_activities"))
print(paste(count_deletedActivities, "activities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))








# aggregate eating activities to superactivities (but leaving in the relevant locations)
pattern <- "^02[1|2|3]4" # 02x4

act_matches <- df_activities %>% select(matches(pattern)) # get a df that contains all columns with variables that match subactivity pattern

count_newActivities <- 0 # to count how many superactivities were created
count_deletedActivities <- 0 # to count how many activities were deleted


for(activity in names(act_matches)){
  superactivity <- "0204" # always the same superactivity
  
  # is it performed on transport?
  transport <- substr(activity, 5, nchar(activity))
  
  if(nchar(transport) > 0) { # if performed on transportation (e.g. drive-through)
    
    # for these activities, I want to count both, the emissions for eating out and those for transportation
    # so, if a person is eating on transportation, I add a second activity for the transportation (9000)
    superactivity_transport <- paste0("9000", transport) # create superactivity_transport for the transport associated with eating
  
    if(!(superactivity_transport %in% names(df_activities))){ # if superactivity_transport does not exist in df_activities yet
      df_activities[[superactivity_transport]] <- 0 # create superactivity_transport column
      count_newActivities <- count_newActivities + 1
      print(paste("Created activity", superactivity_transport))
    }
    
    df_activities[superactivity_transport] <- df_activities[superactivity_transport] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity_transport
    
    print(paste(activity, "added to", superactivity_transport)) # confirm output
  }
  
  
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }  
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  count_deletedActivities <- count_deletedActivities + 1
  
  print(paste(activity, "added to", superactivity)) # confirm output
}

print(paste(count_newActivities, "new superactivities were added to df_activities"))
print(paste(count_deletedActivities, "activities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))













# for the purposes of calculating the carbon footprint of activities,
# some activities should form their own groups of superactivities instead of the predefined one
# e.g. "huisdieren verzorgen" and "hond uitlaten"
# because they map to similar expenditures or emission categories

act_matches <- df_activities %>% select(matches("^34[3|4]0")) # 3430|3440 ("Huisdieren verzorgen | Hond uitlaten")

superactivity_new <- "3430" # activity code that becomes the new "superactivity"
act_matches <- act_matches %>% select(-matches(superactivity_new)) # remove superactivity from act_matches so that it does not get overwritten

for(activity in names(act_matches)){
  
  # if activity was performed on transportation, then add the transportation code again
  superactivity <- paste0(superactivity_new, substr(activity, 5, nchar(activity)))
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  print(paste(activity, "added to", superactivity)) # confirm output
}




act_matches <- df_activities %>% select(matches("^38[2|3]0")) # 3820|3830 ("Hulp bij school en huiswerk | Voorlezen, spelen en praten met kind")

superactivity_new <- "3830" # activity code that becomes the new "superactivity"
act_matches <- act_matches %>% select(-matches(superactivity_new)) # remove superactivity from act_matches so that it does not get overwritten

for(activity in names(act_matches)){
  
  # if activity was performed on transportation, then add the transportation code again
  superactivity <- paste0(superactivity_new, substr(activity, 5, nchar(activity)))
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  print(paste(activity, "added to", superactivity)) # confirm output
}



act_matches <- df_activities %>% select(matches("^8[2|3]00")) # 8200|8300 ("Audiovisueel media, ongespecificeerd | Radio en muziek, ongespecificeerd")

superactivity_new <- "8200" # activity code that becomes the new "superactivity"
act_matches <- act_matches %>% select(-matches(superactivity_new)) # remove superactivity from act_matches so that it does not get overwritten

for(activity in names(act_matches)){
  
  # if activity was performed on transportation, then add the transportation code again
  superactivity <- paste0(superactivity_new, substr(activity, 5, nchar(activity)))
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  print(paste(activity, "added to", superactivity)) # confirm output
}















# aggregate superactivities to highest category for education and paid work
pattern <- "^[1|2][1-9]00" # 1x00 or 2x00

act_matches <- df_activities %>% select(matches(pattern)) # get a df that contains all columns with variables that match subactivity pattern

count_newActivities <- 0 # to count how many superactivities were created
count_deletedActivities <- 0 # to count how many activities were deleted

for(activity in names(act_matches)){
  superactivity <- sub("[1-9]00$", "000", substr(activity, 1, 4)) # get superactivity from activity
  
  # if activity was performed on transportation, then add the transportation code again
  superactivity <- paste0(superactivity, substr(activity, 5, nchar(activity)))
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  count_deletedActivities <- count_deletedActivities + 1
  
  print(paste(activity, "added to", superactivity)) # confirm output
}

print(paste(count_newActivities, "new superactivities were added to df_activities"))
print(paste(count_deletedActivities, "activities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))











# df_activities contains variables like 7190_24 (going by car to a hobby)
# these variables should be aggregated in their respective transport category
# in this case: 9670_24 (car transport for free time)

# inspect which activities should be aggregated
act_matches <- df_activities %>% select(matches("_2[0-9]$"))

act_matches <- act_matches %>% select(-matches("^9[0-8]"))

patterns <- c( # patterns of activities to be aggregated (in df)
  "^0[0-9]{3}", # persoonlijke verzorging
  "^1[0-9]{3}", # werk
  "^2[0-9]{3}", # education
  "^3[6|7][0-9]{2}", # winkels en diensten 
  "^3[0-58-9][0-9]{2}", # huishouden 
  "^4[0-9]{3}", # vrijwilligerswerk
  "^5[0-1][0-9]{2}", # sociaal leven 
  "^5[2-3][0-9]{2}", # vermaak, cultuur, uitrusten
  "^6[0-9]{3}", # sport en lichaamsbeweging 
  "^7[0-9]{3}", # hobby
  "^8[0-9]{3}" # media
)
  
transport_activities <- c( # transport activity codes that the patterns should be aggregated to
  "9000",
  "9100",
  "9200", 
  "9360", 
  "9380",
  "9400",
  "9500",
  "9600",
  "9600",
  "9600",
  "9600"
)
  


# create a dictionary that matches patterns to transport activities
dict <- data.frame(pattern = patterns, transport_activity = transport_activities)



# create a vector with all combinations of (transport) locations and transport activities
location_transport_activities <- expand.grid(transport_activities, 20:26)
location_transport_activities <- paste(location_transport_activities$Var1, location_transport_activities$Var2, sep = "_")
location_transport_activities <- unique(location_transport_activities)

# make sure that all location_transport_activities are in df_activities
for(new in location_transport_activities[which(!(location_transport_activities %in% names(df_activities)))]){
  df_activities[[new]] <- 0
  print(paste(new, "added to df_activities"))
}



count_deletedActivities <- 0 # to count how many activities were deleted


# loop through patterns in dictionary to aggregate activity mentions
for(i in 1:nrow(dict)){
  pattern <- dict$pattern[i]
  transport_activity <- dict$transport_activity[i]
  
  print(paste("Trying to assign activities that match pattern", pattern, "to the overarching transport activity", transport_activity))
  
  
  
  # get activities that match pattern
  df_temp <- act_matches %>% select(matches(pattern)) # get all activities in act_matches that are like pattern (irrespective of location/transport mode)
  
  
  
  # create temporary df to aggregate the values per location / transport mode
  df_temp_agg <- data.frame(matrix(nrow = nrow(df_temp), ncol = length(unique(location_transport_activities))))
  names(df_temp_agg) <- unique(location_transport_activities)
  df_temp_agg[is.na(df_temp_agg)] <- 0 # replace NA with 0 to fill df_temp_agg
  
  
  
  for(activity in names(df_temp)){ # loop through activities to be aggregated
    
    location <- substr(activity, 6, 7) # get location of specific activity
    location_transport_activity <- paste(transport_activity, location, sep = "_") # bind location and related transport_activity together
    
    
    df_temp_agg[location_transport_activity] <- df_temp_agg[location_transport_activity] + df_temp[activity] # add up mentions of activity and transport activity
    
    
    df_temp <- df_temp %>% select(-activity) # remove activity from df_temp
    df_activities <- df_activities %>% select(-activity) # remove activity from df_activities
    
    count_deletedActivities <- count_deletedActivities + 1
    
    
    print(paste(activity, "added to", location_transport_activity))
  }
  
  
  
  # add values of df_temp_agg to df_activities
  df_activities[, names(df_temp_agg)] <- df_activities[, names(df_temp_agg)] + df_temp_agg
  
  print(paste("Activities matching", pattern, "were added to", transport_activity))
  
  
  
  rm(df_temp, df_temp_agg)
}

print(paste(count_deletedActivities, "activities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))






# there are some transportation activities that do not have a location (transport) associated with them
# I will add 20 (unspecified transport) to them

pattern <- "^9[0-8][0-9]{2}$"

act_matches <- df_activities %>% select(matches(pattern)) # get a df that contains all columns with variables that match subactivity pattern

count_newActivities <- 0 # to count how many superactivities were created
count_deletedActivities <- 0 # to count how many activities were deleted

for(activity in names(act_matches)){
  superactivity <- paste0(activity, "_20") # add transport 20
  
  # if(superactivity == "9600_20") superactivity <- "9600_20" # in case of the superactivity "9600", I assign it to "9660"
  
  if(!(superactivity %in% names(df_activities))){ # if superactivity does not exist in df_activities yet
    df_activities[[superactivity]] <- 0 # create superactivity column
    count_newActivities <- count_newActivities + 1
    print(paste("Created activity", superactivity))
  }
  
  df_activities[superactivity] <- df_activities[superactivity] + df_activities[activity] # add number of mentions of activity to number of mentions of superactivity
  df_activities <- df_activities %>% select(-activity) # delete activity column from df_activities
  
  count_deletedActivities <- count_deletedActivities + 1
  
  print(paste(activity, "added to", superactivity)) # confirm output
}

print(paste(count_newActivities, "new superactivities were added to df_activities"))
print(paste(count_deletedActivities, "activities were deleted from df_activities"))
print(paste("df_activities currently has", ncol(df_activities), "columns."))










# calculate total number of hours spent at home
df_activities$home <- rowSums(df_time_location == "11", na.rm = TRUE) # sum up number of times that a person spent at home










# sort according to variable names
df_activities <- df_activities %>%
  select(RINPERSOON, sort(names(df_activities)[2:ncol(df_activities)]))


# now df_activities contains 115 variables

# turn units (10 minutes) into hours per week
df_hours <- round(((df_activities[2:ncol(df_activities)] * 10)/60), 2)
df_activities[2:ncol(df_activities)] <- df_hours

colnames(df_activities)[2:ncol(df_activities)] <- paste("activity", colnames(df_activities)[2:ncol(df_activities)], sep = "_")



# add enq datum to df
df_tbo <- read.spss("G:/VrijetijdCultuur/TBO/2016/TBO2016V2.sav", to.data.frame = TRUE)
df_activities <- merge(df_tbo %>% select(enq_datum, RINPERSOON), df_activities, by = 'RINPERSOON', all.y = TRUE)

df_activities$enq_datum <- str_pad(as.character(df_activities$enq_datum), width = 8, side = "left", pad = 0)



# save as csv
write.csv(df_activities, "F:/Documents/Data/TBO_aggregated.csv", row.names = FALSE)
write_parquet(df_activities, "F:/Documents/Data/TBO_aggregated.parquet")
write_parquet(df_activities, "F:/Documents/time_emissions/processed_data/true/timeuse.parquet")


