"""Missing values of the time columns (2016-2025): impute, never drop rows.

Missing opening dates are filled with the publication date plus the typical
publication -> opening delay of that year; missing closing dates with the
opening date plus the typical opening -> closing duration of that year.
Only valid (non-negative) gaps are used to compute the typical values, so an
imputed date can never fall before the date it is derived from. Every imputed
value is flagged in a separate boolean column.

Usage (from the repository root):
    python -m src.time_integration.missing_values [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.common.missing import missing_by_year, missing_summary
from src.time_integration.columns import COLUMNS, DATETIME_COLS

OUT_DIR = Path("reports/time_integration")
PUB, OPEN, CLOSE = "Data_e_publikimit", "Data_e_hapjes", "Data_e_mbylljes"
TIME_COLS = [PUB, OPEN, CLOSE, "Numri_i_references"]


def parse_dates(df):
    """Convert date columns from text to datetime."""
    for col in DATETIME_COLS:
        df[col] = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
    return df


def median_gap_by_year(start, end, years):
    """Median gap in days between two dates per year, using only gaps >= 0.

    Years without any valid gap fall back to the overall median.
    """
    gap = (end - start).dt.days
    gap = gap.where(gap >= 0)
    by_year = gap.groupby(years).median()
    return years.map(by_year).fillna(gap.median()).round()


def fill_missing_dates(df):
    """Fill missing opening/closing dates and flag every imputed value."""
    df[f"{OPEN}_imputed"] = df[OPEN].isna()
    df[f"{CLOSE}_imputed"] = df[CLOSE].isna()

    open_gap = median_gap_by_year(df[PUB], df[OPEN], df["year"])
    df[OPEN] = df[OPEN].fillna(df[PUB] + pd.to_timedelta(open_gap, unit="D"))
    # A filled opening date can never fall after a known closing date
    too_late = df[f"{OPEN}_imputed"] & (df[OPEN] > df[CLOSE])
    df.loc[too_late, OPEN] = df.loc[too_late, CLOSE]

    # The duration is learned only from real opening dates, then applied to the filled one
    real_open = df[OPEN].where(~df[f"{OPEN}_imputed"])
    close_gap = median_gap_by_year(real_open, df[CLOSE], df["year"])
    df[CLOSE] = df[CLOSE].fillna(df[OPEN] + pd.to_timedelta(close_gap, unit="D"))
    return df


def imputation_report(df, before):
    """Before/after missing counts and the number of imputed values per column."""
    after = missing_summary(df, TIME_COLS)
    report = before.merge(after, on="column", suffixes=("_before", "_after"))
    report["imputed"] = report["column"].map({
        OPEN: int(df[f"{OPEN}_imputed"].sum()),
        CLOSE: int(df[f"{CLOSE}_imputed"].sum()),
    }).fillna(0).astype(int)
    return report


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = parse_dates(read_years(folder, columns=cols_to_read))
    rows_before = len(df)

    before = missing_summary(df, TIME_COLS)
    by_year = missing_by_year(df, [OPEN, CLOSE])

    df = fill_missing_dates(df)
    assert len(df) == rows_before, "rows must never be dropped"

    report = imputation_report(df, before)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUT_DIR / "missing_summary.csv", index=False)
    by_year.to_csv(OUT_DIR / "missing_by_year.csv")

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(report.to_string(index=False))
        print()
        print(by_year.to_string())
    print(f"\nRows: {rows_before:,} -> {len(df):,} (none dropped)")
    print(f"Opening before publication after fill: {(df[OPEN] < df[PUB]).sum():,} "
          "(pre-existing logical issue, fixed in cleaning)")
    print(f"Closing before opening among imputed: "
          f"{((df[CLOSE] < df[OPEN]) & df[f'{CLOSE}_imputed']).sum():,}")


if __name__ == "__main__":
    main()
