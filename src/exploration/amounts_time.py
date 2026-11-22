"""Phase II, Semine's columns: exploration of the amounts and the time columns.

Univariate (summary statistics):
- mean, median, standard deviation, quartiles, skewness and kurtosis of the
  amount and time columns, next to the robust measures (median, IQR, MAD),
  both on all procedures and without the Phase II errors ("gabim", see
  src.outliers.amounts_time) - the same split src.exploration.competition_winners
  uses for its own columns.

Usage (from the repository root):
    python -m src.exploration.amounts_time [csv_folder]
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.final.final_dataset import build
from src.outliers.amounts_time import (AMOUNT_ERROR_ABOVE, DURATION_ERROR_ABOVE,
                                       SAVINGS_PCT_ERROR_ABOVE, value_fund_scale_error)

OUT_DIR = Path("reports/exploration")

AMOUNT_COLUMNS = ["Fondi_limit", "Vlera_e_fituesit", "Vlera_e_fituesit_ne_lidhjen_e_kontrates",
                  "kursimi", "kursimi_pct"]
TIME_COLUMNS = ["ditet_publikim_hapje", "kohezgjatja_e_tenderit", "ditet_nga_zgjedhjet"]
NUMERIC_COLUMNS = AMOUNT_COLUMNS + TIME_COLUMNS


def known_errors(df):
    """Every row with a known error in this part's amount or time columns.

    Reuses the exact rules of src.outliers.amounts_time (same thresholds, same
    reasoning), instead of a new definition that could silently drift from it.
    """
    amounts = df[["Fondi_limit", "Vlera_e_fituesit", "Vlera_e_fituesit_ne_lidhjen_e_kontrates"]]
    amount_error = (amounts.gt(AMOUNT_ERROR_ABOVE).any(axis=1)
                    | df["Fondi_limit"].le(1) | df["Vlera_e_fituesit"].le(1)
                    | value_fund_scale_error(df))
    time_cols = df[["ditet_publikim_hapje", "kohezgjatja_e_tenderit"]]
    time_error = (time_cols.lt(0) | time_cols.gt(DURATION_ERROR_ABOVE)).any(axis=1)
    savings_error = df["kursimi_pct"].abs().gt(SAVINGS_PCT_ERROR_ABOVE)
    return (amount_error | time_error | savings_error).fillna(False)


def describe(series):
    s = series.dropna().astype("float64")
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    return {"n": len(s), "mean": s.mean(), "std": s.std(), "min": s.min(), "q1": q1,
            "median": s.median(), "q3": q3, "max": s.max(), "iqr": q3 - q1,
            "mad": (s - s.median()).abs().median(), "skewness": s.skew(),
            "kurtosis": s.kurt()}


def summary_statistics(df, errors):
    """Classical and robust statistics, on all rows and without the known errors."""
    rows = []
    for column in NUMERIC_COLUMNS:
        for subset, mask in [("Të gjitha", pd.Series(True, index=df.index)),
                             ("Pa gabimet", ~errors)]:
            rows.append({"column": column, "subset": subset, **describe(df.loc[mask, column])})
    return pd.DataFrame(rows).round(3)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df, _ = build(read_years(folder))
    errors = known_errors(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = summary_statistics(df, errors)
    summary.to_csv(OUT_DIR / "summary_statistics_amounts_time.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_rows", 200):
        print(f"Known errors (amounts/time, this part): {int(errors.sum()):,} of {len(df):,}\n")
        print(f"summary_statistics_amounts_time:\n{summary.to_string(index=False)}\n")


if __name__ == "__main__":
    main()
