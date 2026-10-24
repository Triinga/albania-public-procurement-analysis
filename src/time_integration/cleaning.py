"""Cleaning of the time columns (2016-2025): fix logically impossible dates.

The reference number holds the date the procedure was registered
(REF-xxxxx-MM-DD-YYYY), which is never after the publication date. It is used
to decide which of two conflicting dates is the wrong one:

- Opening before publication, but not before registration: the publication
  was recorded late, so the publication date is moved back to the opening date.
- Opening before registration or after closing: the opening date is wrong.
- Closing before registration or after the export date: the closing date is
  wrong (month/year typos, often shared with the opening date).

Wrong dates are set to missing and then filled like the other missing dates
(see missing_values). No row is dropped; every change is flagged.

Usage (from the repository root):
    python -m src.time_integration.cleaning [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.time_integration.columns import COLUMNS
from src.time_integration.missing_values import CLOSE, OPEN, PUB, fill_missing_dates, parse_dates

OUT_DIR = Path("reports/time_integration")
REFERENCE = "Numri_i_references"
EXPORT_DATE = pd.Timestamp(2026, 10, 19)  # "Gjeneruar_me_19102026" in the file names


def reference_date(df):
    """Registration date stored at the end of the reference number."""
    return pd.to_datetime(df[REFERENCE].str[-10:], format="%m-%d-%Y", errors="coerce")


def clean(df):
    """Fix the impossible date orders; wrong dates become missing."""
    df = df.copy()
    registered = reference_date(df)

    late_publication = (df[OPEN] < df[PUB]) & (df[OPEN] >= registered)
    wrong_open = (df[OPEN] < registered) | (df[OPEN] > df[CLOSE])
    wrong_close = (df[CLOSE] < registered) | (df[CLOSE] > EXPORT_DATE)

    df[f"{PUB}_corrected"] = late_publication
    df[f"{OPEN}_invalid"] = wrong_open
    df[f"{CLOSE}_invalid"] = wrong_close

    df.loc[late_publication, PUB] = df.loc[late_publication, OPEN]
    df.loc[wrong_open, OPEN] = pd.NaT
    df.loc[wrong_close, CLOSE] = pd.NaT
    return df


def date_order_checks(df):
    """Rows breaking each date rule."""
    registered = reference_date(df)
    return {
        "Publication before registration": int((df[PUB] < registered).sum()),
        "Opening before publication": int((df[OPEN] < df[PUB]).sum()),
        "Closing before opening": int((df[CLOSE] < df[OPEN]).sum()),
        "Closing before publication": int((df[CLOSE] < df[PUB]).sum()),
        "Closing after export date": int((df[CLOSE] > EXPORT_DATE).sum()),
        "Tender duration > 365 days": int(((df[CLOSE] - df[OPEN]).dt.days > 365).sum()),
    }


def cleaning_summary(df):
    rows = [
        (PUB, "Opening before publication, after registration",
         "Publication date moved back to the opening date", f"{PUB}_corrected"),
        (OPEN, "Opening before registration or after closing",
         "Set to missing, then filled (publication + median delay)", f"{OPEN}_invalid"),
        (CLOSE, "Closing before registration or after the export date (19.10.2026)",
         "Set to missing, then filled (opening + median duration)", f"{CLOSE}_invalid"),
    ]
    return pd.DataFrame([
        {"column": col, "problem": problem, "action": action, "rows": int(df[flag].sum())}
        for col, problem, action, flag in rows
    ])


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = parse_dates(read_years(folder, columns=cols_to_read))
    rows_before = len(df)

    before = date_order_checks(fill_missing_dates(df.copy()))
    df = fill_missing_dates(clean(df))
    assert len(df) == rows_before, "rows must never be dropped"
    after = date_order_checks(df)

    summary = cleaning_summary(df)
    checks = pd.DataFrame({"check": list(before), "before": list(before.values()),
                           "after": list(after.values())})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "cleaning_summary.csv", index=False)
    checks.to_csv(OUT_DIR / "date_order_checks.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_colwidth", 70):
        print(summary.to_string(index=False))
        print()
        print(checks.to_string(index=False))
    print(f"\nRows: {rows_before:,} -> {len(df):,} (none dropped)")


if __name__ == "__main__":
    main()
