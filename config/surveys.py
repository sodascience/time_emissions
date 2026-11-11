import polars as pl

from config.models import *

class Surveys(Namespace):
    """Every survey the pipeline serves; Surveys.all() lists them"""
    kind = Survey

    EXPENDITURES = Survey(
        dataset = Datasets.expenditures,
        ref_year = 2015, 
        unit = HH_SPELL | MONTH,
        date = Variables.BOSTARTDATUM,
        duration = 28,

        target_pattern = r"^BOBEST\d+H$",
        n_folds = 5,
        predictors = tuple(features_of(HH_SPELL | MONTH)),

        baseline = Models.HH_TYPE_MEAN,
        model = Models.HIST_GRADIENT,

        evaluate_by = (CompositionHousehold.type_hh,),
        weight = Variables.BOGEWICHT,
        sample_filter = pl.col(CompositionHousehold.type_hh.name).ne_missing("8"),    # remove institutional households

        batches = 16
    )

    TIMEUSE = Survey(
        dataset = Datasets.timeuse,
        ref_year = 2016,
        unit = PERSON | HH_SPELL | MONTH,
        date = Variables.invul_datum,
        duration = 7,

        target_pattern = r"^activity_.*$",
        predictors = (*features_of(PERSON | HH_SPELL | MONTH),
                      *features_of(HH_SPELL | MONTH)),

        baseline = Models.GENDER_MEAN,
        model = Models.HIST_GRADIENT,

        evaluate_by = (DemographyPerson.gender,),
        weight = Variables.tbo_eindgewicht_7dagen,
        sample_filter = pl.col(DemographyPerson.age.name) >= 10,

        batches = 16
    )



# the years and tables the pipeline builds
YEARS           = sorted({s.ref_year for s in Surveys.all()})
OUTPUT_UNITS    = {s.unit for s in Surveys.all()} | {f.unit for s in Surveys.all() for f in s.predictors}




# checks that run on import

for s in Surveys.all():
    names = {f.name for f in s.predictors}
    
    # every predictor and evaluation group is at the survey's unit or a coarser one
    wrong = [f.name for f in (*s.predictors, *s.evaluate_by) if not f.unit <= s.unit]
    assert not wrong, f"{s.name}: {wrong} cannot be joined at {s.unit!r}"

    # the baseline's group and the sampl filter's columns are among the predictors
    group = s.baseline.model_params.get("group_col")
    assert group is None or group in names, f"{s.name}: the baseline's group {group!r} is not a predictor"  
    used = set(s.sample_filter.meta.root_names()) if s.sample_filter is not None else set ()
    assert used <= names, f"{s.name}: sample_filter uses {sorted(used-names)}, which are not predictors"


survey_files = {s.dataset for s in Surveys.all()}
for ds in Datasets.all():
    if isinstance(ds.files, dict) and ds not in survey_files:
        missing = set(YEARS) - ds.files.keys()
        assert not missing, f"{ds.name}: no file given for {sorted(missing)}"
