library(paletteer)

palette <- paletteer_d("beyonce::X40")

palette_modelComparison <- c(baseline = palette[1], ML = palette[3], true = palette[4])
palette_gender <- c(Men = palette[7], Women = palette[8])
palette_expenseCategories <- c(Food = palette[5], 
                               Housing = palette[4], 
                               Freetime = palette[2], 
                               Transport = palette[1], 
                               Other = palette[6])

set_theme <- function(palette = palette){
  theme <- list(scale_fill_manual(values = palette),
                scale_colour_manual(values = palette),
                theme_bw(base_size = 16))
  
  return(theme)
}


theme_modelComparison <- set_theme(palette_modelComparison)
theme_gender <- set_theme(palette_gender)
theme_expenseCategories <- set_theme(palette_expenseCategories)
theme <- set_theme(palette)
