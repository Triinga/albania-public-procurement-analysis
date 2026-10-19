"""Data quality of the value and winner columns (2016-2025).

Only identifies and documents problems (Part I); treating them belongs to
cleaning and Part II. All 21 columns are read for the duplicate checks;
`Anulluar` (procedure and competition columns) is used only for the
cross-check "cancelled procedure with a winner".

Usage (from the repository root):
    python -m src.values_winners.quality [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years, to_number
from src.common.quality import (ALBANIAN_NIPT, APP_AMOUNT, duplicate_rows,
                                has_extra_whitespace, has_multiple_entries, normalize_name,
                                run_checks, shared_key)
from src.values_winners.columns import COLUMNS, NUMERIC

OUT_DIR = Path("reports/values_winners")
REFERENCE = "Numri_i_references"


def build_checks(df):
    fund = to_number(df["Fondi_limit"])
    winner_value = to_number(df["Vlera_e_fituesit"])
    contract_value = to_number(df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"])
    winner, nipt = df["Fituesi"], df["NIPT_i_fituesit"]
    cancelled = df["Anulluar"].eq("Po")
    nipt_clean = nipt.str.strip()
    single_nipt = nipt.notna() & ~nipt_clean.str.contains("\n", regex=False, na=False)
    all_rows = pd.Series(True, index=df.index)

    source_columns = [c for c in df.columns if c != "year"]
    same_reference = shared_key(df, REFERENCE)

    checks = []

    # Uniqueness (duplicates)
    checks += [
        ("Uniqueness", "All columns", "Exact duplicate row (all 21 columns)",
         duplicate_rows(df, source_columns), all_rows),
        ("Uniqueness", REFERENCE, "Reference number used by more than one procedure",
         same_reference, df[REFERENCE].notna()),
        ("Uniqueness", "Fituesi", "Same reference, different winner",
         same_reference & df.groupby(REFERENCE)["Fituesi"].transform("nunique").gt(1),
         same_reference),
    ]

    # Completeness
    for col in COLUMNS:
        checks.append(("Completeness", col, "Missing value", df[col].isna(), all_rows))

    # Format (interpretability)
    for col in NUMERIC:
        s = df[col]
        checks.append(("Format", col, "Amount not in APP format 1,234.56",
                       s.notna() & ~s.str.fullmatch(APP_AMOUNT, na=False), s.notna()))
    checks += [
        ("Format", "NIPT_i_fituesit", "Extra whitespace or newlines",
         has_extra_whitespace(nipt), nipt.notna()),
        ("Format", "Fituesi", "Extra whitespace or newlines",
         has_extra_whitespace(winner), winner.notna()),
        ("Format", "NIPT_i_fituesit", "Several NIPTs in one cell (joint winners)",
         has_multiple_entries(nipt), nipt.notna()),
        ("Format", "Fituesi", "Several winners in one cell (joint winners)",
         has_multiple_entries(winner), winner.notna()),
        ("Format", "NIPT_i_fituesit", "Single NIPT not in Albanian format (after trimming)",
         single_nipt & ~nipt_clean.str.fullmatch(ALBANIAN_NIPT, na=False), single_nipt),
    ]

    # Accuracy (logically impossible values)
    for col, values in [("Fondi_limit", fund), ("Vlera_e_fituesit", winner_value),
                        ("Vlera_e_fituesit_ne_lidhjen_e_kontrates", contract_value)]:
        present = values.notna()
        checks += [
            ("Accuracy", col, "Value is 0", values.eq(0), present),
            ("Accuracy", col, "Value between 0 and 1 lek", values.gt(0) & values.le(1), present),
        ]
    has_fund = fund.gt(0) & winner_value.notna()
    checks += [
        ("Accuracy", "Vlera_e_fituesit", "Winner value above fund limit",
         has_fund & winner_value.gt(fund), has_fund),
        ("Accuracy", "Fondi_limit", "Fund is 0 but a winner value exists",
         fund.eq(0) & winner_value.gt(0), fund.eq(0)),
    ]

    # Consistency
    both_values = winner_value.notna() & contract_value.notna()
    checks += [
        ("Consistency", "Fituesi", "Cancelled procedure with a winner",
         cancelled & winner.notna(), cancelled),
        ("Consistency", "Vlera_e_fituesit", "Cancelled procedure with a winner value",
         cancelled & winner_value.notna(), cancelled),
        ("Consistency", "NIPT_i_fituesit", "NIPT without winner name",
         nipt.notna() & winner.isna(), nipt.notna()),
        ("Consistency", "Vlera_e_fituesit_ne_lidhjen_e_kontrates",
         "Contract value differs from winner value",
         both_values & (contract_value - winner_value).abs().gt(1), both_values),
    ]
    return checks


def shared_references(df):
    """Procedures that share a reference number, with their value and winner columns."""
    cols = [REFERENCE, "year", "Autoriteti_kontraktues", *COLUMNS]
    return df.loc[shared_key(df, REFERENCE), cols].sort_values([REFERENCE, "year"])


def invalid_nipts(df):
    """Single NIPTs that are not in Albanian format, most frequent first."""
    nipt = df["NIPT_i_fituesit"].str.strip()
    single = nipt.notna() & ~nipt.str.contains("\n", regex=False, na=False)
    bad = df[single & ~nipt.str.fullmatch(ALBANIAN_NIPT, na=False)]
    return (bad.assign(NIPT=nipt[bad.index], winner=bad["Fituesi"].str.strip())
            .groupby("NIPT").agg(rows=("winner", "size"), winner=("winner", "first"))
            .sort_values("rows", ascending=False).reset_index())


def winner_inconsistencies(df):
    """Winner names that appear with several NIPTs or are spelled in several ways."""
    w = df.dropna(subset=["Fituesi", "NIPT_i_fituesit"])
    name, nipt = w["Fituesi"].str.strip(), w["NIPT_i_fituesit"].str.strip()

    per_name = pd.DataFrame({"name": name, "nipt": nipt}).groupby("name")["nipt"]
    multi_nipt = per_name.nunique()
    multi_nipt = pd.DataFrame({
        "issue": "Same name, several NIPTs",
        "key": multi_nipt[multi_nipt > 1].index,
        "variants": [" | ".join(sorted(per_name.get_group(n).unique()))
                     for n in multi_nipt[multi_nipt > 1].index],
    })

    raw = w["Fituesi"]
    per_nipt = pd.DataFrame({"nipt": nipt, "name": raw}).groupby("nipt")["name"]
    spellings = per_nipt.nunique()
    spellings = spellings[spellings > 1]
    spelled = pd.DataFrame({
        "issue": "Same NIPT, name written differently",
        "key": spellings.index,
        "variants": [" | ".join(repr(v) for v in per_nipt.get_group(n).unique())
                     for n in spellings.index],
    })
    return pd.concat([multi_nipt, spelled], ignore_index=True)


def name_summary(df):
    """How many distinct winner names remain after trimming and normalizing."""
    names = df["Fituesi"].dropna()
    return pd.DataFrame([
        {"step": "Raw names", "unique_names": names.nunique()},
        {"step": "After trimming whitespace", "unique_names": names.str.strip().nunique()},
        {"step": "After normalizing (upper case, no punctuation)",
         "unique_names": normalize_name(names).nunique()},
    ])


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df = read_years(folder)  # all columns, needed for the duplicate checks
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(df):,} procedures\n")

    checks = run_checks(df, build_checks(df))
    references = shared_references(df)
    nipts = invalid_nipts(df)
    winners = winner_inconsistencies(df)
    names = name_summary(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks.to_csv(OUT_DIR / "quality_checks.csv", index=False)
    references.to_csv(OUT_DIR / "shared_references.csv", index=False)
    nipts.to_csv(OUT_DIR / "invalid_nipt.csv", index=False)
    winners.to_csv(OUT_DIR / "winner_inconsistencies.csv", index=False)
    names.to_csv(OUT_DIR / "winner_names.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20,
                           "display.max_colwidth", 70):
        print(checks.to_string(index=False))
        print(f"\nReference numbers used by more than one procedure: {references[REFERENCE].nunique()}")
        print(f"\nSingle NIPTs not in Albanian format: {len(nipts)} distinct")
        print(nipts.head(10).to_string(index=False))
        print("\nWinner inconsistencies:")
        print(winners["issue"].value_counts().to_string())
        print()
        print(names.to_string(index=False))


if __name__ == "__main__":
    main()
