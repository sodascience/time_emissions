from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import Model
    
import polars as pl
import numpy as np
from dataclasses import dataclass
from pathlib import Path
import os
import json
import joblib

import optuna
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import make_scorer, mean_squared_error, mean_absolute_error, median_absolute_error, root_mean_squared_log_error

from . import helpers
from .helpers import Named, _label, log, _out, make_stamp, sample_info, log_run
from .unit import Unit
from .dataset import Dataset
from .variable import Variable
from .feature import Feature



@dataclass(eq = False)
class Survey(Named):
    """A survey: the output table it is linked to, its year, its predictors."""

    # fields
    dataset: Dataset                        # the survey file, declared in datasets.py
    ref_year: int                           # the year the survey was fielded
    unit: Unit                              # the output table it is linked to
    date: Variable                          # first day of a survey period
    duration: int                           # length of the survey period in days

    target_pattern: str                     # regex of the target columns: ^...$
    predictors: tuple[Feature, ...]         # features

    baseline: Model                         # the model to compare against
    model: Model                            # main model to predict outcomes

    evaluate_by: tuple[Feature, ...]        # features to evaluate by

    target_dtype: pl.DataType = pl.Float64  # the targets' type after reading
    weight: Variable | None = None          # survey weight
    sample_filter: pl.Expr | None = None    # who the survey represents

    test_share: float = 0.15                # share of respondents in test set
    seed: int = 42
    n_folds: int = 5                        # folds for cross-validation within the training set
    batches: int = 10

    name: str | None = None                 # used in messages; set from the attribute

    def __repr__(self) -> str:
        return _label(kind = "Survey", name = self.name, ref_year = self.ref_year, unit = self.unit,
                      predictors = [f.name for f in self.predictors])
    
    @property
    def n_batches(self) -> int:
        return 1 if helpers.SAMPLE is not None else self.batches
    
    
    # --- paths ---
    def get_folder(self) -> Path:
        """get main folder"""
        return _out() / "surveys" / self.name
    
    def get_responses_path(self) -> Path:
        return self.get_folder() / "responses" / "responses_at_unit.parquet"
    
    def get_predictors_folder(self, year: int | None = None, survey_sample: Survey | None = None) -> Path:
        year = year if year else survey_sample.ref_year

        # make stamp
        folders = [f.get_folder(year = year) for f in self.predictors]       # how the features are operationalized
        stamp = make_stamp(*folders, self.sample_filter, self.n_batches)

        predicted_for = survey_sample.name if survey_sample else "population"
        return self.get_folder() / "predictors" / f"{predicted_for}_{year}_{stamp}"
    
    def get_model_folder(self, model: Model) -> Path:
        """Get the path of the trained models"""
        return _out() / "models" / self.name / model.name
    
    def prediction_inputs(self, model_path, year = None, survey_sample = None):
        predictors_folder = self.get_predictors_folder(year = year, survey_sample = survey_sample)
        return [model_path.read_bytes(), predictors_folder.name]
    
    def get_prediction_folder(self, model: Model, year: int | None = None, survey_sample: Survey | None = None) -> Path:
        """Get the path of the predictions for the training data, test data, or data of a year"""
        model_trained = self.get_model_folder(model = model) / "pipeline.joblib"
        if not model_trained.exists():
            raise FileNotFoundError(f"{self.name}: {model.name} is not trained yet ({model_trained})")

        year = year if year else survey_sample.ref_year
        
        # make stamp
        stamp = make_stamp(*self.prediction_inputs(model_trained, year, survey_sample))

        predicted_for = survey_sample.name if survey_sample else "population"
        return self.get_folder() / "predictions" / model.name / f"{predicted_for}_{year}_{stamp}"
    
    def get_target_columns(self) -> list[str]:
        """The names in the responses that match 'target_pattern'"""
        return self.read_responses().select(pl.col(self.target_pattern)).collect_schema().names()
    
    def get_predictor_columns(self) -> dict[str, pl.DataType]: 
        """Get predictor names and dtypes"""
        names = [f.name for f in self.predictors]
        return dict(self.read_predictors(survey_sample = self).select(names).collect_schema())

    

    # --- responses ---
    def compute_responses(self) -> pl.DataFrame:
        """Preprocess all responses of the survey and turn into the survey's unit"""
        from config.mappings import Mappings
        from config.units import PERSON, HH_SPELL

        first = pl.date(year = self.ref_year, month = 1, day = 1)
        last = pl.date(year = self.ref_year, month = 12, day = 31)
        half = pl.duration(days = (self.duration - 1) // 2)         # a tie goes to the first month
        weight = [self.weight.name] if self.weight is not None else []

        # 1. read the responses, with two dates, both kept within ref_year
        targets = pl.col(self.target_pattern)
        responses = (self.dataset.read(columns = [self.date.name, *weight], year = self.ref_year,
                                       pattern = self.target_pattern)
                                 .with_columns(targets.cast(self.target_dtype),
                                               start = pl.col(self.date.name).clip(first, last),
                                               mid = (pl.col(self.date.name) + half).clip(first, last))
                                 .collect())

        negative = responses.select(pl.sum_horizontal(targets < 0)).to_series().sum()
        if negative:
            log.info(f"{self.name}: {negative} negative target values (but kept in the data)")
            frequent = (responses.select(targets)
                        .unpivot(variable_name = "target")
                        .filter(pl.col("value") < 0)
                        .group_by("target")
                        .agg(n = pl.len(), median = pl.col("value").median())
                        .filter(pl.col("n") > 0.001 * len(responses))           # more than 0.1% of the target's values are negative
                        .sort("n", descending = True))
            for t in frequent.iter_rows(named = True):
                log.info(f"{self.name}:   {t['target']}: {t['n']} negative, median {t['median']:.2f}")
        
        # 2. read and find the household: the spell that holds the start date
        spell_months = Mappings.HOUSEHOLD_PERSON.read(year = self.ref_year)
        on_start = pl.col("start").is_between(pl.col("clip_start"), pl.col("clip_end"))
        household = (responses.lazy().join(other = spell_months, on = PERSON.cols)
                     .filter(on_start)
                     .sort("clip_start")
                     .unique(subset = PERSON.cols, keep = "last")
                     .select(*PERSON.cols, *HH_SPELL.cols))
        
        # 3. get the month of the start spell: the mid of the month if covered, and else the start month
        in_mid_month = pl.col("clip_start").dt.truncate("1mo") == pl.col("mid").dt.truncate("1mo")
        had_mid = in_mid_month.any().over(PERSON.cols)
        is_test = pl.int_range(pl.len()).shuffle(seed = self.seed) < self.test_share * pl.len()
        table = (responses.lazy().join(other = household, on = PERSON.cols)                         # join respondents with their households
                 .with_columns(month = pl.col("mid").dt.month())                                    # add the month of the mid date
                 .join(other = spell_months, on = [*PERSON.cols, *HH_SPELL.cols])                   # join 
                 .filter(in_mid_month | (on_start & ~had_mid))
                 .select(*self.unit.cols, *weight, pl.col(self.target_pattern))
                 .sort(self.unit.cols)
                 .with_columns(split = pl.when(is_test).then(pl.lit("test"))
                               .otherwise(pl.lit("train")))
                 .collect())
        
        # 4. checks
        dropped = len(responses) - len(table)
        if dropped:
            log.info(f"{self.name}: {dropped} of {len(responses)} responses have no household spell-month.")
        assert not table.select(self.unit.cols).is_duplicated().any(), \
            f"{self.name}: two responses in one {self.unit!r} row"
        return table
           

    def write_responses(self, table: pl.LazyFrame) -> None:
        """Save the responses at the survey unit."""
        path = self.get_responses_path()
        path.parent.mkdir(parents = True, exist_ok = True)
        table.write_parquet(path)


    def read_responses(self) -> pl.LazyFrame:
        """Open the saved responses: keys, targets, weight and split."""
        return pl.scan_parquet(source = self.get_responses_path())
    

    # --- predictors ---
    def read_population(self, year: int) -> pl.LazyFrame:
        """Read every row of the survey's output table in 'year' and filter for the keys to predict for."""
        from config.mappings import Mappings
        return Mappings.HOUSEHOLD_PERSON.read(year = year).select(self.unit.cols).unique()
    

    def compute_predictors(self, year: int | None = None, survey_sample: Survey | None = None, batch: int = 0) -> pl.LazyFrame:
        """Read one batch of the wide table: the population's keys, every predictor joined from its freature file, then filtered by sample_filter."""
        from config.units import HH_SPELL
        from config.mappings import Mappings

        if survey_sample:
            assert (year is None) or year == survey_sample.ref_year, f"{self.name}: Cannot write predictors for the {survey_sample.name} sample in {year}"
        else:
            assert year, f"{self.name}: pass a year or a survey_sample"
        year = year or survey_sample.ref_year

        if survey_sample is None:
            in_batch = pl.struct(HH_SPELL.cols).hash() % self.n_batches == batch
            keys = self.read_population(year = year).filter(in_batch)
            keep = lambda lf: lf.filter(in_batch)
            
        else:
            mapping = Mappings.HOUSEHOLD_PERSON.read(year = year)
            keys = (survey_sample.read_responses()
                    .select(survey_sample.unit.cols)
                    .join(mapping, on = survey_sample.unit.cols, how = "inner")
                    .select(self.unit.cols)
                    .unique())
            households = keys.select(HH_SPELL.cols).unique()
            keep = lambda lf: lf.join(other = households, on = HH_SPELL.cols, how = "semi")

        for f in self.predictors:
            keys = keys.join(other = keep(f.read(year = year)), on = f.unit.cols, how = "left")

        return keys if self.sample_filter is None else keys.filter(self.sample_filter)
    
    
    def write_predictors(self, year: int | None = None, survey_sample: Survey | None = None) -> None:
        """Compute and save the predictors of one year (batch by batch). A done file marks a finished year."""
        if survey_sample:
            assert (year is None) or year == survey_sample.ref_year, f"{self.name}: Cannot write predictors for the {survey_sample.name} sample in {year}"
        else:
            assert year, f"{self.name}: pass a year or a survey_sample"
        year = year or survey_sample.ref_year
        
        predicted_for = survey_sample.name if survey_sample else "population"
        
        folder = self.get_predictors_folder(year = year, survey_sample = survey_sample)
        if (folder / "done").exists():
            log.info(f"{self.name}: predictors of {predicted_for} in {year} are already written")
            return
        
        folder.mkdir(parents = True, exist_ok = True)
        n = 1 if survey_sample is not None else self.n_batches

        for b in range(n):
            path = folder / f"batch_{b:02d}.parquet"
            if path.exists():
                continue        # written in an earlier run

            log.info(f"{self.name}: writing predictors of {predicted_for} in {year} - batch {b+1:02d} of {n}")
            self.compute_predictors(year = year, survey_sample = survey_sample, batch = b).sink_parquet(path.with_suffix(".tmp"))
            os.replace(path.with_suffix(".tmp"), path)

        (folder / "done").touch()
        log.info(f"{self.name}: predictors of {predicted_for} in {year} written")


    def read_predictors(self, year: int | None = None, survey_sample: Survey | None = None, batch: int | None = None) -> pl.LazyFrame:
        """Read the predictor table of rows ("respondents" or a year), all batches or one: Keys and predictors only."""
        name = "*.parquet" if batch is None else f"batch_{batch:02d}.parquet"
        return pl.scan_parquet(source = self.get_predictors_folder(year = year, survey_sample = survey_sample) / name)
    
    
    def read_xy(self, split: str) -> tuple[pl.DataFrame, pl.DataFrame]:
        """Read the responses of 'train' or 'test', joined with the ref_year predictors, 
        then split by columns into X (keys & predictors) and Y (targets).
        X and Y come from one table, so their rows match. Respondents outside 
        sample_filter drop out at the join; their number is reported."""
        assert split in ("train", "test"), f"{self.name}: split is 'train' or 'test', not {split!r}"

        responses = self.read_responses().filter(pl.col("split") == split)
        predictors = self.read_predictors(survey_sample = self)
        table = (responses.join(other = predictors, on = self.unit.cols)
                          .sort(self.unit.cols)
                          .collect(engine = "streaming"))
        
        dropped = responses.select(pl.len()).collect().item() - len(table)
        if dropped: 
            log.info(f"{self.name}: {dropped} {split} responses fall outside sample_filter")
        
        targets = self.get_target_columns()
        weight = [self.weight.name] if self.weight is not None else []
        return table.drop(*targets, *weight, "split"), table.select(targets)
    

    # --- models ---
    def tune(self, model: Model, n_trials: int = 100, visualize: bool = False) -> dict:
        """An optuna study, seeded, on read_xy("train") with 
        KFold(n_folds, shuffle = True, random_state = seed). One set of settings 
        for all targets, scored by get_pred_quality made scale_free per target, so every
        target counts equally. Returns the best settings; fits nothing for keeps. 
        Plots go to get_model_folder(model)."""
        X, Y = self.read_xy(split = "train")
        features = self.get_predictor_columns()
        folds = KFold(n_splits = self.n_folds, shuffle = True, random_state = self.seed)
        scorer = make_scorer(get_pred_quality, greater_is_better = False)

        def objective(trial:optuna.Trial) -> float:
            pipe = model.get_pipeline(features = features, params = model.get_params(trial = trial))
            return cross_val_score(pipe, X, Y, cv = folds, scoring = scorer).mean()
        
        study = optuna.create_study(direction = "maximize",
                                    sampler = optuna.samplers.TPESampler(seed = self.seed))
        study.optimize(objective, n_trials = n_trials, show_progress_bar = True)

        if visualize:
            from optuna.visualization import (plot_optimization_history, plot_parallel_coordinate,
                                              plot_contour, plot_param_importances, plot_slice, plot_edf)
            folder = self.get_model_folder(model = model) / "tuning"
            folder.mkdir(parents = True, exist_ok = True)
            for plot in (plot_optimization_history, plot_parallel_coordinate, plot_contour,
                         plot_param_importances, plot_slice, plot_edf):
                plot(study).write_image(folder / f"{plot.__name__}.png", scale = 3)
        log.info(f"{self.name}: best settings for {model.name}: {study.best_params}")
        return model.get_params(trial = optuna.trial.FixedTrial(study.best_params))
            

    def write_params(self, model: Model, params: dict) -> None:
        """Save tuned settings."""
        folder = self.get_model_folder(model = model)
        folder.mkdir(parents = True, exist_ok = True)
        (folder / "params.json").write_text(json.dumps(params, indent = 2))


    def read_params(self, model: Model) -> dict:
        """Read the tuned settings, or the model's defaults if it was not tuned."""
        if not model.is_tunable:
            return model.get_params()
        return json.loads((self.get_model_folder(model = model) / "params.json").read_text())
    

    def train(self, model: Model) -> Pipeline:
        """model.get_pipeline with read_params fitted on read_xy("train"), unweighted"""
        X, Y = self.read_xy(split = "train")
        pipe = model.get_pipeline(features = self.get_predictor_columns(),
                                  params = self.read_params(model = model))
        return pipe.fit(X, Y)
    

    def write_model(self, pipeline: Pipeline, model: Model) -> None:
        """Save a fitted pipeline."""
        path = self.get_model_folder(model = model) / "pipeline.joblib"
        path.parent.mkdir(parents = True, exist_ok = True)
        joblib.dump(pipeline, path)


    def read_model(self, model: Model) -> Pipeline:
        """Open a fitted pipeline."""
        return joblib.load(self.get_model_folder(model = model) / "pipeline.joblib")

    
    # --- predictions ---
    def compute_predictions(self, model: Model, pipeline: Pipeline | None = None,
                            year: int | None = None, survey_sample: Survey | None = None,
                            batch: int | None = None) -> pl.DataFrame:
        X = self.read_predictors(year = year, survey_sample = survey_sample, batch = batch).collect(engine = "streaming")
        log.info(f"{self.name}: {len(X):,} rows read; predicting {len(self.get_target_columns())} targets")

        targets = self.get_target_columns()
        pred = (pipeline or self.read_model(model = model)).predict(X)
        log.info(f"{self.name}: predicted")

        return X.select(self.unit.cols).hstack(
            pl.DataFrame(pred, schema = targets, orient = "row"))
    
    
    def write_predictions(self, model: Model, 
                          year: int | None = None, survey_sample: Survey | None = None) -> None:
        """Compute and save the predictions of rows; a year batch by batch."""
        predicted_for, year = sample_info(year, survey_sample)
        folder = self.get_prediction_folder(model = model, year = year, survey_sample = survey_sample)

        if (folder / "done").exists():
            log.info(f"{self.name}: {model.name} predictions of {predicted_for} for {year} are already written")
            return
        
        folder.mkdir(parents = True, exist_ok = True)
        n = 1 if survey_sample else self.n_batches

        pipeline = self.read_model(model = model)

        for b in range(n):
            path = folder / f"batch_{b:02d}.parquet"
            if path.exists():
                continue
            log.info(f"{self.name}: predicting {predicted_for} for {year} with {model.name} - batch {b:02d} of {n}")
            self.compute_predictions(model = model, year = year, survey_sample = survey_sample, batch = b, pipeline = pipeline).write_parquet(path.with_suffix(".tmp"))
            os.replace(path.with_suffix(".tmp"), path)

        if self.name == "EXPENDITURES":
            model_col = "exp_model"
        else:
            model_col = "time_model"
        log_run(folder, inputs = self.prediction_inputs(model_path = self.get_model_folder(model = model) / "pipeline.joblib", year = year, survey_sample = survey_sample),
                output_type = f"predictions_{self.name}", sample = predicted_for,
                year = year, **{model_col: model.name})
        (folder / "done").touch()
        log.info(f"{self.name}: {model.name} predictions of {predicted_for} for {year} written")


    def read_predictions(self, model: Model, year: int | None = None, survey_sample: Survey | None = None) -> pl.LazyFrame:
        """Open saved predictions: all batches as one table."""
        return pl.scan_parquet(source = self.get_prediction_folder(model = model, year = year, survey_sample = survey_sample) / "batch_*.parquet")

    
    # --- evaluation ---
    def compute_evaluation(self) -> pl.DataFrame:
        """How good the predicitons are per target, for baseline and model, weighted by 'weight' if set."""
        targets = self.get_target_columns()
        w = pl.col(self.weight.name) if self.weight is not None else pl.lit(1.0)

        def wmean(e: pl.Expr) -> pl.Expr:
            return (e*pl.col("w")).sum() / pl.col("w").sum()
        
        scores = [pl.len().alias("n"),
                  wmean((pl.col("predicted").arcsinh() - pl.col("observed").arcsinh()) ** 2).sqrt().alias("rmsae"),
                  wmean((pl.col("predicted") - pl.col("observed")).abs()).alias("mae"),
                  wmean(pl.col("observed")).alias("mean_observed"),
                  wmean(pl.col("predicted")).alias("mean_predicted"),
                  wmean((pl.col("observed") == 0).cast(pl.Float64)).alias("share_zero"),
                  wmean((pl.col("observed") < 0).cast(pl.Float64)).alias("share_negative")]
        
        # 1. the test set
        responses = self.read_responses().with_columns(w = w)
        observed = (responses.filter(pl.col("split") == "test")
                    .unpivot(on = targets, index = [*self.unit.cols, "w"],
                             variable_name = "target", value_name = "observed"))
        predicted = pl.concat([self.read_predictions(model = m, survey_sample = self)
                               .unpivot(on = targets, index = self.unit.cols,
                                        variable_name = "target", value_name = "predicted")
                               .with_columns(model = pl.lit(m.name))
                               for m in (self.baseline, self.model)])
        test = observed.join(other = predicted, on = [*self.unit.cols, "target"])       # inner join so that only the test set is kept (as observed is already filtered)
        for f in self.evaluate_by:
            test = test.join(other = f.read(year = self.ref_year), on = f.unit.cols, how = "left")

        # 2. scores
        tables = [test.group_by("model", "target").agg(scores)
                      .with_columns(grouping = pl.lit("all"), group = pl.lit("all"))]
        tables += [test.group_by("model", "target", f.name).agg(scores)
                       .with_columns(grouping = pl.lit(f.name), group = pl.col(f.name).cast(pl.String))
                       .drop(f.name)
                       for f in self.evaluate_by]
        
        # 3. population check
        survey = (responses.select(wmean(pl.col(t)).alias(t) for t in targets)
                  .unpivot(on = targets, variable_name = "target", value_name = "mean_observed"))
        for m in (self.baseline, self.model):
            if not (self.get_prediction_folder(model = m, year = self.ref_year) / "done").exists():
                log.info(f"{self.name}: population of {self.ref_year} not predicted with {m.name} yet; evaluation without the population check")
                continue
            population = (self.read_predictions(model = m, year = self.ref_year)
                          .select(pl.col(targets).mean())
                          .unpivot(on = targets, variable_name = "target", value_name = "mean_predicted"))
            tables.append(
                survey.join(other = population, on = "target")
                    .with_columns(model = pl.lit(m.name), grouping = pl.lit("population"),
                                    group = pl.lit("all")))            
            
        return (pl.concat(tables, how = "diagonal")
                .select("model", "grouping", "group","target", "n", "rmsae",
                        "mean_observed", "mean_predicted", "share_zero", "share_negative")
                .sort("grouping", "group", "target", "model")
                .collect(engine = "streaming"))
        

    def write_evaluation(self, table: pl.DataFrame) -> None:
        """Save the evaluation"""
        path = self.get_folder() / "evaluation.parquet"
        path.parent.mkdir(parents = True, exist_ok = True)
        table.write_parquet(path)

    
    def read_evaluation(self) -> pl.DataFrame:
        """Open the saved evaluation."""
        return pl.read_parquet(self.get_folder() / "evaluation.parquet")

    





def rmsae(y_true, y_pred, multioutput = "raw_values") -> np.ndarray:
    """Root mean squared asinh error per target: same idea as RMSLE, but on a scale that takes negatives as well"""
    diff = np.arcsinh(np.asarray(y_pred, dtype = float)) - np.arcsinh(np.asarray(y_true, dtype = float))
    return np.sqrt(np.mean(diff ** 2, axis = 0))

METRICS = {"rmsae": rmsae, "rmsle": root_mean_squared_log_error, "mse": mean_squared_error,
           "mdae": median_absolute_error, "mae": mean_absolute_error}


def get_pred_quality(y_true, y_pred, metric: str = "rmsae") -> float:
    """Get a metric per target, and sum them over targets: lower is better.
    RMSAE compares asinh(y), so each target counts by its relative error, and negative values are preserved"""
    if metric not in METRICS:
        raise ValueError(f"unknown metric {metric!r}; choose from {list(METRICS)}")
    return float(np.sum(METRICS[metric](y_true, y_pred, multioutput = "raw_values")))
