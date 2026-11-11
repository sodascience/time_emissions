from config.surveys import *
from src.utils.core.helpers import _out

class Look:
    """One household in one year: the written tables, the delivered data and the steps of 
    a feature, each restricted to that household."""

    def __init__(self, household, year: int):
        self.household, self.year   = household, year

        spine               = Mappings.HOUSEHOLD_PERSON.read(year = year).filter(pl.col("HUISHOUDNR") == household)

        self.households     = spine.select(*HH_SPELL.cols).unique().collect()

        self.persons        = spine.select(*PERSON.cols).unique().collect()

        persons             = self.persons.lazy()

        self.addresses      = (Mappings.ADDRESS_PERSON.read(year = year)
                               .join(persons, on = PERSON.cols, how = "semi")
                               .select(*ADDRESS.cols).unique().collect())
        
        self.breadwinners   = (Mappings.BREADWINNER_PERSON.read(year = year)
                               .join(persons, on = PERSON.cols, how = "semi")
                               .select(*BREADWINNER.cols).unique().collect())
        
    def scoped(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """Keep the rows of this household, by the first of its key sets that the frame has."""
        have = set(lf.collect_schema().names())
        for keys in (self.households, self.persons, self.addresses, self.breadwinners):
            if set(keys.columns) <= have:
                return lf.join(keys.lazy(), on = keys.columns, how = "semi")
        return lf
    

    @property
    def tables(self) -> dict[str, pl.DataFrame]:
        """The written output tables"""
        spine = self.scoped(Mappings.HOUSEHOLD_PERSON.read(year = self.year))
        tables = {}
        for unit in OUTPUT_UNITS:
            table = spine.select(*unit.cols).unique()
            for f in features_of(unit):
                if (f.get_folder(year = self.year) / "done").exists():
                    table = table.join(f.read(year = self.year), on = unit.cols, how = "left")
            tables[TABLE_NAMES[unit]] = table.sort(unit.cols).collect()
        return tables
    
    
    @property
    def raw(self) -> dict[str, pl.DataFrame]:
        """The delivered data, typed: one frame per dataset, with every declared column."""
        return {ds.name: self.scoped(ds.read(columns = [v.name for v in ds.variables], year = self.year)).collect()
                for ds in Datasets.all() if isinstance(ds.files, str) or self.year in ds.files}
    

    def trace(self, what: Variable | Feature) -> dict[str, pl.DataFrame]:
        """Every step of a chain, from its columsn to the final value."""
        steps: dict[str, pl.DataFrame] = {}
        def walk(v:Variable) -> None:
            for earlier in v.inputs:
                walk(earlier)
            label = f"{len(steps) + 1}. " + v.describe().splitlines()[-1]
            steps[label] = self.scoped(v.compute(year = self.year)).collect()
        walk(what.variable if isinstance(what, Feature) else what)
        return steps
    
    
    def export(self, trace_features: list[Feature] = [], path: Path | str | None = None) -> Path:
        """One excel workbook for this household: an overview, the written tables, the delivered data,
        and for each feature the steps from raw columns to the written value."""
        import xlsxwriter
        path = Path(path or _out() / "demographics" / "debug" / f"{self.household}_{self.year}.xlsx")
        path.parent.mkdir(parents = True, exist_ok = True)

        print(f"Writing {path}")

        wb = xlsxwriter.Workbook(str(path))
        bold = wb.add_format({"bold": True})

        def put(df: pl.DataFrame, sheet: str, row: int = 0, label: str | None = None) -> int:
            """Write a frame under an optional label; return the next free row."""
            sheet = sheet[:31]
            ws = wb.get_worksheet_by_name(sheet) or wb.add_worksheet(sheet)
            if label:
                ws.write(row, 0, label, bold)
                row += 1
            df.write_excel(workbook = wb, worksheet = sheet, position = (row, 0),
                           autofit = True, autofilter = label is None)
            return row + df.height + 3
        
        features = [(t, f) for t in TABLES for f in t.all()]
        overview = pl.DataFrame({
            "table":        [TABLE_NAMES[t.unit] for t, f in features],
            "feature":      [f.name for t, f in features],
            "description":  [f.description for t, f in features],
            "chain":        [f.variable.describe().replace("\n", " > ") for t, f in features]})
        row = put(self.persons, "overview", label = f"household {self.household}, year {self.year}: persons")
        row = put(self.households, "overview", row , label = "household spells")
        put(overview, "overview", row, label = "features")

        for name, df in self.tables.items():
            put(df, f"out {name}")
        for name, df in self.raw.items():
            if df.height:
                put(df, f"raw {name}")
        
        for f in trace_features:
            row = 0
            for label, df in self.trace(f).items():
                row = put(df, f"steps {f.name}", row, label = label)
        wb.close()

        print(f"Successfully written {path}")
        return path
        