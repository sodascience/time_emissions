from config.mappings import *

# --- aggregations ---
SUM     = VALUE.sum()
MEAN    = VALUE.mean()
MEDIAN  = VALUE.median()
FIRST   = VALUE.first()
MOST_COMMON = VALUE.drop_nulls().mode().sort().first()                                              # keep most common value but only if not None
LONGEST    = VALUE.sort_by(by = ["cover", "clip_start"], descending = True).drop_nulls().first()    # keep longest, but only if not None

def share(of) -> pl.Expr:
    return (VALUE == of).mean()

def count(of) -> pl.Expr:
    return (VALUE == of).sum()

def any_of(value) -> pl.Expr:
    return (VALUE == value).any()


def add_up(*parts: Variable) -> Variable:
    """The sum of variables at the same unit: stacked, then summed once per row. Gives the same result as a + b + c, without a join for every +."""
    unit = parts[0].unit
    assert all(p.unit == unit for p in parts), "add_up needs variables at one unit."

    def new_recipe(year: int) -> pl.LazyFrame:
        stacked = pl.concat([p.compute(year = year).select(*unit.cols, VALUE) for p in parts],
                            how = "vertical_relaxed")
        return stacked.group_by(unit.cols).agg(SUM)
    
    return Variable(unit = unit, recipe = new_recipe, inputs = parts, step = "add_up")

def written(feature: Feature) -> Variable:
    """A feature as it was written to disk: read, not computed again."""
    return Variable(unit = feature.unit, inputs = (feature.variable,),
                    step = f"written {feature.name}",
                    recipe = lambda year: feature.read(year = year).rename({feature.name: "value"}))



def since(start: Variable, month: Variable | int | None = None, in_: str = "years",
          unit: Unit = PERSON | HH_SPELL | MONTH, **move_args) -> Variable:
    if month is None:
        begin = VALUE.dt.year() * 12 + VALUE.dt.month()
    else:
        begin = VALUE * 12 + (pl.col(month.name) if isinstance(month, Variable) else month)
    months = pl.col("year") * 12 + pl.col("month") - begin
    return start.move(to = unit, **move_args).transform(
        expr = months //12 if in_ == "years" else months)


def mean_of(first: Variable, second: Variable) -> Variable:
    """The mean of two variables at the same unit; a missing side is skipped, not counted as 0."""
    return first.combine(second, lambda a, b: pl.mean_horizontal(a, b))


def group_countries(country: Variable, reference: Dataset = Datasets.landaktueelref,
                    group: Variable = Variables.ETNGRP) -> Variable:
    """Group the countries of a varaible into broader categories, by a reference table.
    A country that is not in the table becomes missing."""
    def expr(year: int) -> pl.Expr:
        table = reference.read(columns = [group.name], year = year).collect()
        return VALUE.replace_strict(table[Keys.LAND.name], table[group.name], default = None)
    return country.transform(expr = expr)


def key_as_value(dataset: Dataset, key: Key) -> Variable:
    """One of a dataset's keys as a variable: each row's value is the key itself, 
    such as the start of a spell."""
    return Variable(unit = dataset.unit, step = f"key {key.name}",
                    recipe = lambda year: (dataset.read(columns = [], year = year)
                                           .with_columns(value = pl.col(key.name))))


def highest_paid(variable: Variable, wage: Variable = Variables.SLNINGLD) -> Variable:
    dataset = variable.dataset
    pair = Variable(unit = dataset.unit, step = f"{variable.name} with {wage.name}",
                    recipe = lambda year: (dataset.read(columns = [variable.name, wage.name], year = year)
                                           .select(*dataset.unit.cols,
                                                   value = pl.struct(value = variable.name,
                                                                     wage = wage.name))))
    top = VALUE.sort_by(VALUE.struct.field("wage"), descending = True, nulls_last = True).first()
    return pair.move(to = PERSON | HH_SPELL | MONTH, agg_method = top.struct.field("value"))