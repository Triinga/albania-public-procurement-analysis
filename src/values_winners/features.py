"""Feature creation, discretization and binarization of the value and winner columns.

Builds on the cleaned data with the chosen missing-value strategy. Only
row-level features are created here; aggregations per winner belong to the
aggregation step.

Usage (from the repository root):
    python -m src.values_winners.features [csv_folder]

If no folder is given, data/raw/ is used. The result is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.cleaning import JOINT_SEPARATOR
from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.features import compare_discretizations, discretize_by_quantiles, to_binary
from src.values_winners.cleaning import KEYS, clean
from src.values_winners.columns import COLUMNS
from src.values_winners.missing_values import apply_strategy, mark_disguised_missing

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
FUND_LABELS = ["Shumë i vogël", "I vogël", "I mesëm", "I madh"]
MISSING_FLAGS = ["Fondi_limit_missing", "Vlera_e_fituesit_missing", "Fituesi_missing"]


def prepare(raw):
    """Cleaned columns with disguised missing values marked and missing flags added."""
    return apply_strategy(mark_disguised_missing(clean(raw)))


def add_features(df):
    """New row-level features."""
    df = df.copy()
    df["kursimi"] = df["Fondi_limit"] - df["Vlera_e_fituesit"]
    df["kursimi_pct"] = (df["kursimi"] / df["Fondi_limit"] * 100).round(2)
    df["nr_fituesve"] = df["Fituesi"].str.split(JOINT_SEPARATOR, regex=False).str.len().astype("Int64")
    df["fitues_i_perbashket"] = df["nr_fituesve"].gt(1).where(df["Fituesi"].notna())
    return df


def discretize(df):
    df = df.copy()
    df["kategoria_e_fondit"] = discretize_by_quantiles(df["Fondi_limit"], FUND_LABELS)
    return df


def binarize(df):
    """Yes/no columns as 0/1."""
    df = df.copy()
    df["me_tvsh"] = to_binary(df["Lidhja_e_kontrates_me_TVSH"])
    df["fitues_i_perbashket"] = to_binary(df["fitues_i_perbashket"])
    for flag in MISSING_FLAGS:
        df[flag] = to_binary(df[flag])
    return df


def features_summary(df):
    rows = [
        ("kursimi", "Created", "Fondi_limit - Vlera_e_fituesit (lekë)"),
        ("kursimi_pct", "Created", "kursimi / Fondi_limit * 100"),
        ("nr_fituesve", "Created", "Number of winners in the cell (consortium members)"),
        ("fitues_i_perbashket", "Created + binarized", "1 if the contract was won by a consortium"),
        ("kategoria_e_fondit", "Discretized", "Fondi_limit in 4 equal-frequency bins"),
        ("me_tvsh", "Binarized", "Lidhja_e_kontrates_me_TVSH: Po/Jo -> 1/0"),
        *[(f, "Binarized", "Missing-value flag -> 1/0") for f in MISSING_FLAGS],
    ]
    return pd.DataFrame([
        {"feature": name, "step": step, "definition": definition,
         "non_null": int(df[name].notna().sum()), "dtype": str(df[name].dtype)}
        for name, step, definition in rows
    ])


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder, columns=KEYS + list(COLUMNS))
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df = binarize(discretize(add_features(prepare(raw))))
    summary = features_summary(df)
    bins = compare_discretizations(df["Fondi_limit"], len(FUND_LABELS))
    bins.insert(1, "label", FUND_LABELS)
    fund_categories = df["kategoria_e_fondit"].value_counts(sort=False, dropna=False).rename_axis(
        "kategoria_e_fondit").reset_index(name="procedures")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "features_summary.csv", index=False)
    bins.to_csv(OUT_DIR / "discretization_fund.csv", index=False)
    fund_categories.to_csv(OUT_DIR / "fund_categories.csv", index=False)
    df.to_csv(PROCESSED_DIR / "values_winners_features.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_colwidth", 60):
        print(summary.to_string(index=False))
        print("\nDiscretization of Fondi_limit (equal width vs equal frequency):")
        print(bins.to_string(index=False))
        print()
        print(fund_categories.to_string(index=False))


if __name__ == "__main__":
    main()
