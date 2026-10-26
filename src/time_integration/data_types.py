"""Data types analysis for time and integration columns (2016-2025).

Usage (from the repository root):
    python -m src.time_integration.data_types [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.data_types import describe_types
from src.time_integration.columns import COLUMNS, DATETIME_COLS

OUT_DIR = Path("reports/time_integration")


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    # viti is added by read_years, so don't include it in usecols
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = read_years(folder, columns=cols_to_read)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(df):,} procedures\n")

    # viti is not a CSV column: it comes from the file name, like the other text values
    df["viti"] = df["year"].astype(str)
    types = describe_types(df, COLUMNS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    types.to_csv(OUT_DIR / "data_types.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 60):
        print(types.to_string(index=False))


if __name__ == "__main__":
    main()
