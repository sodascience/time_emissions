library(tidyverse)


# main function to group activities
groupActivities <- function(df, output_days = 7){
  
  # create dictionary for activity codes
  dict <- data.frame(row.names = c("personal",
                                   "contracted",
                                   "committed",
                                   "free",
                                   "transport"))
  dict$activity_code <- ""
  
  # fill dict
  dict["personal", "activity_code"]   <- "(0[0-9]{3})|(99[0-9]{2})"
  dict["contracted", "activity_code"] <- "(1|2)[0-9]{3}"
  dict["committed", "activity_code"]  <- "(3|4)[0-9]{3}"
  dict["free", "activity_code"]       <- "(5|6|7|8)[0-9]{3}"
  dict["transport", "activity_code"]  <- "9[0-9]{3}"
  
  
  
  # make df for result
  df_categories <- data.frame(row.names = row.names(df))
  
  
  # group activities and add dataframe to list
  for(cat in row.names(dict)){ # loop through selected activity categories
    
    activity_code <- dict[cat, "activity_code"]
    
    # select variables based on combined_code
    df_activities <- df %>%
      select(matches(activity_code))
    
    print("Row-summing:")
    print(cat)
    print(summary(df_activities))
    
    # sum up emissions from all activities associated with activity_code
    df_categories[cat] <- rowSums(df_activities, na.rm = T) # add result to dataframe
  }
  
  df_categories <- df_categories / 7 * output_days
  
  df_categories$RINPERSOON <- df$RINPERSOON
  
  return(df_categories)
}




calc_totalActivities <- function(df, total_name = "total"){
  total <- rowSums(
    abs(
      df %>%
        select(where(is.numeric))
    )
  )
  
  df_total <- data.frame(
    RINPERSOON = df$RINPERSOON
  )
  
  df_total[total_name] <- total
  
  return(df_total)
}

