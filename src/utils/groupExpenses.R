library(tidyverse)


groupExpenses_food <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST011", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$BreadGrains <- rowSums(df[, which(grepl("BOBEST0111", names(df)))])
  df <- df %>% select(-grep("BOBEST0111", names(df), value = TRUE))
  
  df$Meat <- rowSums(df[, which(grepl("BOBEST0112", names(df)))])
  df <- df %>% select(-grep("BOBEST0112", names(df), value = TRUE))
  
  df$AnimalProducts <- rowSums(df[, which(grepl("BOBEST0113|BOBEST0114", names(df)))])
  df <- df %>% select(-grep("BOBEST0113|BOBEST0114", names(df), value = TRUE))
  
  df$OtherFood <- rowSums(df[, which(grepl("BOBEST011", names(df)))])
  df <- df %>% select(-grep("BOBEST011", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_drinks <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST012|BOBEST02", names(df)))]
  
  df$WarmDrinks <- rowSums(df[, which(grepl("BOBEST0121", names(df)))])
  df <- df %>% select(-grep("BOBEST0121", names(df), value = TRUE))
  
  df$ColdDrinks <- rowSums(df[, which(grepl("BOBEST0122", names(df)))])
  df <- df %>% select(-grep("BOBEST0122", names(df), value = TRUE))
  
  df$AlcoholEtc <- rowSums(df[, which(grepl("BOBEST02", names(df)))])
  df <- df %>% select(-grep("BOBEST02", names(df), value = TRUE))
  
  return(df)
}



groupExpenses_housing <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST04|BOBEST05", names(df)))]
  
  # sum up CO2 per categories and then remove subcategories
  df$Housing_general <- rowSums(df[, which(grepl("BOBEST041|BOBEST042|BOBEST043|BOBEST044", names(df)))])
  df <- df %>% select(-grep("BOBEST041|BOBEST042|BOBEST043|BOBEST044", names(df), value = TRUE))
  
  df$Utilities <- rowSums(df[, which(grepl("BOBEST045", names(df)))])
  df <- df %>% select(-grep("BOBEST045", names(df), value = TRUE))
  
  df$HouseholdGoods <- rowSums(df[, which(grepl("BOBEST05", names(df)))])
  df <- df %>% select(-grep("BOBEST05", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_transport <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST07", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$PrivateTransport_purchases <- rowSums(df[, which(grepl("BOBEST071", names(df)))])
  df <- df %>% select(-grep("BOBEST071", names(df), value = TRUE))
  
  df$PrivateTransport_maintenance <- rowSums(df[, which(grepl("BOBEST072", names(df)))])
  df <- df %>% select(-grep("BOBEST072", names(df), value = TRUE))
  
  df$PublicTransport_Land <- rowSums(df[, which(grepl("BOBEST0731|BOBEST0732|BOBEST0734|BOBEST0735|BOBEST0736", names(df)))])
  df <- df %>% select(-grep("BOBEST0731|BOBEST0732|BOBEST0734|BOBEST0735|BOBEST0736", names(df), value = TRUE))
  
  df$PublicTransport_Air <- df[, which(grepl("BOBEST0733", names(df)))]
  df <- df %>% select(-grep("BOBEST0733", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_freeTime <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST03|BOBEST08|BOBEST09", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$Clothing <- rowSums(df[, which(grepl("BOBEST03", names(df)))])
  df <- df %>% select(-grep("BOBEST03", names(df), value = TRUE))
  
  df$Communication <- rowSums(df[, which(grepl("BOBEST08", names(df)))])
  df <- df %>% select(-grep("BOBEST08", names(df), value = TRUE))
  
  df$ElectronicDevices <- rowSums(df[, which(grepl("BOBEST091", names(df)))])
  df <- df %>% select(-grep("BOBEST091", names(df), value = TRUE))
  
  df$FreeTime_Goods <- rowSums(df[, which(grepl("BOBEST092", names(df)))])
  df <- df %>% select(-grep("BOBEST092", names(df), value = TRUE))
  
  df$PetsAndOutdoor_Goods <- rowSums(df[, which(grepl("BOBEST093", names(df)))])
  df <- df %>% select(-grep("BOBEST093", names(df), value = TRUE))
  
  # Remove services and package trips; they will go into the next plot
  df <- df %>% select(-grep("BOBEST094", names(df), value = TRUE))
  df <- df %>% select(-grep("BOBEST096", names(df), value = TRUE))
  
  df$Printed_Goods <- rowSums(df[, which(grepl("BOBEST095", names(df)))])
  df <- df %>% select(-grep("BOBEST095", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_freeTimeServices <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST094|BOBEST096|BOBEST11|BOBEST12", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$Services <- rowSums(df[, which(grepl("BOBEST094", names(df)))])
  df <- df %>% select(-grep("BOBEST094", names(df), value = TRUE))
  
  df$PackageTrips <- df[, which(grepl("BOBEST096", names(df)))]
  df <- df %>% select(-grep("BOBEST096", names(df), value = TRUE))
  
  df$HotelsRestaurants <- rowSums(df[, which(grepl("BOBEST11", names(df)))])
  df <- df %>% select(-grep("BOBEST11", names(df), value = TRUE))
  
  df$BodyCare <- rowSums(df[, which(grepl("BOBEST121|BOBEST122|BOBEST123", names(df)))])
  df <- df %>% select(-grep("BOBEST121|BOBEST122|BOBEST123", names(df), value = TRUE))
  
  df <- df %>% select(-grep("BOBEST12", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_administration <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST124|BOBEST125|BOBEST126|BOBEST127|BOBEST13|BOBEST15", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$SocialSecurity <- rowSums(df[, which(grepl("BOBEST124|BOBEST125", names(df)))])
  df <- df %>% select(-grep("BOBEST124|BOBEST125", names(df), value = TRUE))
  
  df$FinancialServices <- rowSums(df[, which(grepl("BOBEST126|BOBEST127", names(df)))])
  df <- df %>% select(-grep("BOBEST126|BOBEST127", names(df), value = TRUE))
  
  df$Taxes <- rowSums(df[, which(grepl("BOBEST13", names(df)))])
  df <- df %>% select(-grep("BOBEST13", names(df), value = TRUE))
  
  df$Donations <- rowSums(df[, which(grepl("BOBEST15", names(df)))])
  df <- df %>% select(-grep("BOBEST15", names(df), value = TRUE))
  
  return(df)
}


groupExpenses_medicalEdu <- function(df){
  # get data
  df <- df[, which(grepl("BOBEST06|BOBEST10", names(df)))]
  
  
  # sum up CO2 per categories and then remove subcategories
  df$Medical <- rowSums(df[, which(grepl("BOBEST06", names(df)))])
  df <- df %>% select(-grep("BOBEST06", names(df), value = TRUE))
  
  df$Education <- rowSums(df[, which(grepl("BOBEST10", names(df)))])
  df <- df %>% select(-grep("BOBEST10", names(df), value = TRUE))
  
  return(df)
}


groupExpenses <- function(df){
  df_administration <- groupExpenses_administration(df) %>%
    rename_with(~ paste0("admin_", .x))
  
  df_drinks <- groupExpenses_drinks(df) %>%
    rename_with(~ paste0("drinks_", .x))
  
  df_food <- groupExpenses_food(df) %>%
    rename_with(~ paste0("food_", .x))
  
  df_freeTime <- groupExpenses_freeTime(df) %>%
    rename_with(~ paste0("freeTime_", .x))
  
  df_freeTimeServices <- groupExpenses_freeTimeServices(df) %>%
    rename_with(~ paste0("freeTimeServices_", .x))
  
  df_housing <- groupExpenses_housing(df) %>%
    rename_with(~ paste0("housing_", .x))
  
  df_medicalEdu <- groupExpenses_medicalEdu(df) %>%
    rename_with(~ paste0("medicalEdu_", .x))
  
  df_transport <- groupExpenses_transport(df) %>%
    rename_with(~ paste0("transport_", .x))
  
  
  df_grouped <- cbind(df_administration,
                      df_drinks,
                      df_food,
                      df_freeTime,
                      df_freeTimeServices,
                      df_housing,
                      df_medicalEdu,
                      df_transport)
  
  return(df_grouped)
}









plotExpenses <- function(df, limit_x = "default", subtitle = "", saveAs = NULL){
  # turn into long format
  df$id <- row.names(df)
  df_long <- melt(df)
  
  
  # many values are zero, which messes up the plot, so I want to know the range of values that are > 0
  range_non_zero <- range(df_long$value[df_long$value > 0])
  print(range_non_zero)
  
  if(limit_x == "default"){
    limit_x <- range_non_zero[2]
  }
  
  if(limit_x == "95_percentile"){
    limit_x <- quantile(df_long$value, 0.95)
  }
  
  # make plot
  plot <- ggplot(df_long, mapping = aes(x = value, color = variable, fill = variable)) + 
    geom_density(alpha = 0.2) + 
    # coord_cartesian(xlim = c(range_non_zero[1], limit_x)) +
    xlim(range_non_zero[1], limit_x) +
    theme_minimal() +
    labs(title = "GHG footprint", subtitle = subtitle) + xlab("GHG Emissions (kg CO2 Equivalent)")
  
  print(plot)
  
  if(!is.null(saveAs)){
    # save plot
    ggsave(saveAs, plot)
  }
}

