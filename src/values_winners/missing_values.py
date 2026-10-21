"""Missing values of the value and winner columns (2016-2025).

1. Identifies the missing values, including disguised ones (fund 0 or <= 1 lek).
2. Looks at where they come from (by year, cancelled procedures, procedure type).
3. Compares treatment strategies and applies the chosen one.

`Anulluar` and `Lloji_i_procedures` (procedure and competition columns) are
read only to explain the missing values.

Usage (from the repository root):
    python -m src.values_winners.missing_values [csv_folder]

If no folder is given, data/raw/ is used. The result is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.cleaning import po_jo_to_bool
from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.missing import (compare_numeric_strategies, missing_by_group,
                                missing_by_year, missing_summary)
from src.values_winners.cleaning import KEYS, clean
from src.values_winners.columns import COLUMNS

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
CONTEXT = ["Anulluar", "Lloji_i_procedures"]
NOT_A_REAL_FUND = 1  # a fund of 0 or <= 1 lek is a placeholder, not an amount


def mark_disguised_missing(df):
    """Fund limits of 0 or <= 1 lek are placeholders: treat them as missing."""
    df = df.copy()
    df["Fondi_limit"] = df["Fondi_limit"].mask(df["Fondi_limit"].le(NOT_A_REAL_FUND))
    return df


def apply_strategy(df):
    """Chosen strategy: keep NaN (no imputation) and add a missing flag per column."""
    df = df.copy()
    for col in ["Fondi_limit", "Vlera_e_fituesit", "Fituesi"]:
        df[f"{col}_missing"] = df[col].isna()
    return df


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder, columns=KEYS + list(COLUMNS) + CONTEXT)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df = clean(raw)
    df["cancelled"] = po_jo_to_bool(raw["Anulluar"])
    df["procedure_type"] = raw["Lloji_i_procedures"]

    # 1. Identification: real missing values, then disguised ones
    before = missing_summary(df, COLUMNS).rename(
        columns={"missing": "missing_raw", "missing_pct": "missing_raw_pct"})
    df = mark_disguised_missing(df)
    after = missing_summary(df, COLUMNS)
    summary = before.merge(after, on="column")

    # 2. Where do the missing values come from?
    by_year = missing_by_year(df, COLUMNS)
    winner_by_cancel = missing_by_group(df, "Fituesi", "cancelled")
    fund_by_type = missing_by_group(df, "Fondi_limit", "procedure_type").sort_values(
        "missing", ascending=False)
    has_winner = df["Fituesi"].notna()
    value_vs_winner = pd.DataFrame([
        {"case": "Winner present, winner value missing",
         "rows": int((has_winner & df["Vlera_e_fituesit"].isna()).sum())},
        {"case": "Winner missing, winner value present",
         "rows": int((~has_winner & df["Vlera_e_fituesit"].notna()).sum())},
        {"case": "Both missing",
         "rows": int((~has_winner & df["Vlera_e_fituesit"].isna()).sum())},
    ])

    # 3. Strategies compared on the two main amounts
    strategies = pd.concat([
        compare_numeric_strategies(df[col], df["procedure_type"]).assign(column=col)
        for col in ["Fondi_limit", "Vlera_e_fituesit"]
    ])[["column", "strategy", "rows_kept", "still_missing", "median", "mean"]]

    result = apply_strategy(df).drop(columns=["cancelled", "procedure_type"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "missing_summary.csv", index=False)
    by_year.to_csv(OUT_DIR / "missing_by_year.csv")
    winner_by_cancel.to_csv(OUT_DIR / "missing_winner_by_cancellation.csv", index=False)
    fund_by_type.to_csv(OUT_DIR / "missing_fund_by_procedure_type.csv", index=False)
    value_vs_winner.to_csv(OUT_DIR / "missing_value_vs_winner.csv", index=False)
    strategies.to_csv(OUT_DIR / "missing_strategies.csv", index=False)
    result.to_csv(PROCESSED_DIR / "values_winners_missing_handled.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        for title, table in [("Missing values (raw -> with disguised)", summary),
                             ("Missing by year (%)", by_year),
                             ("Winner missing by cancellation", winner_by_cancel),
                             ("Fund missing by procedure type", fund_by_type.head(8)),
                             ("Winner value vs winner", value_vs_winner),
                             ("Strategies", strategies)]:
            print(f"{title}:\n{table.to_string(index=title == 'Missing by year (%)')}\n")


if __name__ == "__main__":
    main()
