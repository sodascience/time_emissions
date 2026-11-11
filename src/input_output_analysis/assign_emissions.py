import os
import polars as pl

from config.surveys import *
from src.utils.core.helpers import make_stamp, sample_info, log_run


# --- settings ---
EMISSIONS_FOLDER    = OUT / "emissions"
MAPPING_PATH        = OUT / "input_output_analysis" / "mapping_exp_timeuse_weighted.parquet"
INTENSITY_PATH      = OUT / "input_output_analysis" / "emission_intensity_per_expenditure.csv"
N_BATCHES = 50

HOUSEHOLD_KEYS = (HH_SPELL | MONTH).cols
PERSON_KEYS = (PERSON | HH_SPELL | MONTH).cols



# helpers
def individual_inputs(household_path, time_model, year = None, survey_sample = None):
    time_prediction_folder = Surveys.TIMEUSE.get_prediction_folder(model = time_model, year = year, survey_sample = survey_sample)
    return [household_path.name, time_prediction_folder.name, MAPPING_PATH.read_bytes()]



# --- paths ---
def get_household_path(exp_model: Model | None = None, year: int | None = None, survey_sample: Survey | None = None) -> Path:
    if exp_model is None:
        stamp = make_stamp(Surveys.EXPENDITURES.get_responses_path().read_bytes())        
        return EMISSIONS_FOLDER / "OBSERVED" / f"emissions_households_EXPENDITURES_{Surveys.EXPENDITURES.ref_year}_{stamp}"
    predictions = Surveys.EXPENDITURES.get_prediction_folder(model = exp_model, year = year, survey_sample = survey_sample)
    return EMISSIONS_FOLDER / exp_model.name / f"emissions_households_{predictions.name}"

def get_individual_folder(household_path, time_model: Model, year: int | None = None, survey_sample: Survey | None = None) -> Path:
    stamp = make_stamp(*individual_inputs(household_path, time_model, year, survey_sample))
    predicted_for, year = sample_info(year, survey_sample)
    return household_path.parent / time_model.name / f"emissions_individuals_{predicted_for}_{year}_{stamp}"

def to_activity(activity: str) -> pl.Expr:
    terms = [pl.col(row["category"]) * row[activity]
             for row in mapping.iter_rows(named = True) if row[activity] != 0]
    return pl.sum_horizontal(terms or [pl.lit(0.0)]).alias(activity)






# --- read data ---
mapping = pl.read_parquet(MAPPING_PATH)

ACTIVITIES = [c for c in mapping.columns if c != "category"]
FALLBACK_ACTIVITY   = "activity_home"
OTHER_ACTIVITIES = [a for a in ACTIVITIES if a != FALLBACK_ACTIVITY]

intensities = pl.read_csv(INTENSITY_PATH)
EMISSIONS_PER_EURO = dict(zip(intensities["Variable"], intensities[intensities.columns[1]]))

def to_emissions(expenditures: pl.LazyFrame) -> pl.LazyFrame:
    categories = [c for c in expenditures.collect_schema().names() if c in EMISSIONS_PER_EURO]
    return (expenditures
            .select(*HOUSEHOLD_KEYS, *[pl.col(c) * EMISSIONS_PER_EURO[c] for c in categories])
            .with_columns(total = pl.sum_horizontal(categories)))


def write_household_emissions(household_path, exp_model = None, year = None, survey_sample = None) -> None:
    if exp_model is None:                               # no prediction model -> use observed data
        batches = {"batch_00.parquet": Surveys.EXPENDITURES.read_responses()}
        inputs = Surveys.EXPENDITURES.get_responses_path().read_bytes()
        sample, year = sample_info(survey_sample = Surveys.EXPENDITURES)
    else:                                               # use predicted data
        predictions_path = Surveys.EXPENDITURES.get_prediction_folder(model = exp_model, year = year, survey_sample = survey_sample)
        if not (predictions_path / "done").exists():             # check if expenditure predictions exist
            raise FileNotFoundError(f"No expenditure predictions yet: {predictions_path}")
        batches = {b.name: pl.scan_parquet(b) for b in sorted(predictions_path.glob("batch_*.parquet"))}
        inputs = [predictions_path.name]
        sample, year = sample_info(year, survey_sample)
    
    log.info(f"Writing household emissions for {sample} in {year}...")
    temporary = household_path.with_name(household_path.name + "_tmp")
    temporary.mkdir(parents = True, exist_ok = True)
    for name, exp_lf in batches.items():
        log.info(f"Writing household emissions for {sample} in {year} - {name}")
        emissions_df = to_emissions(exp_lf).collect()
        emissions_df.write_parquet(temporary / name)

    log_run(household_path, inputs = inputs, write_in = temporary,
            output_type = "emissions_households", exp_model = exp_model.name if exp_model else "OBSERVED",
            sample = sample, year = year)
    os.replace(temporary, household_path)


def read_household_emissions(household_path, in_batch) -> pl.DataFrame:
    source = household_path if household_path.is_file() else household_path / "batch_*.parquet"
    return (pl.scan_parquet(source)
                           .filter(in_batch)
                           .select(*HOUSEHOLD_KEYS, *[to_activity(a) for a in ACTIVITIES])
                           .collect())


def read_timeuse_predictions(time_model, in_batch, year = None, survey_sample = None) -> pl.DataFrame:
    members = (Mappings.HOUSEHOLD_PERSON.read(year = year or survey_sample.ref_year)
               .filter(in_batch)
               .select(PERSON_KEYS))
    if survey_sample is not None:
        sample_households = survey_sample.read_responses().select(HOUSEHOLD_KEYS)
        members = members.join(sample_households, on = HOUSEHOLD_KEYS, how = "semi")
    
    predictions = (Surveys.TIMEUSE.read_predictions(model = time_model, year = year, survey_sample = survey_sample)
                   .filter(in_batch)
                   .select(*PERSON_KEYS, *ACTIVITIES)
                   .with_columns(has_prediction = pl.lit(True)))
    
    return (members
            .join(predictions, on = PERSON_KEYS, how = "left")
            .with_columns(pl.col(ACTIVITIES).fill_null(0.0),
                          pl.col("has_prediction").fill_null(False))
                          .collect(engine = "streaming"))


# --- divide emissions among members ---
def move_unused_emissions(household_emissions, timeuse) -> pl.DataFrame:
    household_time = timeuse.group_by(HOUSEHOLD_KEYS).agg(pl.col(ACTIVITIES).sum())
    nobody_does = {a: pl.col(f"{a}_time") == 0 for a in OTHER_ACTIVITIES}
    unused = pl.sum_horizontal(pl.when(nobody_does[a]).then(pl.col(a)).otherwise(0.0)
                               for a in OTHER_ACTIVITIES)
    return (household_emissions
            .join(household_time, on = HOUSEHOLD_KEYS, suffix = "_time")
            .with_columns((pl.col(FALLBACK_ACTIVITY) + unused).alias(FALLBACK_ACTIVITY),
                          *[pl.when(nobody_does[a]).then(0.0).otherwise(pl.col(a)).alias(a)
                            for a in OTHER_ACTIVITIES])
                            .select(*HOUSEHOLD_KEYS, *ACTIVITIES))


def compute_timeuse_shares(timeuse) -> pl.DataFrame:
    def share(activity:str) -> pl.Expr:
        household_time = pl.col(activity).sum().over(HOUSEHOLD_KEYS)
        return (pl.col(activity) / household_time).fill_nan(0.0).alias(activity)
    return timeuse.with_columns(share(a) for a in ACTIVITIES)


def compute_individual_emissions(timeuse_shares, household_emissions) -> pl.DataFrame:
    return (timeuse_shares
            .join(household_emissions, on = HOUSEHOLD_KEYS, suffix = "_household")
            .select(*PERSON_KEYS, "has_prediction",
                    *[(pl.col(a) * pl.col(f"{a}_household")).alias(a) for a in ACTIVITIES]))







# --- main ---

def assign_emissions(household_path, time_model, in_batch, year = None, survey_sample = None) -> pl.DataFrame:
    household_emissions = read_household_emissions(household_path, in_batch)
    timeuse = read_timeuse_predictions(time_model, in_batch, year = year, survey_sample = survey_sample)

    household_emissions = move_unused_emissions(household_emissions, timeuse)
    timeuse_shares = compute_timeuse_shares(timeuse)

    return compute_individual_emissions(timeuse_shares, household_emissions)


    
def write_individual_emissions(household_path, time_model, output_folder, year = None, survey_sample = None) -> None:
    if not household_path.exists():
        log.info(f"No household emissions yet: {household_path}")
        return
    if (output_folder / "done").exists():
        log.info(f"Already written: {output_folder}")
        return
    output_folder.mkdir(parents = True, exist_ok = True)

    sample, year = sample_info(year, survey_sample)
    log.info(f"Writing individual emissions for {sample} in {year}...")

    n_batches = 1 if survey_sample is not None else N_BATCHES
    for b in range(n_batches):
        path = output_folder / f"batch_{b:02d}.parquet"
        if path.exists():
            continue

        log.info(f"Writing individual emissions for {sample} in {year} - batch {b}")
        
        in_batch = pl.struct(HH_SPELL.cols).hash() % n_batches == b
        
        individual_emissions = assign_emissions(household_path, time_model, in_batch, year, survey_sample)

        temporary = path.with_suffix(".tmp")
        individual_emissions.write_parquet(temporary)
        os.replace(temporary, path)
        log.info(f"Written: {path}")

    sample, sample_year = sample_info(year, survey_sample)
    log_run(output_folder, inputs = individual_inputs(household_path, time_model, year, survey_sample),
            output_type = "emissions_individuals", exp_model = household_path.parent.name,
            time_model = time_model.name, sample = sample, year = sample_year)

    (output_folder / "done").touch()