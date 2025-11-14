library(foreign)
library(data.table)
library(tidyverse)
library(nanoparquet)

budget_df <- read.spss("G:/InkomenBestedingen/BUDGETONDERZOEK/2015/BUDGETONDERZOEK2015V4.sav", to.data.frame = TRUE)
var_labels <- data.frame(var = names(budget_df), label =  attr(budget_df, "variable.labels"))





##### CATEGORIES #####

# find variables that end with 00H
categories <- budget_df %>% select(ends_with("00H")) # Find all variables subcategories of category_var
categories <- var_labels[which(grepl("[1-9]00H$", var_labels$var)),]


# function to compare total expenditure category to sum of subcategories
compare_categorySubcategories <- function(category){
  category_name <- category$label
  category_var <- category$var
  category_var_stem <- sub("00H$", "", category_var)
  
  subcategories_var <- budget_df %>% select(num_range(category_var_stem, 10:99, "H")) # Find all variables subcategories of category_var
  
  # compare
  sum <- round(rowSums(subcategories_var), digits = 2) # sum up expenditures of all subcategories
  expend_category <- round(budget_df[[category_var]], digits = 2) # get expenditure of category 
  areEqual <- abs(sum - expend_category) < 1 # check whether the difference between sum and expend_category is < 1
  df <- data.frame(sum, expend_category, areEqual) # put in df
  
  # summary(df) # return summary of df
  unequal <- df[which(!df$areEqual),] # rows in which they are not equal
  output <- paste("There are", nrow(unequal), "households in which the sum of the subcategories does not match the total expenditure of the category", category_name)
  
  return(output)
}


# function to remove the variables of the subcategories (if sum of subcategories = total expenditure category)
remove_subcategories <- function(category, df, exception_vars = c()){
  category_name <- category$label
  category_var <- category$var
  category_var_stem <- sub("00H$", "", category_var)
  
  # find all variables subcategories of category_var
  subcategories_var <- df %>% select(num_range(category_var_stem, 10:99, "H")) 
  
  # subtract exception expenditures from category expenditure
  for(exception_var in exception_vars){
    print(paste("Exception:", exception_var))
    df[, category_var] <- df[, category_var] - df[, exception_var]
  }
  
  # remove exceptions from var list to be deleted
  subcategories_var <- subcategories_var %>% select(-all_of(exception_vars))
  
  # remove subcategories from df
  df <- df %>% select(-names(subcategories_var))
  
  print(paste("The following variable was removed:", names(subcategories_var)))
  return(df)
}


category_temp <- categories[1,] # Brood & granen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST011110H", "BOBEST011170H"))

category_temp <- categories[2,] # Vlees
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST011210H", "BOBEST011220H", "BOBEST011240H"))

category_temp <- categories[3,] # Vis en schaal- en schelpdieren
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[4,] # Melk, kaas, en eieren
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST011410H", "BOBEST011420H", "BOBEST011430H"))

category_temp <- categories[5,] # Olien en vetten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[6,] # Fruit
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[7,] # Groenten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[8,] # Suiker, zoetwaren, ijs
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[9,] # Voedingsmiddelen niet elders genoemd
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[10,] # Koffie, thee en cacao
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST012110H", "BOBEST012120H", "BOBEST012130H"))
# remove category (because all subcategories were retained)
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[11,] # Mineraalwater, frisdranken, sappen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST012210H", "BOBEST012220H", "BOBEST012230H"))
# remove category (because all subcategories were retained)
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[12,] # Gedistilleeerde dranken
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[13,] # Wijn
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[14,] # Bier
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST022000H", label = "Tabak") # Tabak
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[16,] # Kleding
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[17,] # Overige kledingartikelen en toebehoren
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[18,] # Stomen en reparatie van kleding
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[19,] # Schoenen en ander schoeisel
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[22,] # Overige werkelijke woninghuur
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[26,] # Onderhoudsdiensten voor de woning
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[30,] # Overige kosten van woningvoorziening
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[32,] # Gas
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[34,] # Vaste brandstoffen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[35,] # Onderhoudsdiensten voor de woning
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[36,] # Onderhoudsdiensten voor de woning
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST051230H")

category_temp <- data.frame(var = "BOBEST052000H", label = "Huishoudtextiel") # Onderhoudsdiensten voor de woning
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST052040H")

category_temp <- categories[38,] # Grote huishoudelijke apparaten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[39,] # Kleine elektrische huishoudelijke apparaten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST054000H", label = "Glas, services, en huishoudelijke artikelen") # Onderhoudsdiensten voor de woning
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[41,] # Grote gereedschappen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[42,] # Kleine gereedschapen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST055230H")

category_temp <- categories[43,] # Niet-duurzame huishoudproducten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[44,] # Huishoudelijke diensten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST056230H")

category_temp <- categories[46,] # Overige medische producten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[47,] # Therapeutische apparaten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST061330H")

category_temp <- categories[48,] # Diensten van artsen en paramedici
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[50,] # Diensten van paramedici
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST062310H")

category_temp <- categories[51,] # Autos
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[55,] # Benodigheden prive-voertuigen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[56,] # Brandstoffen en smeermiddelen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[58,] # Overige diensten prive-voertuigen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[59,] # Personenvervoer per spoor
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[60,] # Personenvervoer over de weg
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[61,] # Personenvervoer door de lucht
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[62,] # Personenvervoer over water
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[64,] # Overige aankopen van vervoersdiensten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST081000H", label = "Post- en pakketdiensten")
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[65,] # TV, audio- en video-apparatuur
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[66,] # Foto-, film- en optische apparatuur
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[67,] # Gegevensverwerkende apparatuur
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST091330H")

category_temp <- categories[68,] # Informatiedragers
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST091410H", "BOBEST091420H"))

category_temp <- categories[70,] # Goederen voor outdoor recreatie
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[71,] # Goederen voor indoor recreatie
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST092210H")

category_temp <- categories[73,] # Spellen, speelgoed en hobby's 
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[74,] # Sport en kampeerartikelen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = "BOBEST093230H")

category_temp <- categories[75,] # Tuinen, planten, en bloemen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[76,] # huisdieren
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[78,] # Diensten voor recreatie en sport
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[79,] # Culturele diensten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df, exception_vars = c("BOBEST094210H", "BOBEST094220H", "BOBEST094250H"))

category_temp <- categories[81,] # Boeken
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[82,] # Kranten en Tijdschriften
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[84,] # Schrijfwaren en tekenartikelen
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST096000H", label = "Pakketreizen")
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST101000H", label = "Kleuter- en primair onderwijs")
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[85,] # Restaurants, cafes
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST112000H", label = "Accommodaties")
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[87,] # Kappers en Schoonheidssalons
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[88,] # Elektrische toestellen voor lichaamsverzorgingn en reparatie
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[89,] # Overige producten voor lichaamsverzorging
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[90,] # Sieraden, klokken, horloges
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[91,] # Overige artikelen voor persoonlijk gebruik
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- data.frame(var = "BOBEST124000H", label = "Sociale bescherming")
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[93,] # Verzekering in verband met ziekte
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[94,] # Verzekering in verband met vervoer
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)

category_temp <- categories[97,] # Overige financiele diensten
compare_categorySubcategories(category_temp) # equal
budget_df <- remove_subcategories(category_temp, budget_df)



##### SUPERCATEGORIES #####


# check whether sum of categories matches the expenditures in supercategory (e.g.  Voedingsmiddelen; Voedingsmiddelen en alcohol vrije drank; Alle bestedingen)
# if they match, then delete supercategory

# find variables that end with 000H
categories <- var_labels[which(grepl("[1-9]000H$", var_labels$var)),]


# function to compare total expenditure category to sum of subcategories
compare_supercategoryCategories <- function(category){
  category_name <- category$label
  category_var <- category$var
  category_var_stem <- sub("000H$", "", category_var)
  
  # subcategories_var <- budget_df %>% select(num_range(category_var_stem, 001:999, "H")) # Find all variables subcategories of category_var
  
  padded_numbers <- sprintf("%03d", 1:999)
  matching_vars <- paste0(category_var_stem, padded_numbers, "H")
  subcategories_var <- budget_df %>% select(any_of(matching_vars))
  
  print(paste("Categories of the supercategory", category_name))
  print(names(subcategories_var))
  
  # compare
  sum <- round(rowSums(subcategories_var), digits = 2) # sum up expenditures of all subcategories
  expend_category <- round(budget_df[[category_var]], digits = 2) # get expenditure of category 
  areEqual <- abs(sum - expend_category) < 1 # check whether the difference between sum and expend_category is < 1
  df <- data.frame(sum, expend_category, areEqual) # put in df
  
  # summary(df) # return summary of df
  unequal <- df[which(!df$areEqual),] # rows in which they are not equal
  output <- paste("There are", nrow(unequal), "households in which the sum of the subcategories does not match the total expenditure of the category", category_name)
  
  return(output)
}


category_temp <- categories[1,] # Voedingsmiddelen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[2,] # Alcoholvrije dranken
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[3,] # Alcoholhoudende dranken
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[6,] # Kleding en kledingstoffen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[7,] # Schoenen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[8,] # Werkelijke woninghuur
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[9,] # Toegerekende huur
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[10,] # Onderhoud en reparatie van woning
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[11,] # Kosten van woningvoorzieningen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[12,] # Energie
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[13,] # Meubelen, stoffering, en decoratie
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[15,] # Huishoudelijke apparaten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[17,] # Gereedschappen en werktuigen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[18,] # Dagelijks onderhoud van de woning
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[19,] # Medische producten en apparaten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[20,] # Extramurale gezondheidszorg
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[22,] # Aankoop van voertuigen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[23,] # Gebruik van privé voertuigen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[24,] # Vervoersdiensten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[26,] # Telefoonapparatuur
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[27,] # Telefoondiensten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[28,] # Audio-, video, fotoapparatuur en dergelijke
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[29,] # Goederen recreatie en cultuur
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[30,] # Spelartikelen, planten en huisdieren
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[31,] # Diensten voor recreatie en cultuur
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[32,] # Kranten, boeken, schrijfwaren
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[39,] # Catering diensten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[41,] # Persoonlijke verzorging
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[43,] # Goederen voor persoonlijk gebruik
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[45,] # Verzekeringen
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[46,] # Financiele diensten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[47,] # Overige diensten
compare_supercategoryCategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)



##### SUPERSUPERCATEGORIES #####

# find variables that end with 0000H
categories <- var_labels[which(grepl("[1-9]0000H$", var_labels$var)),]


# function to compare total expenditure category to sum of subcategories
compare_supersupercategorySupercategories <- function(category){
  category_name <- category$label
  category_var <- category$var
  category_var_stem <- sub("0000H$", "", category_var)
  
  # subcategories_var <- budget_df %>% select(num_range(category_var_stem, 001:999, "H")) # Find all variables subcategories of category_var
  
  padded_numbers <- sprintf("%04d", 1:9999)
  matching_vars <- paste0(category_var_stem, padded_numbers, "H")
  subcategories_var <- budget_df %>% select(any_of(matching_vars))
  
  print(paste("Categories of the supercategory", category_name))
  print(names(subcategories_var))
  
  # compare
  sum <- round(rowSums(subcategories_var), digits = 2) # sum up expenditures of all subcategories
  expend_category <- round(budget_df[[category_var]], digits = 2) # get expenditure of category 
  areEqual <- abs(sum - expend_category) < 1 # check whether the difference between sum and expend_category is < 1
  df <- data.frame(sum, expend_category, areEqual) # put in df
  
  # summary(df) # return summary of df
  unequal <- df[which(!df$areEqual),] # rows in which they are not equal
  output <- paste("There are", nrow(unequal), "households in which the sum of the subcategories does not match the total expenditure of the category", category_name)
  
  return(output)
}


category_temp <- categories[1,] # Voedingsmiddelen en alcohol vrije drank
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[2,] # Alcoholhoudende dranken en tabak
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[3,] # Kleding en schoenen
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[4,] # Huisvesting, water, en energie
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[5,] # Stoffering en huishoudelijke apparaten
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[6,] # Gezondheid
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[7,] # Vervoer
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[8,] # Communicatie
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[9,] # Recreatie en cultuur
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[10,] # Restaurants en hotels
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[11,] # Diverse goederen en diensten
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[12,] # Consumptiegebonden belastingen
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)

category_temp <- categories[13,] # Goede doelen
compare_supersupercategorySupercategories(category_temp) # equal
budget_df <- budget_df %>% select(-category_temp$var)




library(stringr)

##### CHECK #####

# for all expenditure categories, check whether the sum of it's subcategories are equal to the expenditure in the category itself
# as we have removed many variables above, and have subtracted the amounts of the subcategories that we do keep from the amount of the category,
# the sum should now not be equal anymore. If the sum is equal, then this variable is redundant and should be deleted

exp_variables <- names(select(budget_df, starts_with("BOBEST")))

for(name in exp_variables){
  name_num <- sub("H$", "", sub("^BOBEST", "", name))
  
  last_nonzero <- max(tail(str_locate_all(name_num, '[^0]')[[1]][,2], n = 1), 2)
  
  name_stem <- substr(name_num, 1, last_nonzero)
  name_stem <- paste("BOBEST", name_stem, sep = "")
  
  subcategories <- grep(name_stem, exp_variables, value = T)
  subcategories <- subcategories[-1] # delete first object of list (because it is the category instead of a subcategory)
  
  if(length(subcategories) > 0){
    # print(paste("I have found the following subcategories of category", name, "with stem", name_stem, ":"))
    # print(subcategories)
    
    # compare sum of subcategories with category expenditure
    data <- budget_df %>% select(all_of(subcategories))
    sum_subcategories <-  round(rowSums(data), digits = 2)
    expenditure_category <- round(budget_df[[name]], digits = 2)
    areEqual <- abs(sum_subcategories - expenditure_category) < 1
    data <- data.frame(sum_subcategories, expenditure_category, areEqual) # put in df
    
    unequal <- data[which(!data$areEqual),] # rows in which they are not equal
    output <- paste("There are", nrow(unequal), "households in which the sum of the subcategories does not match the total expenditure of the category", name)
    
    # by now, the sum of the subcategories should not be equal anymore (because we have already subtracted them from each other)
    if(nrow(unequal) == 0){
      print(output)
    }
    
  }

}


# There are no households in which the sum of the subcategories does not match the total expenditure of the category BOBEST100000H
# So, we should remove BOBEST100000H - Onderwijs

budget_df <- budget_df %>% select(- BOBEST100000H)





# check whether all add up

exp_variables <- select(budget_df, starts_with("BOBEST"))
exp_variables <- exp_variables %>% select(- BOBEST000000H)
exp_variables <- exp_variables %>% select(- BOBESTINKH) # this is the spendable income of the household
exp_variables <- exp_variables %>% select(- BOBESTKINDEROPVANG) # this is not in the COICOP classification

expenditure_all <- select(budget_df, BOBEST000000H)



sum_subcategories <-  round(rowSums(exp_variables), digits = 2)
areEqual <- abs(sum_subcategories - expenditure_all) < 1
data <- data.frame(sum_subcategories, expenditure_all, areEqual) # put in df
names(data) <- c("sum_subcategories", "expenditure_all", "areEqual")

unequal <- data[which(!data$areEqual),] # rows in which they are not equal
output <- paste("There are", nrow(unequal), "households in which the sum of the subcategories does not match the total expenditure")

print(output)

# The total expenditures only matches the sum of the other variables if we leave out BOBESTKINDEROPVANG


budget_df <- budget_df %>% select(- c(BOBEST000000H, BOBESTKINDEROPVANG))

# round expenditure variables to 4 digits 
for(var in 1:ncol(budget_df)){
  if(is.numeric(budget_df[, var]) & grepl('BOBEST', names(budget_df)[var])){
    budget_df[, var] <- round(budget_df[, var], 4)
  }
  else{
    print("Not numeric")
  }
}

##### SAVE #####

write.csv(budget_df, "F:/Documents/Data/budget_df.csv", row.names = F)
write_parquet(budget_df, "F:/Documents/Data/budget_df.parquet")
write_parquet(budget_df, "F:/Documents/R_code/data/true/budget_df.parquet")

