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

### Data output

The project saves its output and temporary data in `data/processed_data/`. You can find an overview of the folders and the files they contain in [`data/processed_data/README.md`](data/processed_data/README.md). Git does not track generated data, and the input data are stored separately.


### Overview of Main Scripts

| Script | Description | Outcome |
| --- | --- | --- |
| `01_load_demographics.py` | Caches register tables and mappings, then builds demographic features for individuals and households. | Cached Parquet tables and year-specific Parquet feature files, split into batches where needed. |
| `02_process_expenditures.py`, `02_process_timeuse.py` | These Python files are placeholders. Survey preparation is currently done by the R scripts in `src/process_surveys/`. | Prepared survey Parquet files. The R scripts currently write them under `H:/Maike/processed_data/surveys/`. |
| `03_train_models.py` | Builds the response and predictor tables, then trains and evaluates each survey's baseline and main model. | `responses_at_unit.parquet`, fitted `pipeline.joblib` files, optional `params.json` files, and `evaluation.parquet`. |
| `04_predict_surveys.py` | Predicts both models for the survey samples and the main model for the population. | Batched Parquet prediction files, with run metadata and completion markers. |
| `05_input_output_analysis.py` | Calculates weighted population expenditure totals for each category. The separate input-output workflow (under `src/input_output_analysis/IO_analysis/`) is used to calculate emission intensities. | `expenditures_population_sums.parquet`; the input-output workflow should provide `emission_intensity_per_expenditure.csv`. |
| `06_assign_emissions_to_ind.py` | Calculates household emissions and distributes them to household members using predicted time-use. | Batched Parquet files for household and individual emissions, with run metadata and completion markers. |


### 1. Load Demographics

We build demographic features from CBS register datasets. The script `01_load_demographics.py` first caches the typed dataset tables and mapping tables, then writes a Parquet file for each feature and year. Feature files may be split into batches and are stored separately for household-month and person-household-month tables. These features describe the population and are later used as model predictors.


### 2. Process Survey Data

Survey preparation is specific to each survey. The Python scripts `02_process_expenditures.py` and `02_process_timeuse.py` are currently placeholders; the actual processing is in `src/process_surveys/expenditures.R` and `src/process_surveys/timeuse.R`. 

For the **time-use survey**, the R script aggregates primary and secondary activities and converts the reported time to average hours per day. Its current output contains 114 activity variables (for example, eating, showering, and preparing food), alongside identifiers and the survey weight.

For the **expenditure survey**, the R script combines expenditure subcategories and converts annual amounts to daily amounts. The resulting file contains household expenditure variables and identifiers.

### 3. Train & Test Models

The Python pipeline reads each prepared survey file and maps its responses to the unit used by that survey's models. It writes `responses_at_unit.parquet` with the unit identifiers, target variables, survey weight when available, and a train/test split. It also builds predictor tables from the demographic features.

For each survey, the pipeline trains a baseline and a main model on the training portion of the data. The split is 85% for training and 15% for testing. If a model has tunable parameters, the pipeline searches them using five-fold cross-validation. It evaluates both models on the test data and saves a fitted `pipeline.joblib` for each one, along with tuning settings and evaluation results where applicable.

###  4. Predict at the Population Level

The pipeline uses each survey's main model to predict its outcomes for the population in each configured year. It also writes predictions from both models for each survey sample. Population predictions are saved as numbered Parquet batches; predictions for a survey sample are written as a single batch. Each completed prediction folder includes run metadata and a `done` marker.

---

*The following steps are highly context-specific and depend on the research question. Please see the `Context` section above for more details.*

### 5. Input-Output Analysis

The script `05_input_output_analysis.py` calculates weighted population expenditure totals and saves them in `input_output_analysis/expenditures_population_sums.parquet`. The separate input-output workflow under `src/input_output_analysis/IO_analysis/` is used to estimate the carbon intensity of each expenditure category. Its result, `emission_intensity_per_expenditure.csv`, is read by the next step.

### 6. Assign Emissions to Individuals

The emissions assignment step multiplies household expenditure predictions (or observed expenditures) by their emission intensities to calculate household emissions. It then uses predicted time-use to divide those emissions among household members. The required weighted mapping is `input_output_analysis/mapping_exp_timeuse_weighted.parquet`; it is prepared by `src/input_output_analysis/calc__mapping_exp_timeuse_weighted.R` from an expenditure-to-time-use mapping workbook. The Python step writes household and individual results as Parquet batches, with run metadata and a completion marker.

### 7. Analyse

We analyse the population-level data. In our case, we analyse demographic patterns in individual carbon emissions.

*This code is still under development* 


## Contact

This is a project by the [ODISSEI Social Data Science team](https://odissei-soda.nl/). Do you have any questions or suggestions? Please contact [Maike Weiper](https://github.com/MWeiper).

<img src="https://odissei-soda.nl/images/logos/soda_logo.svg" alt="SoDa logo" width="250px"/> 
