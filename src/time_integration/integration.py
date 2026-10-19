"""Integration of procurement data (2016-2025) with election periods.

Usage (from the repository root):
    python -m src.time_integration.integration [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.time_integration.columns import COLUMNS, DATETIME_COLS
from src.time_integration.elections import ELECTIONS

OUT_DIR = Path("reports/time_integration")


def parse_dates(df):
    """Convert date columns from text to datetime."""
    for col in DATETIME_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
    return df


def add_election_period(df):
    """Add election period classification based on procurement date."""
    df["election_period"] = None
    df["election_year"] = None
    
    for idx, row in df.iterrows():
        date_val = row.get("Data_e_publikimit")
        
        if pd.isna(date_val):
            continue
        
        year = date_val.year
        
        if year in ELECTIONS:
            for start, end in ELECTIONS[year]:
                if start <= date_val <= end:
                    df.loc[idx, "election_period"] = f"{year}_{start.month:02d}"
                    df.loc[idx, "election_year"] = year
                    break
    
    return df


def integration_summary(df):
    """Create integration summary report."""
    summary_data = []
    summary_data.append(["Total procedures", len(df)])
    summary_data.append(["Years covered", f"{int(df['year'].min())}-{int(df['year'].max())}"])
    summary_data.append(["Procedures with Data_e_publikimit", df["Data_e_publikimit"].notna().sum()])
    summary_data.append(["Procedures during elections", df["election_period"].notna().sum()])
    summary_data.append(["Procedures outside elections", df["election_period"].isna().sum()])
    
    return pd.DataFrame(summary_data, columns=["metric", "value"])


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    
    print("Loading procurement data (2016-2025)...")
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = read_years(folder, columns=cols_to_read)
    print("[OK] Loaded " + str(len(df)) + " procedures\n")
    
    print("Parsing dates...")
    df = parse_dates(df)
    print("[OK] Parsed dates\n")
    
    print("Adding election periods...")
    df = add_election_period(df)
    print("[OK] Added election periods\n")
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Creating integration summary...")
    summary = integration_summary(df)
    summary.to_csv(OUT_DIR / "integration_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("[OK] Saved to " + str(OUT_DIR / 'integration_summary.csv') + "\n")
    
    print("Creating elections mapping...")
    elections_data = []
    for year, periods in sorted(ELECTIONS.items()):
        for start, _ in periods:
            count = len(df[df["election_year"] == year])
            elections_data.append([year, start.strftime("%Y-%m-%d"), count])
    
    elections_df = pd.DataFrame(elections_data, columns=["year", "election_date", "procedures_count"])
    elections_df.to_csv(OUT_DIR / "elections_mapping.csv", index=False)
    print(elections_df.to_string(index=False))
    print("[OK] Saved to " + str(OUT_DIR / 'elections_mapping.csv') + "\n")


if __name__ == "__main__":
    main()
