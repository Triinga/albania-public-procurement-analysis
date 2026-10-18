"""Describing the data type of each column, reusable for any group of columns.

Columns are described with a spec: {column_name: ColumnType(...)}.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ColumnType:
    category: str  # "Numeric" or "Categorical"
    type: str      # e.g. "Ratio", "Nominal", "Ordinal", "Binary (Po/Jo)", "Datetime"
    nature: str    # "Continuous" or "Discrete"

    @property
    def is_numeric(self):
        return self.category == "Numeric"


def describe_types(df, spec):
    """One row per column: its data type, how it is stored in the CSV and example values."""
    rows = []
    for col, t in spec.items():
        s = df[col].dropna()
        rows.append({
            "column": col,
            "category": t.category,
            "type": t.type,
            "nature": t.nature,
            "csv_type": "text" if pd.api.types.is_string_dtype(df[col]) else str(df[col].dtype),
            "unique_values": int(s.nunique()),
            "examples": " | ".join(s.drop_duplicates().head(3)),
        })
    return pd.DataFrame(rows)
