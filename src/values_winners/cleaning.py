"""Cleaning of the value and winner columns (2016-2025).

Fixes the format and consistency problems found in the quality assessment:
amounts stored as text, Po/Jo answers, whitespace and newlines in winner
names and NIPTs, and the same NIPT written with different names.
Logically impossible values (e.g. winner value above the fund) are NOT
changed here: they belong to Part II.

Usage (from the repository root):
    python -m src.values_winners.cleaning [csv_folder]

If no folder is given, data/raw/ is used. The cleaned columns are saved to
data/processed/ (not tracked by git); the summary goes to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.cleaning import canonical_by_key, clean_text, po_jo_to_bool
from src.common.data_loading import DATA_DIR, YEARS, read_years, to_number
from src.values_winners.columns import COLUMNS, NUMERIC

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
KEYS = ["Numri_i_references", "Autoriteti_kontraktues"]  # identify a procedure


def clean(raw):
    """Return the cleaned value and winner columns (plus keys and year)."""
    df = raw[KEYS + ["year"]].copy()

    for col in NUMERIC:
        df[col] = to_number(raw[col])

    df["Lidhja_e_kontrates_me_TVSH"] = po_jo_to_bool(raw["Lidhja_e_kontrates_me_TVSH"])

    df["NIPT_i_fituesit"] = clean_text(raw["NIPT_i_fituesit"]).str.upper()
    names = clean_text(raw["Fituesi"]).str.upper()
    df["Fituesi"] = canonical_by_key(names, df["NIPT_i_fituesit"])
    return df[KEYS + ["year", *COLUMNS]]


def cleaning_summary(raw, clean_df):
    """Before/after view of each cleaning step."""
    rows = []
    for col in NUMERIC:
        rows.append({
            "column": col, "step": "Text amount -> number",
            "before": f"text ({raw[col].notna().sum():,} values)",
            "after": f"{clean_df[col].dtype} ({clean_df[col].notna().sum():,} values)",
        })
    tvsh = "Lidhja_e_kontrates_me_TVSH"
    rows.append({
        "column": tvsh, "step": "Po/Jo -> boolean",
        "before": str(raw[tvsh].value_counts().to_dict()),
        "after": str({str(k): v for k, v in clean_df[tvsh].value_counts().items()}),
    })
    for col in ["NIPT_i_fituesit", "Fituesi"]:
        rows.append({
            "column": col, "step": "Trim whitespace/newlines, upper case"
                                   + (", one name per NIPT" if col == "Fituesi" else ""),
            "before": f"{raw[col].nunique():,} distinct",
            "after": f"{clean_df[col].nunique():,} distinct",
        })
    return pd.DataFrame(rows)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder, columns=KEYS + list(COLUMNS))
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df = clean(raw)
    summary = cleaning_summary(raw, df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "cleaning_summary.csv", index=False)
    df.to_csv(PROCESSED_DIR / "values_winners_clean.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_colwidth", 80):
        print(summary.to_string(index=False))
    print(f"\nSaved {len(df):,} rows to {PROCESSED_DIR / 'values_winners_clean.csv'}")


if __name__ == "__main__":
    main()
