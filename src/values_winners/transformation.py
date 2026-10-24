"""Transformation of the numeric value and winner columns.

Amounts in lek have a very long right tail, so they are first log-transformed
and then scaled: min-max normalization to [0, 1] and z-score standardization.
Savings (`kursimi`, `kursimi_pct`) are not transformed yet: they contain the
logically impossible values (winner value far above the fund) that are handled
in Part II, and would distort any scaling. Missing values stay missing.

Usage (from the repository root):
    python -m src.values_winners.transformation [csv_folder]

If no folder is given, data/raw/ is used. The result is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.transform import describe_transformation, log_transform, min_max, summarize, z_score
from src.values_winners import features
from src.values_winners.cleaning import KEYS
from src.values_winners.columns import COLUMNS

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
AMOUNTS = ["Fondi_limit", "Vlera_e_fituesit", "Vlera_e_fituesit_ne_lidhjen_e_kontrates"]


def build(raw):
    """All earlier steps: cleaning, missing values, features, discretization, binarization."""
    return features.binarize(features.discretize(features.add_features(features.prepare(raw))))


def transform(df):
    """Add log, min-max and z-score versions of the numeric columns."""
    df = df.copy()
    rows = []
    for col in AMOUNTS:
        log = log_transform(df[col])
        df[f"{col}_log"] = log
        df[f"{col}_log_minmax"] = min_max(log)
        df[f"{col}_log_z"] = z_score(log)
        rows += [
            describe_transformation(df[col], log, col, "log(1 + x)"),
            describe_transformation(df[col], min_max(df[col]), col, "min-max (without log)"),
            describe_transformation(df[col], df[f"{col}_log_minmax"], col, "log + min-max"),
            describe_transformation(df[col], df[f"{col}_log_z"], col, "log + z-score"),
        ]
    return df, summarize(rows)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder, columns=KEYS + list(COLUMNS))
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df, summary = transform(build(raw))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "transformation_summary.csv", index=False)
    df.to_csv(PROCESSED_DIR / "values_winners_transformed.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
