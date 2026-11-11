from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .variable import Variable

import polars as pl
from dataclasses import dataclass
from pathlib import Path
import os, csv, shutil
import re

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from . import helpers
from .helpers import Named, _label, FAR_FUTURE, log, _keep_persons, make_stamp
from .unit import Unit, Key



@dataclass(eq = False)
class Dataset(Named):
    """A delivered file, per year, and what one of its rows is."""

    # fields
    unit: Unit                      # native unit: the keys of one row
    files: dict[int, str] | str     # year -> file name, or one name for all years
    name: str | None = None         # used in messages; set from the attribute
    description: str = ""
    start: str | None = None        # the column where a spell starts
    end: str | None = None          # the column where a spell ends

    
    def __repr__(self) -> str:
        return _label(kind = "Dataset", name = self.name, unit = self.unit,
                      description = self.description)
    

    @property
    def variables(self) -> list[Variable]:
        from config.variables import Variables
        return [v for v in Variables.all() if v.dataset is self]


    # methods
    def get_raw_path(self, year: int) -> Path:
        """Get the path of the raw file"""
        from config.datasets import RAW            # at call time: datasets.py imports core
        if isinstance(self.files, str):     # one cumulative file
            return RAW / self.files
        assert year in self.files, "f.{self.name}: no file given for {year}"
        return RAW / self.files[year]


    def get_cache_path(self, year: int) -> Path:
        """Get the path of the cached file"""
        from config.datasets import CACHE
        columns = [*sorted(self.unit, key = lambda k: k.name), *self.variables]
        stamp = make_stamp(*[(c.name, str(c.dtype), c.format, sorted(c.codebook.items()))
                             for c in columns])
        return CACHE / "datasets" / self.name / f"{year}_{self.get_raw_path(year).stem}_{stamp}.parquet"
    
    
    def _touches(self, year: int) -> pl.Expr:
        """For a bus: the spell starts before the year is over, and ends (or runs on) after it began"""
        assert self.start in self.unit.cols, f"{self.name}: start column {self.start} is not a key"
        first = pl.date(year = year, month = 1, day = 1)
        last = pl.date(year = year, month = 12, day = 31)
        return (pl.col(self.start) <= last) & (pl.col(self.end).fill_null(value = FAR_FUTURE) >= first)
    

    def write_cache(self, year: int) -> None:
        """Read the variables from the raw file, parse the dtype of all variables and write the new file to cache"""

        assert helpers.SAMPLE is None, "no typed copies while testing on a sample"

        path = self.get_cache_path(year = year)
        path.parent.mkdir(parents = True, exist_ok = True)

        raw, variables = self.get_raw_path(year = year), self.variables
        tmp = path.with_suffix(".tmp")
        names = [*self.unit.cols, *[v.name for v in variables],
                    *([self.end] if self.start else [])]
        tmp, parts = path.with_suffix(".tmp"), path.with_suffix(".parts")
        shutil.rmtree(parts, ignore_errors = True)
        parts.mkdir()

        for i, piece in enumerate(PIECES[raw.suffix](path = raw, columns = list(dict.fromkeys(names)))):
            self._read_raw(year = year, lf = piece.lazy()).collect().write_parquet(parts / f"{i:05d}.parquet")
            log.info(f"{year}: {self.name}: piece {i} written")

        pl.scan_parquet(parts / "*.parquet").sink_parquet(path = tmp)
        shutil.rmtree(parts)
        os.replace(tmp, path)
    

    def read(self, columns: list[str], year: int, pattern: str | None = None) -> pl.LazyFrame:
        """Read the cached file of the dataset (or the raw file if there is no cached copy yet)."""
        cache_path      = self.get_cache_path(year = year)
        target_columns  = [pl.col(pattern)] if pattern else []

        if pattern is None and cache_path.exists():
            table = pl.scan_parquet(source = cache_path)
        else:
            table = self._read_raw(year = year, pattern = pattern)

        return _keep_persons(lf = table.select(*self.unit.cols, *columns, *target_columns),
                          unit = self.unit)
    

    def _read_raw(self, year: int, pattern: str | None = None, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Open the delivered file: its keys plus the given variables, each cast to its dtype
        Columns matching pattern are kept as delivered: for survey targets only."""

        key_columns         = sorted(self.unit, key = lambda key: key.name)
        variable_columns    = [variable.name for variable in self.variables]
        target_columns      = [pl.col(pattern)] if pattern else []

        if self.start is not None:
            assert self.end in variable_columns, f"{self.name}: end column {self.end} is not a declared variable"

        # open the file, unless a piece of it is given
        raw = lf if lf is not None else _scan(
            path = self.get_raw_path(year = year),
            columns = [*self.unit.cols, *variable_columns], pattern = pattern)
        
        # a yearly file without a year column gets one
        if "year" in self.unit.cols and "year" not in raw.collect_schema().names():
            raw = raw.with_columns(year = pl.lit(value = year, dtype = pl.Int16))
        
        # every column in its declared dtype
        typed = raw.select(*[_parse_dtype(variable = key, year = year) for key in key_columns],
                           *[_parse_dtype(variable = variable, year = year) for variable in self.variables],
                           *target_columns)

        # only the spells that touch this year
        in_year = typed.filter(self._touches(year = year)) if self.start is not None else typed

        return in_year.select(*self.unit.cols, *variable_columns, *target_columns)
            



# --- HELPERS FOR READING FILES ---

# --- reading in one go --- 
def _scan(path: Path, columns: list[str], pattern: str | None = None) -> pl.LazyFrame:
    """Open a delivered file lazily, whatever its format; values as delivered."""
    if path.suffix == ".parquet":
        return pl.scan_parquet(source = path)
    if path.suffix == ".csv":
        with open(path, encoding = "utf-8", errors = "replace") as f:
            header = f.readline()
        separator = ";" if header.count(";") > header.count(",") else ","
        return pl.scan_csv(source = path, separator = separator, infer_schema = False, low_memory = True)
    if path.suffix == ".sav":
        import pyreadstat
        _, meta = pyreadstat.read_sav(path, metadataonly = True)
        present = [c for c in meta.column_names
                   if c in columns or (pattern and re.match(pattern, c))]
        df, _ = pyreadstat.read_sav(path, usecols = present)
        return (pl.from_pandas(df).lazy()
                .with_columns(pl.col(pl.Date, pl.Datetime).dt.strftime("%Y%m%d")))
    raise ValueError(f"{path.name}: unknown file type")


# --- reading in pieces ---
def _csv_pieces(path: Path, columns: list[str], rows: int = 128 * 2**20):
    """The csv in pieces of about 128 MB, every column as text: memory stays at one piece."""
    with open(path, encoding = "utf-8-sig", newline = "") as f:
        header = next(csv.reader(f))
    reader = pacsv.open_csv(
        path,
        read_options = pacsv.ReadOptions(block_size = rows),
        convert_options = pacsv.ConvertOptions(
            column_types = {c: pa.string() for c in header},        # text: keeps leading zeros
            include_columns = [c for c in columns if c in header],
            strings_can_be_null = True, null_values = [""]))        # only a blank is missing
    for batch in reader:
        yield pl.from_arrow(batch)

def _parquet_pieces(path: Path, columns: list[str], rows: int = 2_000_000):
    file = pq.ParquetFile(path)
    keep_columns = [c for c in columns if c in file.schema_arrow.names]
    for batch in file.iter_batches(batch_size = rows, columns = keep_columns):
        yield pl.from_arrow(batch)

def _sav_pieces(path: Path, columns: list[str], rows: int = 2_000_000):
    import pyreadstat
    _, meta = pyreadstat.read_sav(path, metadataonly = True)
    keep_columns = [c for c in columns if c in meta.column_names]
    for df, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(path),
                                                chunksize = rows, usecols = keep_columns):
        yield (pl.from_pandas(df)
               .with_columns(pl.col(pl.Date, pl.Datetime).dt.strftime("%Y%m%d")))

PIECES = {".csv": _csv_pieces, ".parquet": _parquet_pieces, ".sav": _sav_pieces}


# --- typing the read columns --- 
def _parse_dtype(variable: Key | Variable, year: int) -> pl.Expr:
    """One column in its declared dtype: CBS codes replaced first, then cast or parsed"""

    dtype = variable.dtype
    text = pl.col(variable.name).cast(pl.String).str.strip_chars()

    if dtype.is_numeric() or dtype in (pl.Date, pl.Boolean):
        text = text.str.replace(r"\.0$", "")

    if variable.codebook:
        book = {code: None if value is None else value.format(year = year)
                for code, value in variable.codebook.items()}
        text = text.replace(book)

    if variable.dtype == pl.Date:
        return pl.coalesce(
            text.str.to_date(format = variable.format, strict = False),
            text.str.to_date(format = "%Y-%m-%d", strict = False),
            ).alias(variable.name)
    
    if variable.dtype == pl.Boolean:
        return text.cast(dtype = pl.Int8).cast(pl.Boolean)
   
    return text.cast(dtype).alias(variable.name)