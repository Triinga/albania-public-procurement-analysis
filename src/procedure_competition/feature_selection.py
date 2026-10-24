"""Final feature selection for the procedure and competition dataset."""
import pandas as pd

from src.procedure_competition.encoding import FREQUENCY_COLUMNS, ONE_HOT_COLUMNS


DIRECT_FEATURES = [
    "year",
    "Anulluar",
    "Pezulluar",
    "Numri_i_ofertave_te_dorezuara",
    "Numri_i_ofertave_te_kualifikuara",
]

ENGINEERED_FEATURES = [
    "cpv_count",
    "offers_missing",
    "no_submitted_offers",
    "qualified_offer_share",
    "single_bidder",
    "no_qualified_offers",
    "is_framework_agreement",
    "has_cancellation_reason",
    "cancelled_without_reason",
]

BOOLEAN_FEATURES = [
    "Anulluar",
    "Pezulluar",
    "offers_missing",
    "no_submitted_offers",
    "single_bidder",
    "no_qualified_offers",
    "is_framework_agreement",
    "has_cancellation_reason",
    "cancelled_without_reason",
]

EXCLUSION_REASONS = {
    "Autoriteti_kontraktues": "Replaced by contracting_authority_frequency",
    "Objekti_i_prokurimit": "Free text retained only in the cleaned dataset",
    "Lloji_i_procedures": "Replaced by procedure_type one-hot columns",
    "Tipi_i_kontrates": "Replaced by contract_type one-hot columns",
    "Lloji_i_marreveshjes_kuader": "Replaced by framework_type one-hot columns",
    "Arsyeja_e_anullimit": "Free text replaced by cancellation indicators",
    "Kodet_CPV": "Raw multi-value field replaced by parsed CPV features",
    "primary_cpv_code": "Replaced by primary_cpv_code_frequency",
    "primary_cpv_division": "Replaced by cpv_division one-hot columns",
    "primary_cpv_division_name": "Descriptive label retained in the cleaned dataset",
    "competition_band": "Replaced by competition_band one-hot columns",
}


def _encoded_feature_columns(df):
    prefixes = tuple(f"{prefix}__" for prefix in ONE_HOT_COLUMNS.values())
    frequency_columns = set(FREQUENCY_COLUMNS.values())
    return [
        column for column in df.columns
        if column.startswith(prefixes) or column in frequency_columns
    ]


def _selection_report(encoded, selected_features):
    rows = [{
        "column": "procedure_row_id",
        "status": "selected",
        "role": "identifier",
        "reason": "Deterministic row identifier for outputs created in the same run",
    }]
    direct = set(DIRECT_FEATURES)
    engineered = set(ENGINEERED_FEATURES)
    selected = set(selected_features)

    for column in encoded.columns:
        if column in direct:
            role = "direct_feature"
            reason = "Source feature retained for analysis"
            status = "selected"
        elif column in engineered:
            role = "engineered_feature"
            reason = "Derived indicator or quantitative feature retained for analysis"
            status = "selected"
        elif column in selected:
            role = "encoded_feature"
            reason = "Numeric representation retained for analysis"
            status = "selected"
        else:
            role = "excluded_source"
            reason = EXCLUSION_REASONS.get(
                column,
                "Retained in the cleaned dataset but excluded from the numeric matrix",
            )
            status = "excluded"
        rows.append({
            "column": column,
            "status": status,
            "role": role,
            "reason": reason,
        })
    return pd.DataFrame(rows)


def select_analysis_features(encoded):
    """Create a numeric feature matrix and document every selection decision."""
    encoded_features = _encoded_feature_columns(encoded)
    selected_features = DIRECT_FEATURES + ENGINEERED_FEATURES + encoded_features
    missing = [column for column in selected_features if column not in encoded.columns]
    if missing:
        raise ValueError(f"Encoded dataset is missing selected columns: {missing}")

    matrix = encoded.loc[:, selected_features].copy()
    for column in BOOLEAN_FEATURES:
        matrix[column] = matrix[column].astype("Int8")
    matrix.insert(0, "procedure_row_id", pd.RangeIndex(1, len(matrix) + 1))
    report = _selection_report(encoded, selected_features)
    return matrix, report
