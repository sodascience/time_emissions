# Processed data

The project stores its generated data and intermediate files in this folder. The paths in `config/datasets.py` point to this directory and its `cache/` subfolder. If you run the pipeline on a sample, outputs that use the shared `_out()` helper go into `sample/` instead.

Most folders are empty until you run the step that creates their contents. Git ignores generated data files, so they will not be included in commits. Please do not commit restricted or personally identifiable data.

## Folder structure

```text
data/processed_data/
├── cache/
│   ├── datasets/{dataset}/{year}_{source}_{stamp}.parquet
│   ├── mappings/{dataset}/{year}_{source}/{month}.parquet
│   └── divided/{year}_{stamp}.parquet
├── demographics/
│   ├── household_month/{feature}_{stamp}/{year}/
│   │   ├── batch_{number}.parquet
│   │   └── done
│   └── person_household_month/{feature}_{stamp}/{year}/
│       ├── batch_{number}.parquet
│       └── done
├── emissions/
│   ├── OBSERVED/
│   │   ├── emissions_households_{survey}_{year}_{stamp}/
│   │   └── {time_model}/emissions_individuals_{sample}_{year}_{stamp}/
│   └── {expenditure_model}/
│       ├── emissions_households_{predictions}/
│       └── {time_model}/emissions_individuals_{sample}_{year}_{stamp}/
├── input_output_analysis/
│   ├── emission_intensity_per_expenditure.csv
│   └── mapping_exp_timeuse_weighted.parquet
├── models/
│   └── {survey}/{model}/
│       ├── pipeline.joblib
│       ├── params.json
│       └── tuning/*.png
├── sample/
└── surveys/
    └── {survey}/
        ├── responses/responses_at_unit.parquet
        ├── predictors/{sample}_{year}_{stamp}/
        │   ├── batch_{number}.parquet
        │   └── done
        ├── predictions/{model}/{sample}_{year}_{stamp}/
        │   ├── batch_{number}.parquet
        │   └── done
        └── evaluation.parquet
```

## What each folder contains

- **`surveys/`** keeps the data for each survey together. `responses/` contains the prepared survey responses, `predictors/` contains the features used by the models, and `predictions/` contains model results. The evaluation results are saved alongside these folders. The active surveys are `TIMEUSE` and `EXPENDITURES`.
- **`models/`** contains the fitted pipeline and any tuned settings for each survey and model. It can also contain plots from model tuning.
- **`demographics/`** contains the population features used to make predictions. Features are grouped by output table: `household_month` or `person_household_month`.
- **`input_output_analysis/`** holds the emission-intensity CSV and the expenditure-to-time-use mapping used to calculate emissions. Both files need to be present before running the emissions step.
- **`emissions/`** contains household emissions and the individual emissions assigned using predicted time-use. Household results are grouped by whether they use observed expenditures or a model's predictions. Individual results are nested under the time-use model used.
- **`cache/`** stores intermediate Parquet tables so the project can reuse processed datasets, mappings, and divided variables.
- **`sample/`** keeps sample-mode outputs separate from full outputs when they use the shared `_out()` helper.

## Files and naming

Most tables are saved as Parquet files. Model pipelines use `.joblib`, tuned settings use `.json`, emission intensities use `.csv`, and optional tuning plots use `.png`.

Large tables may be split into numbered `batch_{number}.parquet` files. A `done` marker shows that a feature, predictor, or prediction folder has finished processing. Emissions outputs also include `run_info.parquet`, which records details such as the output type, model, sample, year, and input stamp.

Some folder names include a short `{stamp}` based on the inputs and settings used to create the data. This lets the project keep different versions separate. `{sample}` is either `population` or the name of the survey sample being processed.


## Where paths are set

`OUT` in `config/datasets.py` points to this folder, based on the repository location. `CACHE` points to `cache/` here. The raw input data location is configured separately and is not changed by this folder layout.
