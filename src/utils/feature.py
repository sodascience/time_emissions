import polars as pl
from dataclasses import dataclass
from pathlib import Path
import os

from . import helpers
from .helpers import Named, _label, VALUE, log, _out, make_stamp
from .unit import Unit
from .variable import Variable
from .mapping import Mapping


@dataclass(eq = False)
class Feature(Named):
    """A variable that gets written to an output table"""

    # fields
    variable: Variable                      # the chain result it writes
    description: str = ""                   # what the column means
    condition: pl.Expr | Variable | None = None     # passed on to move: which rows count
    weight: pl.Expr | None = None           # how an amount is divided
    agg_method: pl.Expr | None = None              # how rows are combined
    via: Mapping | None = None              # which mapping, if the rule should not choose
    fill: object = None                     # the value of a row where value is missing
    name: str | None = None                 # the column name; from the attrbute
    unit: Unit | None = None                # the table's unit; from the namespace class
    batches: int = 1                        # >1 indicates that this feature is written in batches of persons (or of households)

    def __post_init__(self) -> None:
        """A feature of another table as input: its variable already at that table's unit."""
        if isinstance(self.variable, Feature):
            self.variable = self.variable.variable

    def __repr__(self) -> str:
        return _label(kind = "Feature", name = self.name, unit = self.unit,
                      description = self.description)

    def __set_name__(self, owner: type, name: str) -> None:
        """Take the name from teh attribute and the unit from the class; then move there."""
        assert hasattr(owner, "unit"), f"{name}: a Feature belongs in a table class with a unit"
        if self.name is None:
            self.name = name
        self.unit = owner.unit              # a theme class inherits it from its table
        needs_move = (self.variable.unit != self.unit
                      or any(a is not None for a in (self.condition, self.weight, self.agg_method)))
        if needs_move:                      # errors from move name the problem, on import
            self.variable = self.variable.move(to = self.unit, condition = self.condition,
                                               weight = self.weight, agg_method = self.agg_method, via = self.via)
        if self.fill is not None:           # every row of the table gets a value
            self.variable = self.variable._fill(self.fill)

        compute = self.variable.recipe

        def new_recipe(year: int) -> pl.LazyFrame:
            if helpers.SAMPLE is None and (self.get_folder(year = year) / "done").exists():
                return self.read(year = year).rename({self.name: "value"})
            return compute(year)
        
        self.variable.recipe = new_recipe

        
    # method
    def compute(self, year: int) -> pl.LazyFrame:
        """Run the variable and name its column."""
        return (self.variable.compute(year = year)
                .select(*self.unit.cols, VALUE.alias(self.name)))
    
    def get_folder(self, year: int) -> Path:
        """This feature's files for one year. The name carries a stamp of how it is built"""
        from config.features import TABLE_NAMES
        stamp = make_stamp(self.variable.describe(), self.fill, self.batches)
        return _out() / "demographics" / TABLE_NAMES[self.unit] / f"{self.name}_{stamp}" / str(year)
    
    def write(self, year: int) -> None:
        """Write one year in batches of persons or households, each for the whole year."""
        from config.datasets import Datasets
        from config.units import PERSON, HH_SPELL
        
        folder = self.get_folder(year = year)
        if (folder / "done").exists():
            return
        folder.mkdir(parents = True, exist_ok = True)

        ids = PERSON.cols if PERSON <= self.unit else HH_SPELL.cols
        members = (Datasets.gbahuishoudenbus.read(columns = [], year = year)
                   .select(*HH_SPELL.cols, *PERSON.cols).unique()
                   .with_columns(batch = pl.struct(ids).hash() % self.batches)
                   .collect())
        
        for b in range(self.batches):
            path = folder / f"batch_{b:02d}.parquet"
            if path.exists():
                continue
            log.info(f"{year}: writing {self.name} - batch {b:02d}")
            in_batch = members.filter(pl.col("batch") == b)
            helpers.BATCH = in_batch.select(PERSON.cols).unique()
            try:
                result = (self.compute(year = year)
                        .join(in_batch.select(ids).unique().lazy(), on = ids, how = "semi")
                        .collect(engine = "streaming"))
            finally:
                helpers.BATCH = None
            result.write_parquet(path.with_suffix(".tmp"))
            os.replace(path.with_suffix(".tmp"), path)
        (folder / "done").touch()


    def read(self, year: int, month: int | None = None) -> pl.LazyFrame:
        """The saved feature: its keys and one column with its name"""
        lf = pl.scan_parquet(source = self.get_folder(year = year) / "*.parquet")
        return lf if month is None else lf.filter(pl.col("month") == month)
    


### helpers.py ###

from __future__ import annotations
from datetime import datetime
import hashlib
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .unit import Unit
    
import polars as pl
pl.enable_string_cache()
from pathlib import Path
import logging

logging.basicConfig(level = logging.WARNING, format = "%(asctime)s %(message)s", datefmt = "%H:%M:%S")
log = logging.getLogger("pipeline")
log.setLevel(logging.INFO)


def make_stamp(*inputs, length = 8) -> str:
    h = hashlib.md5()
    for i in inputs:
        h.update(i if isinstance(i, bytes) else str(i).encode())
        h.update(b"|")
    return h.hexdigest()[:length]


LOG_SCHEMA = {
    "output_type": pl.String, 
    "exp_model": pl.String, 
    "time_model": pl.String,
    "sample": pl.String, 
    "year": pl.Int32,
    "stamp": pl.String,
    "inputs": pl.String,
    "created": pl.Datetime,
    "polars": pl.String
}


def readable(input) -> str:
    return make_stamp(input) if isinstance(input, bytes) else str(input)

def log_run(folder: Path, inputs = (), write_in: Path | None = None, **info) -> None:
    info |= {
        "stamp": folder.name.split("_")[-1],
        "inputs": " | ".join(readable(i) for i in inputs),
        "created": datetime.now(),
        "polars": pl.__version__,
    }
    row = {col: [info.get(col)] for col in LOG_SCHEMA}
    pl.DataFrame(row, schema = LOG_SCHEMA).write_parquet((write_in or folder) / "run_info.parquet")

def read_logbook(root: Path, output_type: str | None = None) -> pl.DataFrame:
    files = sorted(root.rglob("run_info.parquet"))
    if not files:
        return pl.DataFrame(schema = LOG_SCHEMA)
    logbook = pl.concat([pl.read_parquet(f).with_columns(folder = pl.lit(str(f.parent))) for f in files])
    if output_type is not None:
        logbook = logbook.filter(pl.col("output_type") == output_type)
    return logbook



def sample_info(year = None, survey_sample = None):
    if survey_sample is None:
        return "population", year
    return survey_sample.name, year or survey_sample.ref_year




def _label(kind: str, **fields) -> str:
    """How an object prints: like the call that made it.
    Fields that are empty are left out.Pass names, not objects: == on a Variable builds a Variable."""
    shown = [f"{k}={v!r}"for k, v in fields.items() if v is not None and v!= ""]
    return f"{kind}({', '.join(shown)})"



class Named:
    """Mixin: an instance assigned in a class body takes that attribute's name.
    Python calls __set_name__ itself when a namespace class is created."""

    def __set_name__(self, owner: type, name: str) -> None:
        if self.name is None:           # an explicit name wins
            self.name = name



class Namespace:
    """Groups instances under one name (Keys.RINPERSOON, Datasets.INPATAB, ...).
    A subclass sets 'kind'; all() lists its instances in the order written."""

    kind: type = object

    @classmethod
    def all(cls, kind: type | None = None) -> list:
        """Its instances of 'kind'; by default of the namespace's own kind"""
        wanted = kind or cls.kind
        assert wanted is not object, f"{cls.__name__} sets no kind"
        return [v for v in vars(cls).values() if isinstance(v, wanted)]
    


FAR_FUTURE = pl.date(year = 2099, month = 12, day = 31)     # stands in for open spells
VALUE = pl.col("value")                                     # a variable's own value
COVER = pl.col("cover")
SAMPLE: pl.DataFrame | None = None
BATCH: pl.DataFrame | None = None



def _keep_persons(lf: pl.LazyFrame, unit: Unit) -> pl.LazyFrame:
    """Keep only the rows opf the sampled persons and of the current batch, if this unit has persons"""
    for persons in (SAMPLE, BATCH):
        if persons is not None and "RINPERSOON" in unit.cols:
            lf = lf.filter(pl.col("RINPERSOON").is_in(persons.get_column("RINPERSOON").implode()))
    return lf


def _out() -> Path:
    """Where output tables go: OUT, or OUT/sample while testing, so nothing real is overwritten."""
    from config.datasets import OUT

    return OUT / "sample" if SAMPLE is not None else OUT