"""Data quality of the time and integration columns (2016-2025).

Only identifies and documents problems (Part I); treating them belongs to
cleaning and Part II.

Usage (from the repository root):
    python -m src.time_integration.quality [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.quality import has_extra_whitespace, run_checks
from src.time_integration.cleaning import reference_date
from src.time_integration.columns import COLUMNS, DATETIME_COLS

OUT_DIR = Path("reports/time_integration")
REFERENCE = "Numri_i_references"


def parse_dates_safe(series):
    """Try to parse dates; return datetime or NaT if fails."""
    return pd.to_datetime(series, format="%d.%m.%Y", errors="coerce")


def is_valid_date_format(series):
    """Check if date string matches DD.MM.YYYY format before parsing."""
    pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    return series.fillna("").str.match(pattern)


def build_checks(df):
    """Build all quality checks for time columns."""
    all_rows = pd.Series(True, index=df.index)
    
    # Parse dates safely
    pub_date = parse_dates_safe(df["Data_e_publikimit"])
    open_date = parse_dates_safe(df["Data_e_hapjes"])
    close_date = parse_dates_safe(df["Data_e_mbylljes"])
    
    checks = []
    
    # ========== COMPLETENESS: Missing values ==========
    checks += [
        ("Completeness", "Data_e_publikimit", "Missing value",
         df["Data_e_publikimit"].isna(), all_rows),
        ("Completeness", "Data_e_hapjes", "Missing value",
         df["Data_e_hapjes"].isna(), all_rows),
        ("Completeness", "Data_e_mbylljes", "Missing value",
         df["Data_e_mbylljes"].isna(), all_rows),
        ("Completeness", "Numri_i_references", "Missing value",
         df["Numri_i_references"].isna(), all_rows),
    ]
    
    # ========== FORMAT: Date format and whitespace ==========
    pub_str = df["Data_e_publikimit"].fillna("")
    open_str = df["Data_e_hapjes"].fillna("")
    close_str = df["Data_e_mbylljes"].fillna("")
    
    checks += [
        ("Format", "Data_e_publikimit", "Invalid date format (not DD.MM.YYYY)",
         df["Data_e_publikimit"].notna() & ~is_valid_date_format(df["Data_e_publikimit"]),
         df["Data_e_publikimit"].notna()),
        ("Format", "Data_e_hapjes", "Invalid date format (not DD.MM.YYYY)",
         df["Data_e_hapjes"].notna() & ~is_valid_date_format(df["Data_e_hapjes"]),
         df["Data_e_hapjes"].notna()),
        ("Format", "Data_e_mbylljes", "Invalid date format (not DD.MM.YYYY)",
         df["Data_e_mbylljes"].notna() & ~is_valid_date_format(df["Data_e_mbylljes"]),
         df["Data_e_mbylljes"].notna()),
        ("Format", "Data_e_publikimit", "Extra whitespace",
         has_extra_whitespace(df["Data_e_publikimit"]), df["Data_e_publikimit"].notna()),
        ("Format", "Data_e_hapjes", "Extra whitespace",
         has_extra_whitespace(df["Data_e_hapjes"]), df["Data_e_hapjes"].notna()),
        ("Format", "Data_e_mbylljes", "Extra whitespace",
         has_extra_whitespace(df["Data_e_mbylljes"]), df["Data_e_mbylljes"].notna()),
    ]
    
    # ========== ACCURACY: Logical impossibilities ==========
    today = pd.Timestamp(datetime.now().date())
    
    # Both dates present for comparison
    pub_open = pub_date.notna() & open_date.notna()
    open_close = open_date.notna() & close_date.notna()
    pub_close = pub_date.notna() & close_date.notna()
    
    checks += [
        ("Accuracy", "Data_e_hapjes", "Opening date before publication date",
         pub_open & (open_date < pub_date), pub_open),
        ("Accuracy", "Data_e_mbylljes", "Closing date before opening date",
         open_close & (close_date < open_date), open_close),
        ("Accuracy", "Data_e_mbylljes", "Closing date before publication date",
         pub_close & (close_date < pub_date), pub_close),
        ("Accuracy", "Data_e_publikimit", "Publication date in the future",
         pub_date.notna() & (pub_date > today), pub_date.notna()),
        ("Accuracy", "Data_e_hapjes", "Opening date in the future",
         open_date.notna() & (open_date > today), open_date.notna()),
        ("Accuracy", "Data_e_mbylljes", "Closing date in the far future (> 2030)",
         close_date.notna() & (close_date.dt.year > 2030), close_date.notna()),
        ("Accuracy", "Data_e_mbylljes", "Same day opening and closing",
         open_close & (close_date.dt.date == open_date.dt.date),
         open_close),
    ]

    # ========== CONSISTENCY: publication year vs. the yearly file ==========
    pub_year = pub_date.dt.year
    registered = reference_date(df)
    checks += [
        ("Consistency", "Data_e_publikimit", "Published in a later year than the file",
         pub_date.notna() & (pub_year > df["year"]), pub_date.notna()),
        ("Consistency", "Data_e_publikimit", "Published later than February of the next year",
         late_publication(df, pub_date), pub_date.notna()),
        ("Consistency", "Data_e_publikimit", "Published 2+ years after the file year",
         pub_date.notna() & (pub_year >= df["year"] + 2), pub_date.notna()),
        ("Consistency", "Numri_i_references", "Registration year differs from the file year",
         registered.notna() & (registered.dt.year != df["year"]), registered.notna()),
    ]

    return run_checks(df, checks)


def late_publication(df, pub_date):
    """Published in a later year than the file, beyond the usual January-February spill-over."""
    next_year_start = (pub_date.dt.year == df["year"] + 1) & (pub_date.dt.month <= 2)
    return pub_date.notna() & (pub_date.dt.year > df["year"]) & ~next_year_start


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    
    print("Loading procurement data (2016-2025)...")
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = read_years(folder, columns=cols_to_read)
    print(f"[OK] Loaded {len(df):,} procedures\n")
    
    print("Running quality checks...")
    quality = build_checks(df)
    
    pub_date = parse_dates_safe(df["Data_e_publikimit"])
    late = df[late_publication(df, pub_date)][["Numri_i_references", "Data_e_publikimit", "year"]]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    quality.to_csv(OUT_DIR / "quality_checks.csv", index=False)
    late.to_csv(OUT_DIR / "late_publications.csv", index=False)
    
    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 80):
        print(quality.to_string(index=False))
        print(f"\nPublished later than February of the next year: {len(late)}")
        print(late.to_string(index=False))
    
    print(f"\n[OK] Saved to {OUT_DIR / 'quality_checks.csv'}\n")


if __name__ == "__main__":
    main()
