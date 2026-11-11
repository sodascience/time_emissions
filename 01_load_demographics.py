# --- load the config files ---
from config.surveys import *


# create a dictionary with all features per output unit 
OUTPUTS = {unit: features_of(unit) for unit in OUTPUT_UNITS}    # the features of each output table

# check whether feature names per output unit are unique
for unit, features in OUTPUTS.items():
    assert features, f"no theme class in features.py for {unit!r}"



# --- write the typed copies of datasets and the mapping tables ---
for year in YEARS:
    for ds in Datasets.all():
        if ds.name in ("budgetonderzoek", "tbo"): # do not process the survey datasets for now
            continue
        if not (isinstance(ds.files, str) or year in ds.files):
            continue
        if ds.get_cache_path(year = year).exists():
            log.info(f"{year}: {ds.name} is already cached")
            continue
        log.info(f"{year}: writing {ds.name} to cache")
        ds.write_cache(year = year)

    for m in Mappings.all():
        months = range(1,13) if "month" in m.unit.cols else [0]     # 0: a yearly table, in one file
        for month in months:
            if m.get_cache_path(year = year, month = month).exists():
                log.info(f"\t{month:02d}-{year}: {m.name} is already written")
                continue
            log.info(f"\t{month:02d}-{year}: computing and writing {m.name}")
            table = m.compute(year = year)
            if month:
                table = table.filter(pl.col("month") == month)
            m.write_cache(table = table, year = year, month = month)
                 



# --- write the output features ---
for year in YEARS:
    for unit in sorted(OUTPUT_UNITS, key = len, reverse = True):        # persons first: households reuse them
        for feature in OUTPUTS[unit]:
            if (feature.get_folder(year = year) / "done").exists():
                log.info(f"{year}: {feature.name} is already written")
                continue
            try:
                feature.write(year = year)
            except Exception:
                print(feature.variable.describe())
                raise



log.info("done")