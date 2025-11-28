# Time-use Imputation for Modelling Emissions (TIME)

This project explores how we can leverage Dutch register data to impute survey data for individuals outside the original sample.

In the context of climate sociology, we use household expenditure and individual time-use data as example surveys. The resulting predictions can be combined to estimate individual and household carbon emissions at the population level.



This repository is currently under development.



## Workflow

1. Integrate and preprocess demographic data (from register datasets / CBS microdata)
2. Preprocess and clean survey datasets (e.g., time-use or expenditure surveys)
3. Train and evaluate machine learning models to predict a survey
4. Generate population-level predictions from the fitted model
5. Integrate population-level surveys with each other


### Overview of Main Scripts

| Script                        | Description                           | Outcome                                                                                       |
| ----------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------- | 
| `01_process_demographics.py`  | Integrates multiple CBS datasets      | `Parquet` file containing all relevant demographic data (at individual & at household level; *population data*) | 
| `02_process_survey.py`        | Processes survey to be predicted      | `Parquet` file containing one id variable and all survey variables to be predicted (*survey data*)              |
| `03_train_model.py`           | Trains, tests, and fits the model that is used to predict survey data | `Joblib` file containing the final fitted model                               | 
| `04_predict_survey.py`        | Predicts survey data at the population level | `Parquet` file containing one id variable and all predicted survey variables (*population data*)         |


### 1. Process Demographics

First, we create the demographic dataset that contains the features (predictors) of the models. For this, we read in multiple CBS datasets, process their data, and integrate them into the main dataset.

Since the surveys the we are working with contain data at the individual (timeuse) and household (expenditure) level, we create two versions of the same demographic dataset - one at each level of the data.

### 2. Process Survey Data

Second, we process the surveys that we aim to predict. Of course, this processing is highly survey specific. The resulting datasets only contain an id variable and the survey variables to be predicted. 

For the **time-use survey**, we have aggregated all primary and secondary activities to obtain the number of hours that each person spends on 113 activities (e.g. 'eating', 'showering', 'preparing food', ...).

For the **expenditure survey**, we have aggregated all household expenditures to a higher (i.e. less detailed) level. Specifically, the dataset now contains variables indicating how much money each household spent on 156 categories (e.g. 'meat', 'vegetables', 'clothes', 'gasoline', 'furniture', ...).

### 3. Train & Test Models

Third, we train, test, and fit the machine learning model to each survey. Specifically, we first train a model to 80% of the survey data (for each survey). Then, we evaluate the prediction quality on the remaining 20% of the data (of each survey). This process can be performed for different kinds of models, such as a baseline model and a machine learning model, to compare the prediction qualities with each other. Eventually, this process will also entail hyperparameter tuning (currently under development).

Lastly, we fit the model to the whole survey dataset. The resulting model will be used for the survey predictions in the next step.

###  4. Predict at the Population Level

Fourth, we use the fitted model that was created in the last step to predict survey data at the population level. The result is a dataset that contains an id variable together with the predicted variables for the respective survey.

### 5. Integrate Population-Level Surveys

Fifth, we integrate the two surveys with each other. This is a highly context-specific process. In our case, we use a [concordance table](processed_data/meta/mapping_budget-TBO.xlsx) that matches each expenditure variable to a timeuse variable. This allowed us to assign the carbon emissions - calculated from the (predicted) expenditures - to each individual living in a household, on the basis of their predicted timeuse.

*Please note, the code is currently under development*

### 6. Analyse

Sixth, we analyse the population-level data. In our case, we analyse demographic patterns in individual carbon emissions.

*Please note, the code is currently under development*



## Contact

This is a project by the [ODISSEI Social Data Science team](https://odissei-soda.nl/). Do you have any questions or suggestions? Please contact [Maike Weiper](https://github.com/MWeiper).

<img src="https://odissei-soda.nl/images/logos/soda_logo.svg" alt="SoDa logo" width="250px"/> 
