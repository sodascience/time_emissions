import polars as pl

from sklearn.model_selection import train_test_split


# Define data types for demographic features to be used in model training
features = {
    "TYPHH":                        pl.Categorical,             # type huishouden
    "PLHH":                         pl.Categorical,             # plaats van persoon in huishouden
    "AANTALPERSHH":                 pl.Int64,                   # aantal personen in huishouden
    "AANTALKINDHH":                 pl.Int64,                   # aantal kinderen in huishouden
    "GEBJAARJONGSTEKINDHH":         pl.Int64,                   # geboortejaar jongste kind in huishouden
    "GEBJAAROUDSTEKINDHH":          pl.Int64,                   # geboortejaar oudste kind in huishouden
    "GBAGEBOORTELAND":              pl.Categorical,             # Geboorteland
    "GBAGESLACHT":                  pl.Categorical,             # Geslacht
    "GBAGEBOORTEJAAR":              pl.Int64,                   # Geboortejaar
    "GBAHERKOMSTGROEPERING":        pl.Categorical,             # Migratieachtergrond (CBS definitie)
    "GBAGENERATIE":                 pl.Categorical,             # Generatie
    "OPLNIVSOI2016AGG4HGMETNIRWO":  pl.Categorical,             # opleidingsniveau (SOI 2016) in 18 categorieen
    "INPEMFO":                      pl.Categorical,             # Financiële onafhankelijkheid van de persoon
    "INPKKGEM":                     pl.Float64,                 # Gemiddelde koopkracht van de persoon in jaar t-1 en t, in prijspeil van jaar t.
    "INPPERSINK":                   pl.Float64,                 # Persoonlijk inkomen
    # "INPPINK":                      pl.Categorical,             # Indicator persoon met inkomen
    "INPSECJ":                      pl.Categorical,             # Sociaaleconomische categorie op jaarbasis
    # "INPT6325KGB":                  pl.Float64,                 # Kindgebonden budget
    "SECM":                         pl.Categorical,             # Sociaaleconomische categorie
    "VEHW1100BEZH":                 pl.Float64,                 # bezittingen van het huishouden
    "VEHW1200STOH":                 pl.Float64,                 # schulden van het huishouden
    "VEHW1121WONH":                 pl.Float64                  # eigen woning van het huishouden
}




def load_df(train_test = True):
    """
    Load and prepare the main dataframe by joining demographic and target data.

    Args:
        train_test (bool): Whether to split the data into training and testing samples.

    Returns:
        pl.DataFrame: Prepared dataframe with demographic and target data, optionally split into train/test samples.
    """

    # Y -----
    df_y = pl.read_parquet("F:/Documents/Data/TBO_aggregated.parquet")

    # X -----
    df_x = (
        pl.read_parquet("F:/Documents/Data/df_demographics.parquet")
        .join(df_y, on = "RINPERSOON", how = "semi")
    )

    # JOIN -----
    df = df_x.join(df_y, on = "RINPERSOON")

    if train_test:
        # add split_sample variable to df_true
        # split_sample indicates whether a record belongs to the train or test sample
        df = split_sample(df)

    return df




def split_sample(df, test_size = 0.2):
    """
    Splits sample into train and test samples and indicates this with a new variable called split_sample

    Args:
        df (pl.DataFrame): dataframe to be split
        test_size (float): proportion of df to be used as test sample (default: 0.2)
    
    Returns:
        pl.DataFrame: df with a new variable called split_sample
    """

    df_train, df_test = train_test_split(df, test_size = test_size, random_state = 42)


    # create split_sample variable
    df = df.with_columns(
        # when in training dataset
        pl.when(pl.col("RINPERSOON").is_in(df_train["RINPERSOON"]))
        .then(pl.lit("train"))
        # when in test dataset
        .when(pl.col("RINPERSOON").is_in(df_test["RINPERSOON"]))
        .then(pl.lit("test"))
        # otherwise
        .otherwise(pl.lit(None))
        .alias("split_sample") # name of the variable
    )

    return df
