"""Integrated dataset (2016-2025): the prepared columns of all three parts in one table.

Every part is prepared from the same raw read by its own code:
- values and winners: cleaning, missing values, features (src.values_winners)
- time and integration: cleaning, missing values, election and COVID features (this package)
- procedure and competition: cleaning, CPV integration, features (src.procedure_competition)

A procedure is identified by its reference number together with the contracting
authority (the reference alone is shared by 7 pairs of procedures). The parts
are joined on the raw values of that key, so later text cleaning cannot break
the join; the joins are checked to be one-to-one and no row may be lost.

Usage (from the repository root):
    python -m src.time_integration.integrated_dataset [csv_folder]

If no folder is given, data/raw/ is used. The dataset is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.procedure_competition.columns import COLUMNS as PROCEDURE_COLUMNS
from src.procedure_competition.prepare import clean_and_engineer
from src.time_integration.columns import COLUMNS as TIME_COLUMNS
from src.time_integration.features import build_features
from src.values_winners import features as values_features
from src.values_winners.cleaning import KEYS
from src.values_winners.columns import COLUMNS as VALUE_COLUMNS

OUT_DIR = Path("reports/time_integration")
PROCESSED_DIR = Path("data/processed")
AUTHORITY = "Autoriteti_kontraktues"
SOURCES = {
    "values_winners": "Marigona Hamiti",
    "time_integration": "Semine Muharremi",
    "procedure_competition": "Tringa Baftiu",
}


def prepare_parts(raw):
    """Each part prepared by its own code, with the raw join key attached."""
    keys = raw[KEYS]
    values = values_features.binarize(values_features.discretize(
        values_features.add_features(values_features.prepare(raw[KEYS + ["year", *VALUE_COLUMNS]]))))
    time = build_features(raw[[c for c in TIME_COLUMNS if c != "viti"] + ["year"]])
    procedure = clean_and_engineer(raw[[*PROCEDURE_COLUMNS, "year"]])

    # The cleaned authority name is kept under its own name; the raw one is the key
    procedure = procedure.rename(columns={AUTHORITY: f"{AUTHORITY}_clean"})
    parts = {
        "values_winners": values.drop(columns=KEYS),
        "time_integration": time.drop(columns=["Numri_i_references"]),
        "procedure_competition": procedure,
    }
    for name, part in parts.items():
        assert part.index.equals(raw.index), f"{name} must keep every raw row in order"
        parts[name] = pd.concat([keys, part], axis=1)
    return parts


def integrate(parts):
    """Join the parts one-to-one on the procedure key; year must agree everywhere."""
    names = list(parts)
    df = parts[names[0]]
    for name in names[1:]:
        df = df.merge(parts[name], on=KEYS, how="outer", validate="one_to_one",
                      suffixes=("", f"__{name}"), indicator=True)
        assert df["_merge"].eq("both").all(), f"rows of {name} without a match"
        assert df["year"].eq(df[f"year__{name}"]).all(), f"year differs in {name}"
        df = df.drop(columns=["_merge", f"year__{name}"])

    # Readable column order: key, year, then each part
    df[AUTHORITY] = df.pop(f"{AUTHORITY}_clean")
    first = ["Numri_i_references", AUTHORITY, "year"]
    return df[first + [c for c in df.columns if c not in first]]


def column_sources(df, parts):
    rows = []
    for col in df.columns:
        if col in ["Numri_i_references", AUTHORITY, "year"]:
            source, owner = "key", "-"
        else:
            source = next(n for n, p in parts.items() if col in p.columns and col not in KEYS)
            owner = SOURCES[source]
        rows.append({"column": col, "source": source, "owner": owner, "dtype": str(df[col].dtype),
                     "non_null": int(df[col].notna().sum()),
                     "missing_pct": round(df[col].isna().mean() * 100, 2)})
    return pd.DataFrame(rows)


def integration_summary(raw, df, columns):
    per_source = columns["source"].value_counts()
    return pd.DataFrame([
        ("Raw rows (10 yearly files)", len(raw)),
        ("Integrated rows", len(df)),
        ("Rows lost or duplicated", len(raw) - len(df)),
        ("Duplicated procedure keys", int(df.duplicated(KEYS).sum())),
        ("Columns", df.shape[1]),
        *[(f"Columns from {name}", int(per_source.get(name, 0))) for name in ["key", *SOURCES]],
        ("Years", f"{df['year'].min()}-{df['year'].max()}"),
    ], columns=["metric", "value"])


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    parts = prepare_parts(raw)
    df = integrate(parts)
    assert len(df) == len(raw), "rows must never be lost or duplicated"

    columns = column_sources(df, parts)
    summary = integration_summary(raw, df, columns)
    by_year = df.groupby("year").size().rename("procedures").reset_index()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "integrated_summary.csv", index=False)
    columns.to_csv(OUT_DIR / "integrated_columns.csv", index=False)
    by_year.to_csv(OUT_DIR / "integrated_rows_by_year.csv", index=False)
    df.to_csv(PROCESSED_DIR / "prokurimi_integruar.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(summary.to_string(index=False))
        print()
        print(columns.to_string(index=False))
    print(f"\nSaved {len(df):,} rows x {df.shape[1]} columns to {PROCESSED_DIR / 'prokurimi_integruar.csv'}")


if __name__ == "__main__":
    main()
