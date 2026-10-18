"""Data types of the value and winner columns (2016-2025).

Usage (from the repository root):
    python -m src.values_winners.data_types [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.data_types import describe_types
from src.values_winners.columns import COLUMNS

OUT_DIR = Path("reports/values_winners")


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df = read_years(folder, columns=list(COLUMNS))
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(df):,} procedures\n")

    types = describe_types(df, COLUMNS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    types.to_csv(OUT_DIR / "data_types.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 60):
        print(types.to_string(index=False))


if __name__ == "__main__":
    main()
