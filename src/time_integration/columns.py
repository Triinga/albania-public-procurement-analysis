"""Time and integration columns and their data types."""
from src.common.data_types import ColumnType

COLUMNS = {
    "Data_e_publikimit": ColumnType("Categorical", "Datetime", "Discrete"),
    "Data_e_hapjes": ColumnType("Categorical", "Datetime", "Discrete"),
    "Data_e_mbylljes": ColumnType("Categorical", "Datetime", "Discrete"),
    "Numri_i_references": ColumnType("Numeric", "Count", "Discrete"),
    "viti": ColumnType("Numeric", "Ordinal", "Discrete"),
}

DATETIME_COLS = [c for c, t in COLUMNS.items() if "Datetime" in t.type]
NUMERIC_COLS = [c for c, t in COLUMNS.items() if t.is_numeric]
