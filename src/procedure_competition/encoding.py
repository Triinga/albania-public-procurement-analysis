"""Categorical encoding for procedure and competition attributes."""
import re
import unicodedata

import pandas as pd


ONE_HOT_COLUMNS = {
    "Lloji_i_procedures": "procedure_type",
    "Tipi_i_kontrates": "contract_type",
    "Lloji_i_marreveshjes_kuader": "framework_type",
    "primary_cpv_division": "cpv_division",
    "competition_band": "competition_band",
}

FREQUENCY_COLUMNS = {
    "Autoriteti_kontraktues": "contracting_authority_frequency",
    "primary_cpv_code": "primary_cpv_code_frequency",
}


def _slug(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "missing"


def _category_column_names(categories, prefix):
    names = {}
    used = set()
    for category in categories:
        stem = f"{prefix}__{_slug(category)}"
        name = stem
        suffix = 2
        while name in used:
            name = f"{stem}_{suffix}"
            suffix += 1
        names[category] = name
        used.add(name)
    return names


def encode_categories(df):
    """Append deterministic one-hot and frequency-encoded columns."""
    features = {}
    summary = []

    for source_column, prefix in ONE_HOT_COLUMNS.items():
        values = df[source_column].astype("string").fillna("[MISSING]")
        categories = sorted(values.unique().tolist())
        column_names = _category_column_names(categories, prefix)
        for category, column_name in column_names.items():
            features[column_name] = values.eq(category).astype("Int8")
        summary.append({
            "source_column": source_column,
            "encoding_method": "one_hot",
            "input_categories": len(categories),
            "generated_columns": len(column_names),
            "missing_policy": "Separate [MISSING] category when present",
        })

    for source_column, output_column in FREQUENCY_COLUMNS.items():
        values = df[source_column].astype("string").fillna("[MISSING]")
        frequencies = values.value_counts(dropna=False) / len(df) if len(df) else pd.Series(dtype=float)
        features[output_column] = values.map(frequencies).astype("Float64")
        summary.append({
            "source_column": source_column,
            "encoding_method": "frequency",
            "input_categories": int(values.nunique(dropna=False)),
            "generated_columns": 1,
            "missing_policy": "Missing values treated as a separate category",
        })

    summary.extend([
        {
            "source_column": "Objekti_i_prokurimit",
            "encoding_method": "not_encoded_free_text",
            "input_categories": int(df["Objekti_i_prokurimit"].nunique(dropna=True)),
            "generated_columns": 0,
            "missing_policy": "Original text and missing values preserved",
        },
        {
            "source_column": "Arsyeja_e_anullimit",
            "encoding_method": "not_encoded_free_text",
            "input_categories": int(df["Arsyeja_e_anullimit"].nunique(dropna=True)),
            "generated_columns": 0,
            "missing_policy": "Original text preserved; indicator feature used",
        },
    ])

    encoded_features = pd.DataFrame(features, index=df.index)
    return pd.concat([df.copy(), encoded_features], axis=1), pd.DataFrame(summary)
