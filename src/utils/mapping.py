from __future__ import annotations

import polars as pl
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import helpers
from .helpers import Named, _label, FAR_FUTURE, _keep_persons
from .unit import Unit
from .dataset import Dataset


@dataclass(eq = False)
class Mapping(Named):
    """A table of links: which rows of one kind go with which rows of another."""

    # fields
    unit: Unit                              # the keys of one row of its table
    recipe: Callable[[int], pl.LazyFrame]   # year -> the table
    dataset: Dataset                        # its file for the year names the cache
    name: str | None = None                 # used in messages; set from the attribute

    def __repr__(self) -> str:
        return _label(kind = "Mapping", name = self.name, unit = self.unit,
                      dataset = self.dataset.name)
    

    # methods
    def compute(self, year: int) -> pl.LazyFrame:
        """Run the recipe for one year: one row per link, sorted by its keys."""

        lf = self.recipe(year)

        if "cover" in lf.collect_schema().names():          # a spell mapping: merge repeat spells
            return lf.group_by(self.unit.cols).agg(pl.col("cover").sum(),
                                                   pl.col("clip_start").min(),
                                                   pl.col("clip_end").max())
        
        else:
            return lf.select(self.unit.cols).unique()
        
        
    def get_cache_path(self, year: int, month: int | None = None) -> Path:
        """Cache file for this year, named after its source file: new delivery, new name."""
        from config.datasets import CACHE

        folder = CACHE / "mappings"/ self.dataset.name / f"{year}_{self.dataset.get_raw_path(year = year).stem}"
        return folder if month is None else folder / f"{month:02d}.parquet"
    

    def write_cache(self, table: pl.LazyFrame, year: int, month: int) -> None:
        """Save a computed table to the cache."""
        assert helpers.SAMPLE is None, "no mapping tables while testing on a sample"

        path = self.get_cache_path(year = year, month = month)
        path.parent.mkdir(parents = True, exist_ok = True)

        table.sink_parquet(path = path)


    def read(self, year: int) -> pl.LazyFrame:
        """Open the saved table. Fails if write has not run for this year."""
        return _keep_persons(
            lf = pl.scan_parquet(source = self.get_cache_path(year = year) / "*.parquet"), 
            unit = self.unit)
    



def compute_calendar(year: int) -> pl.LazyFrame:
    """The first grid: one row per calendar month, with its first and last day."""
    return (
        pl.LazyFrame(data = {"month": range(1, 13)}, schema = {"month": pl.Int8})
        .with_columns(year = pl.lit(value = year, dtype = pl.Int16),
                      clip_start = pl.date(year = year, month = pl.col("month"), day = 1))
        .with_columns(clip_end = pl.col("clip_start").dt.month_end())
    )


def _explode(bus: pl.LazyFrame, start: str, end: str, grid: pl.LazyFrame) -> pl.LazyFrame:
    """Clip each spell to every grid row it overlaps; count the days in 'cover'."""
    from config.units import PERSON
    on = [c for c in PERSON.cols if c in grid.collect_schema().names()]

    bus = (bus.with_columns(s_start = pl.col(start),
                            s_end = pl.col(end).fill_null(value = FAR_FUTURE))
                            .drop("year", strict = False))

    overlap = [pl.col("s_start") <= pl.col("clip_end"),         # began before the grid row ended
               pl.col("s_end") >= pl.col("clip_start")]         # ended before the grid row began
    if on:
        joined = bus.join(other = grid, on = on).filter(*overlap)
    else:                                                       # the calendar: no keys to match
        joined = bus.join_where(grid, *overlap)
    
    lo = pl.max_horizontal("s_start", "clip_start")
    hi = pl.min_horizontal("s_end", "clip_end")
    return joined.with_columns(clip_start = lo, clip_end = hi,  # the new, smaller spell-month
                               cover = (hi - lo).dt.total_days() + 1)


def make_spell_mapping(links: Unit, dataset: Dataset, 
                       grid: Callable[[int], pl.LazyFrame] | None = None) -> Mapping:
    """Make a spell mapping: links 'links' to a person's household spell-months,
    through the spells in 'dataset' that run from 'start' to 'end'."""

    from config.units import PERSON, HH_SPELL, MONTH
    assert dataset.start is not None, f"{dataset.name}: a bus needs start and end, see Dataset"

    def new_recipe(year: int) -> pl.LazyFrame:
        from config.mappings import Mappings
        months = (grid(year) if grid is not None
                  else Mappings.HOUSEHOLD_PERSON.read(year = year).drop("cover"))
        bus = dataset.read(columns = [dataset.end], year = year)
        return _explode(bus = bus, start = dataset.start, end = dataset.end, grid = months)
    
    return Mapping(unit = links | PERSON | HH_SPELL | MONTH, recipe = new_recipe, dataset = dataset)
