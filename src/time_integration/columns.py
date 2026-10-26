"""Time and integration columns and their data types."""
from src.common.data_types import ColumnType

# Dates and the year are interval-scaled: differences are meaningful (e.g. the
# tender duration in days), but there is no absolute zero.
COLUMNS = {
    "Data_e_publikimit": ColumnType("Numeric", "Interval (date)", "Discrete"),
    "Data_e_hapjes": ColumnType("Numeric", "Interval (date)", "Discrete"),
    "Data_e_mbylljes": ColumnType("Numeric", "Interval (date)", "Discrete"),
    "Numri_i_references": ColumnType("Categorical", "Nominal (identifier)", "Discrete"),
    "viti": ColumnType("Numeric", "Interval", "Discrete"),
}

DATETIME_COLS = [c for c, t in COLUMNS.items() if "(date)" in t.type]
NUMERIC_COLS = [c for c, t in COLUMNS.items() if t.is_numeric]
