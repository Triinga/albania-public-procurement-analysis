"""Reading the yearly procurement files exported from APP."""
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/raw")
YEARS = range(2016, 2026)  # 2026 is excluded because it is incomplete
FILE_PATTERN = "Procedurat_e_prokurimit_-_viti_{year}_*.csv"


def find_year_file(folder, year):
    """Return the CSV for one year; duplicate downloads ("... (1).csv") are skipped."""
    files = [f for f in Path(folder).glob(FILE_PATTERN.format(year=year)) if "(" not in f.name]
    if len(files) != 1:
        raise FileNotFoundError(f"Expected 1 file for {year} in {folder}, found {len(files)}")
    return files[0]


def read_years(folder=DATA_DIR, columns=None, years=YEARS):
    """Read the yearly files into one DataFrame with an added `year` column.

    Everything is read as text so the original format is kept; convert types
    explicitly afterwards (see `to_number`). `columns=None` reads all 21 columns.
    """
    parts = []
    for year in years:
        df = pd.read_csv(find_year_file(folder, year), dtype=str, usecols=columns)
        df["year"] = year
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


def to_number(series):
    """Convert APP amounts stored as text ("230,211.00") to floats; invalid -> NaN."""
    return pd.to_numeric(series.str.replace(",", "", regex=False), errors="coerce")
