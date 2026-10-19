"""Generic data quality helpers, reusable for any group of columns.

Quality checks only identify and count problems; nothing is changed or removed here.
"""
import pandas as pd

ALBANIAN_NIPT = r"[A-Z]\d{8}[A-Z]"  # e.g. K31528061N
APP_AMOUNT = r"\d{1,3}(,\d{3})*\.\d{2}"  # e.g. 741,600.00


def duplicate_rows(df, columns):
    """Extra copies of rows that are identical in all the given columns."""
    return df.duplicated(subset=list(columns), keep="first")


def shared_key(df, key):
    """Rows whose `key` value appears more than once (all copies are marked)."""
    return df[key].notna() & df.duplicated(subset=[key], keep=False)


def has_extra_whitespace(series):
    """Text with leading/trailing whitespace (incl. newlines) or double spaces."""
    s = series.dropna()
    return (s != s.str.strip()) | s.str.contains("  ", regex=False)


def has_multiple_entries(series):
    """Cells holding several values separated by newlines (e.g. joint winners)."""
    return series.dropna().str.strip().str.contains("\n", regex=False)


def normalize_name(series):
    """Name in a comparable form: upper case, no punctuation, single spaces."""
    return (series.str.upper()
            .str.replace(r"[^\w ]", " ", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip())


def run_checks(df, checks):
    """Count the rows matching each check.

    `checks` is a list of (dimension, column, description, mask, base) where
    `mask` marks the problematic rows and `base` the rows the check applies to.
    """
    rows = []
    for dimension, column, description, mask, base in checks:
        mask = mask.reindex(df.index, fill_value=False)
        base = base.reindex(df.index, fill_value=False)
        n, b = int(mask.sum()), int(base.sum())
        rows.append({
            "dimension": dimension,
            "column": column,
            "check": description,
            "rows": n,
            "base": b,
            "pct_of_base": round(n / b * 100, 2) if b else 0.0,
        })
    return pd.DataFrame(rows)
