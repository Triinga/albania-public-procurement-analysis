"""Type, profile, clean and engineer procedure/competition attributes.

Usage from repository root:
    python -m src.procedure_competition.prepare <folder> [start-year] [end-year]

CSV inputs are read as text to preserve source values. Reports are written to
a year-range subfolder under reports/procedure_competition. Raw data is untouched.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.common.data_loading import FILE_PATTERN, YEARS
from src.common.data_types import describe_types
from src.common.quality import duplicate_rows, has_extra_whitespace, run_checks
from src.procedure_competition.columns import BINARY, COLUMNS, NUMERIC

OUT_DIR = Path("reports/procedure_competition")
CPV_PATTERN = re.compile(r"(?<!\d)(\d{8})(?:-(\d))?")
EXPORT_DATE_PATTERN = re.compile(r"Gjeneruar_me_(\d{8})", re.IGNORECASE)


def _is_blank(series):
    return series.isna() | series.astype("string").str.strip().eq("").fillna(True)


def _cpv_codes(value):
    if pd.isna(value):
        return []
    return list(dict.fromkeys(match.group(1) for match in CPV_PATTERN.finditer(str(value))))


def _export_date(path):
    """Return the generation date encoded in an APP export filename."""
    match = EXPORT_DATE_PATTERN.search(path.stem)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d%m%Y").date()
    except ValueError:
        return None


def _select_year_file(folder, year):
    """Select one yearly APP export, preferring the newest dated export."""
    candidates = [p for p in folder.glob(FILE_PATTERN.format(year=year)) if "(" not in p.name]
    if not candidates:
        raise FileNotFoundError(f"No source file found for {year} in {folder}")
    if len(candidates) == 1:
        return candidates[0]

    dated = [(_export_date(path), path) for path in candidates]
    dated = [(date, path) for date, path in dated if date is not None]
    if not dated:
        raise FileNotFoundError(
            f"Found {len(candidates)} source files for {year} in {folder}, but none has a generation date"
        )
    newest_date = max(date for date, _ in dated)
    newest = [path for date, path in dated if date == newest_date]
    if len(newest) != 1:
        raise FileNotFoundError(
            f"Expected one newest source file for {year} in {folder}; found {len(newest)} dated {newest_date}"
        )
    return newest[0]


def quality_report(df, cleaned=False):
    """Return row-level quality counts without removing source rows."""
    all_rows = pd.Series(True, index=df.index)
    checks = []
    for col in COLUMNS:
        present = ~_is_blank(df[col])
        checks.append(("Completeness", col, "Missing or blank value", ~present, all_rows))
    checks += [
        ("Uniqueness", "Procedure/competition fields", "Rows identical across these 11 fields",
         duplicate_rows(df, list(COLUMNS)), all_rows),
    ]
    for col in ["Autoriteti_kontraktues", "Objekti_i_prokurimit", "Lloji_i_procedures",
                "Tipi_i_kontrates", "Lloji_i_marreveshjes_kuader", "Arsyeja_e_anullimit", "Kodet_CPV"]:
        s = df[col].astype("string")
        present = ~_is_blank(s)
        checks.append(("Format", col, "Leading/trailing or repeated whitespace",
                       present & has_extra_whitespace(s), present))
    for col in BINARY:
        present = ~_is_blank(df[col])
        if cleaned:
            invalid = present & ~df[col].isin([True, False])
            description = "Value outside boolean vocabulary"
        else:
            s = df[col].astype("string").str.strip().str.casefold()
            invalid = present & ~s.isin(["po", "jo"])
            description = "Value outside Po/Jo vocabulary"
        checks.append(("Format", col, description, invalid, present))
    for col in NUMERIC:
        n = pd.to_numeric(df[col].astype("string").str.strip(), errors="coerce")
        present = ~_is_blank(df[col])
        checks += [
            ("Format", col, "Non-numeric value", present & n.isna(), present),
            ("Accuracy", col, "Negative offer count", n.lt(0).fillna(False), n.notna()),
        ]
    submitted = pd.to_numeric(df["Numri_i_ofertave_te_dorezuara"], errors="coerce")
    qualified = pd.to_numeric(df["Numri_i_ofertave_te_kualifikuara"], errors="coerce")
    both = submitted.notna() & qualified.notna()
    checks.append(("Consistency", "Numri_i_ofertave_te_kualifikuara",
                   "Qualified offers exceed submitted offers", both & qualified.gt(submitted), both))
    if cleaned:
        cancelled = df["Anulluar"].eq(True).fillna(False)
    else:
        cancelled = df["Anulluar"].astype("string").str.strip().str.casefold().eq("po")
    reason_missing = _is_blank(df["Arsyeja_e_anullimit"])
    checks += [
        ("Consistency", "Arsyeja_e_anullimit",
         "Cancellation reason present when procedure is not marked cancelled",
         ~reason_missing & ~cancelled, ~reason_missing),
        ("Completeness", "Arsyeja_e_anullimit",
         "Cancellation reason missing when procedure is marked cancelled",
         reason_missing & cancelled, cancelled),
    ]
    cpv_present = ~_is_blank(df["Kodet_CPV"])
    cpv_count = df["Kodet_CPV"].map(lambda x: len(_cpv_codes(x)))
    checks += [
        ("Format", "Kodet_CPV", "Non-empty cell contains no 8-digit CPV code",
         cpv_present & cpv_count.eq(0), cpv_present),
        ("Format", "Kodet_CPV", "More than one CPV code in cell",
         cpv_count.gt(1), cpv_present),
    ]
    return run_checks(df, checks)


def missing_value_report(before, after):
    """Summarize missing values before and after cleaning and record their treatment."""
    treatments = {
        "Lloji_i_marreveshjes_kuader": "Retained as missing; no reliable source value to impute",
        "Arsyeja_e_anullimit": "Retained as missing; only applicable to cancelled procedures",
        "Kodet_CPV": "Whitespace normalized; missing values retained",
    }
    rows = []
    for col in COLUMNS:
        before_missing = int(_is_blank(before[col]).sum())
        after_missing = int(_is_blank(after[col]).sum())
        if col in NUMERIC:
            treatment = "Converted to nullable integer; missing values retained"
        elif col in BINARY:
            treatment = "Mapped Po/Jo to boolean; invalid or blank values retained as missing"
        else:
            treatment = treatments.get(
                col, "Whitespace normalized; blank values retained as missing"
            )
        rows.append({
            "column": col,
            "missing_before": before_missing,
            "pct_before": round(before_missing * 100 / len(before), 2) if len(before) else 0.0,
            "missing_after": after_missing,
            "pct_after": round(after_missing * 100 / len(after), 2) if len(after) else 0.0,
            "treatment": treatment,
        })
    return pd.DataFrame(rows)


def category_profile(df):
    rows = []
    for col in ["Lloji_i_procedures", "Tipi_i_kontrates", "Lloji_i_marreveshjes_kuader", "Anulluar", "Pezulluar"]:
        vals = df[col].astype("string").str.strip().replace("", pd.NA).fillna("[MUNGON]")
        for value, count in vals.value_counts(dropna=False).items():
            rows.append({"column": col, "value": value, "rows": int(count),
                         "pct": round(float(count) * 100 / len(df), 3) if len(df) else 0})
    return pd.DataFrame(rows)


def clean_and_engineer(df):
    """Normalize whitespace/types and add documented analysis features."""
    out = df.copy()
    for col in [c for c in COLUMNS if c not in NUMERIC]:
        out[col] = out[col].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
        out[col] = out[col].replace("", pd.NA)
    for col in NUMERIC:
        out[col] = pd.to_numeric(out[col].astype("string").str.strip(), errors="coerce").astype("Int64")
    for col in BINARY:
        out[col] = out[col].str.casefold().map({"po": True, "jo": False}).astype("boolean")

    codes = out["Kodet_CPV"].map(_cpv_codes)
    out["cpv_count"] = codes.map(len).astype("Int64")
    out["primary_cpv_code"] = codes.map(lambda items: items[0] if items else pd.NA).astype("string")
    # CPV divisions use the first two digits. Keep as text so leading zeroes survive.
    out["primary_cpv_division"] = out["primary_cpv_code"].str[:2]
    out["offers_missing"] = out["Numri_i_ofertave_te_dorezuara"].isna().astype("boolean")
    out["no_submitted_offers"] = out["Numri_i_ofertave_te_dorezuara"].eq(0).fillna(False).astype("boolean")
    out["qualified_offer_share"] = (
        out["Numri_i_ofertave_te_kualifikuara"] /
        out["Numri_i_ofertave_te_dorezuara"].where(out["Numri_i_ofertave_te_dorezuara"].gt(0))
    )
    # Preserve original reason but add a usable indicator. Missing stays missing.
    out["has_cancellation_reason"] = out["Arsyeja_e_anullimit"].notna().astype("boolean")
    out["cancelled_without_reason"] = (
        out["Anulluar"].eq(True) & out["Arsyeja_e_anullimit"].isna()
    ).fillna(False).astype("boolean")
    return out


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    start_year = int(sys.argv[2]) if len(sys.argv) > 2 else YEARS.start
    end_year = int(sys.argv[3]) if len(sys.argv) > 3 else YEARS.stop - 1
    if start_year > end_year or start_year < YEARS.start or end_year >= YEARS.stop:
        raise ValueError(f"Choose a year range inside {YEARS.start}-{YEARS.stop - 1}")
    years = list(range(start_year, end_year + 1))
    out_dir = OUT_DIR / f"{start_year}_{end_year}"
    parts = []
    for year in years:
        source_file = _select_year_file(folder, year)
        part = pd.read_csv(source_file, dtype=str, usecols=list(COLUMNS))
        part["year"] = year
        parts.append(part)
    # Load every source field as text and append the source year, with no row sampling.
    df = pd.concat(parts, ignore_index=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    describe_types(df, COLUMNS).to_csv(out_dir / "data_types.csv", index=False)
    quality_report(df).to_csv(out_dir / "quality_checks.csv", index=False)
    category_profile(df).to_csv(out_dir / "category_profile.csv", index=False)
    clean = clean_and_engineer(df)
    quality_report(clean, cleaned=True).to_csv(out_dir / "quality_after.csv", index=False)
    missing_value_report(df, clean).to_csv(out_dir / "missing_values.csv", index=False)

    yearly = df.groupby("year", dropna=False).size().rename("procedures").reset_index()
    yearly.to_csv(out_dir / "yearly_row_counts.csv", index=False)
    summary = pd.DataFrame([
        {"metric": "source_years", "value": f"{min(years)}-{max(years)}"},
        {"metric": "input_rows", "value": len(df)},
        {"metric": "output_rows", "value": len(clean)},
        {"metric": "rows_removed", "value": len(df) - len(clean)},
        {"metric": "rows_with_CPV_code", "value": int(clean["cpv_count"].gt(0).sum())},
        {"metric": "rows_with_multiple_CPV_codes", "value": int(clean["cpv_count"].gt(1).sum())},
        {"metric": "cancelled_without_reason", "value": int(clean["cancelled_without_reason"].sum())},
    ])
    summary.to_csv(out_dir / "preparation_summary.csv", index=False)
    # Clean rows are emitted separately for downstream integration; raw data remains untouched.
    clean.to_csv(out_dir / "procedure_competition_clean.csv", index=False)
    print(summary.to_string(index=False))
    print(f"Reports and cleaned extract written to {out_dir}")


if __name__ == "__main__":
    main()
