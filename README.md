# Time-use Imputation for Modelling Emissions (TIME)

This project explores how we can use machine-learning techniques to impute survey data for individuals outside the original sample based on Dutch register data. 
This way, multiple non-overlapping samples can be imputed for the entire Dutch population and combined with each other to generate new insights.

## Context

This project is situated in the context of climate sociology.
The goal is to understand the relationship between individual time-use and household carbon emissions.
To achieve this, we use input-output analysis to estimate household carbon emissions based on household expenditure data. Then, we assign these household emissions to the individual household members based on their time-use.

However, the samples of the time-use and expenditure surveys are non-overlapping and therefore cannot be directly linked to each other.
This presents the case study for this project: 
To assign the household emissions to the individual household members, we need a dataset that contains both types of information for the *same individuals*.

To create this overlapping dataset, we use machine-learning techniques to impute or predict the survey data for individuals outside the original sample based on Dutch register data (see steps 1-4 in the workflow below).
Then, we estimate the household carbon emissions from the predicted household expenditures using input-output analysis (step 5).
Eventually, we assign these emissions to the individual household members based on their predicted individual time-use (step 6). 



## Workflow

1. Integrate and preprocess demographic data (from register datasets / CBS microdata)
2. Preprocess and clean survey datasets (time-use and expenditure surveys)
3. Train and evaluate machine learning models to predict a survey
4. Generate population-level predictions from the fitted model
5. Conduct input-output analysis to estimate the carbon intensity of expenditure categories
6. Assign household emissions to individual household members based on their predicted time-use


### Setup

This code is designed to run on the CBS Microdata environment. Therefore no datafiles are available on github. The package requirements can be found in requirements.txt. You can read more about creating a python environment on the CBS Microdata environment [here](https://github.com/sodascience/cbs_python/).


### Overview of Main Scripts

| Script                        | Description                           | Outcome                                                                                       |
| ----------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------- | 
| `01_load_demographics.py`  | Loads multiple CBS datasets and creates the features needed for the machine-learning models at the individual or household level      | `Parquet` files for each feature (at individual & at household level; *population data*) | 
| `02_process_survey.py`        | Processes survey to be predicted      | `Parquet` file containing id variables and all outcome variables to be predicted (*survey data*)              |
| `03_train_models.py`           | Trains, tests, tunes, and fits the models that are used to predict the survey data | `Joblib` file containing the final fitted model                               | 
| `04_predict_surveys.py`        | Predicts survey data at the population level | `Parquet` file containing id variables and all predicted survey variables (*population data*)         |
| `05_input_output_analysis.py` | Conducts the input-output analysis to estimate the carbon intensity (kg CO² / € spent) of expenditure categories | `csv` file containing the emission intensities per expenditure category         |
| `06_assign_emissions_to_ind.py` | Calculates the household emissions from the predicted household expenditures and assigns them to the different household members based on their predicted individual time-use | `Parquet` files containing id variables and (a) the household carbon emissions and (b) the individual carbon emissions (*population data*)         |


### 1. Load Demographics

We load the demographic features that are used to predict the survey data. 
These features are derived from multiple CBS datasets and contain information about the individuals and households in the Netherlands.
The script `01_load_demographics.py` creates `Parquet` files for each feature (at individual & at household level). This is data at the population level.


### 2. Process Survey Data

We process the surveys that we aim to predict. Of course, this processing is highly survey specific. The resulting datasets only contain id variables and the survey variables to be predicted. 

For the **time-use survey**, we have aggregated all primary and secondary activities to obtain the number of hours that each person spends on 113 activities (e.g. 'eating', 'showering', 'preparing food', ...).

For the **expenditure survey**, we have aggregated all household expenditures to a higher (i.e. less detailed) level. Specifically, the dataset now contains variables indicating how much money each household spent on 156 categories (e.g. 'meat', 'vegetables', 'clothes', 'gasoline', 'furniture', ...).

### 3. Train & Test Models

We train the machine learning models to predict the outcome variables of each survey (step 2) using the demographic features created in step 1. 
Specifically, we train a model to 85% of the survey data (for each survey) and tune the hyperparameters (if applicable) on a 5-fold cross-validation. 
Then, we evaluate the prediction quality on the remaining 15% of the data (of each survey). 
This process can be performed for different kinds of models. In our case, we train a baseline model as well as a machine learning model per survey.
Finally, we fit the best model to the training data. The result is a fitted model stored as a `joblib` file that can be used to predict survey data at the population level.

###  4. Predict at the Population Level

We use the fitted model that was created in the last step to predict survey data at the population level. 
The result is a dataset consisting of multiple `Parquet` files that contain id variables together with the predicted outcome variables for the respective survey.

---

*The following steps are highly context-specific and depend on the research question. Please see the `Context` section above for more details.*

### 5. Input-Output Analysis

We conduct an input-output analysis to estimate the carbon intensity (kg CO² / € spent) of expenditure categories. The result is a `csv` file containing the emission intensities per expenditure category.

### 6. Assign Emissions to Individuals

We calculate the household emissions from the predicted household expenditures and assign them to the different household members based on their predicted individual time-use. 
To do this, we use a [concordance table](processed_data/meta/mapping_budget-TBO.xlsx) that matches each expenditure variable to a timeuse variable.
The results are stored in `Parquet` files that contain id variables and either (a) the household carbon emissions or (b) the individual carbon emissions.

### 7. Analyse

We analyse the population-level data. In our case, we analyse demographic patterns in individual carbon emissions.

*This code is still under development* 


## Contact

This is a project by the [ODISSEI Social Data Science team](https://odissei-soda.nl/). Do you have any questions or suggestions? Please contact [Maike Weiper](https://github.com/MWeiper).

<img src="https://odissei-soda.nl/images/logos/soda_logo.svg" alt="SoDa logo" width="250px"/> 
