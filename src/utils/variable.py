from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .mapping import Mapping

import polars as pl
from dataclasses import dataclass, field
from typing import Callable
import operator
from collections import defaultdict
import os

from . import helpers
from .helpers import Named, _label, VALUE, _keep_persons, make_stamp
from .unit import Unit
from .dataset import Dataset


@dataclass(eq = False)
class Variable(Named):
    """A column of a dataset, or a recipe built from columns."""

    # fields
    name: str | None = None             # set from the attribute; the column name for columns
    dataset: Dataset | None = None      # where the column lives; only for columns
    dtype: pl.DataType | None = None    # its type on read; only for columns
    format: str = "%Y%m%d"              # dates only: how the date is written
    description: str = ""               # what it measures
    codebook: dict[str, str | None] = field(default_factory = dict) # CBS code -> value; None = missing
    unit: Unit | None = None            # the keys of one row; filled for columns
    recipe: Callable[[int], pl.LazyFrame] | None = None     # year -> keys + "value" (+ "cover")
    inputs: tuple[Variable, ...] = ()   # the variables it was built from
    step: str = ""

    def __post_init__(self) -> None:
        """For a column: take the dataset's unit and make the recipe that reads it."""
        if self.dataset is not None:
            assert self.dtype, "a dataset column needs a dtype"
            ds = self.dataset           # the name arrives later, from the attribute
            self.unit = ds.unit
            self.recipe = lambda year: (ds.read(columns = [self.name], year = year)
                                        .rename(mapping = {self.name: "value"}))

    def __repr__(self) -> str:
        """A column prints the dataset it originates from, the dtype, unit, and description.
        A non-native variable prints the steps that made it."""
        if self.dataset is not None:
            return _label(kind = "Variable", name = self.name, dataset = self.dataset.name,
                          dtype = self.dtype, unit = self.unit, description = self.description)
        else: 
            return _label(kind = "Variable", name = self.name, unit = self.unit, 
                          step = self.step, description = self.description)

    # --- running ---
    def compute(self, year: int) -> pl.LazyFrame:
        """Run the recipe for one year. Opens no file itself."""
        return self.recipe(year)
    
    
    def describe(self, indent: str = "") -> str:
        """The chain behind this variable: each step and the unit it ends at."""
        if self.dataset is not None:
            return f"{indent}{self.name} ({self.dataset.name}) -> {self.unit!r}"
        deeper = indent + " " if len(self.inputs) > 1 else indent
        lines = [v.describe(indent = deeper) for v in self.inputs]
        return "\n".join([*lines, f"{indent}{self.step} -> {self.unit!r}"])
    
    def write_cache(self) -> None:
        """Compute once per year and save it; every later use reads the file instead"""
        compute = self.recipe
        
        def new_recipe(year: int) -> pl.LazyFrame:
            if helpers.SAMPLE is not None:
                return compute(year)
            
            from config.datasets import CACHE
            stamp = make_stamp(self.describe())
            path = CACHE / "divided" / f"{year}_{stamp}.parquet"

            if not path.exists():
                if helpers.BATCH is not None:
                    return compute(year = year)
                path.parent.mkdir(parents = True, exist_ok = True)
                temp = path.with_suffix(".tmp")
                compute(year).sink_parquet(path = temp)
                os.replace(temp, path)

            return _keep_persons(lf = pl.scan_parquet(source = path), unit = self.unit)
        
        self.recipe = new_recipe
        return self

    

    # --- moving to another unit ---
    def move(self, to: Unit, condition: pl.Expr | Variable | None = None, weight: pl.Expr | None = None,
             agg_method: pl.Expr | None = None, via: Mapping | None = None) -> Variable:
        """Move to unit 'to': look up the keys it lacks, filter, divide, fold the rest away. 
        Without a weight, a value is copied to every new row; with  one, it is divided over htem. 
        agg_method says how rows combine; it is needed when the lookk-up leaves keys that 'to' lacks."""

        v = self

        # 1. if the goal unit is larger than the origin unit, 
        # find the corresponding mapping and join the missing keys
        # the variable values will then be copied to all new rows
        if not to <= self.unit: 
            v = v._join(mapping = _get_mapping(origin = self.unit, to = to, via = via))
        
        # 2. keep the rows that fulfill a specified condition
        if condition is not None:
            v = v._filter(condition = condition, per = self.unit.cols if weight is not None else None)

        # 3. divide the variable values by a specified weight (e.g. number of days lived in apartment) and fallback option (e.g. 1 per row if nobody lived in the apartment)
        if weight is not None:
            v = v._divide(weight = weight, per = self.unit.cols)
        
        # 4. if there are more keys in the current unit than in the goal unit
        # collapse the multiple rows per current unit according to agg_method to reach the goal unit
        if v.unit != to or agg_method is not None:         # 3. fold away what 'to' lacks
            assert agg_method is not None, f"{v.unit -to!r} left over on the way to {to!r}: give agg_method"
            v = v._collapse(to = to, agg_method = agg_method)
        
        # 5. write to cache if variable needed weighting (because computing these variables requires a lot of memory)
        if weight is not None:
            v.write_cache()

        return v
    

    # --- building blocks ---
    def _join(self, mapping: Mapping) -> Variable:
        """Join this mapping's table. Shared by join_mapping, aggregate, and disaggregate."""
        unit = self.unit | mapping.unit
        on = (self.unit & mapping.unit).cols

        def new_recipe(year: int) -> pl.LazyFrame:
            lf = self.compute(year = year).drop("cover", "clip_start", strict = False)
            joined = lf.join(other = mapping.read(year = year), on = on)
            return _tidy(lf = joined, unit = unit)
        
        return Variable(unit = Unit(*unit), recipe = new_recipe,
                        inputs = (self,), step = f"join {mapping.name}")
    

    def _filter(self, condition: pl.Expr, per: list[str] | None = None) -> Variable:
        """Step 2: remove rows. The condition is a Polars expression, whose columns are added 
        automatically, or a boolean Variable at this unit or a coarser one."""

        is_variable = isinstance(condition, Variable)
        assert not is_variable or condition.unit <= self.unit, f"{condition.unit!r} is finer than {self.unit!r}"

        def new_recipe(year: int) -> pl.LazyFrame:
            lf = self.compute(year = year)
            if is_variable:
                values = condition.compute(year = year).select(*condition.unit.cols, _keep = VALUE)
                lf = lf.join(values, on = condition.unit.cols, how = "left")
            else:
                lf = _add_columns(lf = lf, names = condition.meta.root_names(), unit = self.unit, year = year)
                lf = lf.with_columns(_keep = condition)
            keep = pl.col("_keep").fill_null(False)
            if per is not None:
                keep = keep | ~keep.any().over(per)
            return _tidy(lf = lf.filter(keep), unit = self.unit)
        
        name = condition.name if is_variable else condition
        return Variable(unit = self.unit, recipe = new_recipe,
                        inputs = (self, condition) if is_variable else (self,),
                        step = f"filter {name}" + (", else all" if per else ""))
    

    def _divide(self, weight: pl.Expr, per: list[str]) -> Variable:
        """Step 2: divide each input row's value over its rows here, in proportion to weight.
        fallback is a second weight, used only where the weight sums to 0 for an input row."""

        def new_recipe(year: int) -> pl.LazyFrame:
            lf = _add_columns(lf = self.compute(year = year), names = weight.meta.root_names(),
                              unit = self.unit, year = year)
            
            total = weight.sum().over(per)
            share = pl.when(total > 0).then(weight / total)
            return _tidy(lf = lf.with_columns(VALUE * share), unit = self.unit)     # drops _w, _f
        
        return Variable(unit = self.unit, recipe = new_recipe,
                        inputs = (self, ), step = f"divide by {weight}")
    

    def _collapse(self, to: Unit, agg_method: pl.Expr) -> Variable:
        """Step 3: drop keys; group by a subset of the unit and combine rows with agg_method."""
        assert to <= self.unit, "_collapse can only drop keys"

        def new_recipe(year: int) -> pl.LazyFrame:
            names = agg_method.meta.root_names()
            lf = _add_columns(lf = self.compute(year = year), names = names,
                              unit = self.unit, year = year)
            return lf.group_by(to.cols).agg(agg_method.alias("value"))
        
        return Variable(unit = Unit(*to), recipe = new_recipe,
                        inputs = (self,), step = "_collapse")
           

    # --- transform and operators ---
    def _fill(self, value: object) -> Variable:
        """The variable on every row of the household table, with fill where it has no value:
        for a value whose absence means zero, such as the hours of somehone without a job"""
        
        def new_recipe(year: int) -> pl.LazyFrame:
            from config.mappings import Mappings
            spine = Mappings.HOUSEHOLD_PERSON.read(year = year).select(*self.unit.cols)
            if "RINPERSOON" not in self.unit.cols:
                spine = spine.unique()      # only for the household table
            return (spine.join(other = self.compute(year = year), on = self.unit.cols, how = "left")
                    .with_columns(VALUE.fill_null(value)))
        
        return Variable(unit = self.unit, recipe = new_recipe,
                        inputs = (self,), step = f"fill {value}")


    def transform(self, expr: pl.Expr | Callable[[int], pl.Expr]) -> Variable:
        """Apply any Polars expression to the value, within one frame."""
        def new_recipe(year: int) -> pl.LazyFrame:
            e = expr if isinstance(expr, pl.Expr) else expr(year)
            lf = _add_columns(lf = self.compute(year = year), names = e.meta.root_names(),
                              unit = self.unit, year = year)
            return _tidy(lf = lf.with_columns(e.alias("value")), unit = self.unit)
        
        return Variable(unit = self.unit, recipe = new_recipe,
                        inputs = (self,), step = "transform")
    

    def combine(self, other: Variable | float | str,
                    op: Callable[[pl.Expr, pl.Expr], pl.Expr],
                    fill: float | None = None) -> Variable:
        """Join two variables on their unit and apply op; a plain value needs no join."""
        if not isinstance(other, Variable):
            return self.transform(expr = op(VALUE, pl.lit(other)))
        assert self.unit == other.unit, "different units"
        k = self.unit.cols

        def new_recipe(year: int) -> pl.LazyFrame:
            joined = self.compute(year = year).join(other = other.compute(year = year),
                                                    on = k, how = "full", coalesce = True)
            a, b = VALUE, pl.col("value_right")
            left, right = fill if isinstance(fill, tuple) else(fill, fill)
            if left is not None:
                a = a.fill_null(left)
            if right is not None:
                b = b.fill_null(right)
            return joined.select(*k, value = op(a, b))
            
        return Variable(unit = self.unit, recipe = new_recipe,
                        inputs = (self, other), step = op.__name__)
        

    # arithmetic: + and - treat a missing side as 0, * and / keep it missing
    def __add__(self, other):       return self.combine(other = other, op = operator.add, fill = (0, 0))
    def __sub__(self, other):       return self.combine(other = other, op = operator.sub, fill = (None, 0))
    def __mul__(self, other):       return self.combine(other = other, op = operator.mul)
    def __truediv__(self, other):   return self.combine(other = other, op = operator.truediv)
    __radd__, __rmul__ = __add__, __mul__       # so 12 * v and sum([...]) work

    # comparisons: each returns a boolean Variable; a missing side stays missing
    def __eq__(self, other): return self.combine(other = other, op = operator.eq)
    def __ne__(self, other): return self.combine(other = other, op = operator.ne)
    def __lt__(self, other): return self.combine(other = other, op = operator.lt)
    def __le__(self, other): return self.combine(other = other, op = operator.le)
    def __gt__(self, other): return self.combine(other = other, op = operator.gt)
    def __ge__(self, other): return self.combine(other = other, op = operator.ge)

    # combining conditions: use & | ~ with brackets; and/or/not cannot be redefined
    def __and__(self, other): return self.combine(other = other, op = operator.and_)
    def __or__(self, other): return self.combine(other = other, op = operator.or_)
    def __invert__(self, other): return self.transform(expr = ~VALUE)

    __hash__ = object.__hash__           # redefining == would otherwise make it unhashable




def _tidy(lf: pl.LazyFrame, unit: Unit) -> pl.LazyFrame:
    """Keep the unit's keys, value, cover and clip_start; drop everything else."""
    extra = [c for c in ("cover", "clip_start") if c in lf.collect_schema().names()]
    return lf.select(*unit.cols, "value", *extra)


def _add_columns(lf: pl.LazyFrame, names: list[str], unit: Unit,
                 year: int) -> pl.LazyFrame:
    """Join the named columns the frame lacks: columns are read, chain variables computed."""
    from config.variables import Variables                             # at call time: both import core
    from config.features import Chains
    sources = {v.name: v for v in Variables.all() + Chains.all()}
    have = set(lf.collect_schema().names())
    by_dataset = defaultdict(list)                              # a dict starting each key with []
    chains = []
    for n in names:
        if n in sources and n not in have:                      # only what's missing
            source = sources[n]
            if source.dataset is not None:
                by_dataset[source.dataset].append(source)       # grouped: one read per file
            else:
                chains.append(source)
    for ds, variables in by_dataset.items():
        assert ds.unit <= unit, f"{ds.unit.cols} is finer than {unit.cols}"
        lf = lf.join(other = ds.read(columns = [v.name for v in variables], year = year),
                     on = ds.unit.cols, how = "left")
    for v in chains:
        assert v.unit <= unit, f"{v.unit.cols} is finer than {unit.cols}"
        column = v.compute(year = year).select(*v.unit.cols, VALUE.alias(v.name))
        lf = lf.join(other = column, on = v.unit.cols, how = "left")
    return lf





def _get_mapping(origin: Unit, to: Unit, via: Mapping | None = None) -> Mapping:
    """The mapping that reaches 'to': it shares the most keys with this variable,
    then adds the fewest keys beyond 'to'. via= chooses one by hand."""
    if via is not None: 
        return via
    from config.mappings import Mappings        # at call time: mappings.py import core

    def shared(m: Mapping) -> int:              # keys in common, besides time
        return len(set((origin & m.unit).cols) - {"year", "month"})
    
    def added(m: Mapping) -> int:               # keys the join brings that 'to' does not want
        return len((origin | m.unit) - to)
    
    fits = [m for m in Mappings.all() if shared(m) and to <= origin | m.unit]
    assert fits, f"no mapping leads from {origin!r} to {to!r}"
    fits = [m for m in fits if shared(m) == max(shared(f) for f in fits)]
    fits = [m for m in fits if added(m) == min(added(f) for f in fits)]
    assert len(fits) == 1, f"{[m.name for m in fits]} all lead to {to!r}: choose with via="
    return fits[0]