"""Column definitions for procurement procedure and competition fields."""
from src.common.data_types import ColumnType

COLUMNS = {
    "Autoriteti_kontraktues": ColumnType("Categorical", "Nominal", "Discrete"),
    "Objekti_i_prokurimit": ColumnType("Categorical", "Text", "Discrete"),
    "Lloji_i_procedures": ColumnType("Categorical", "Nominal", "Discrete"),
    "Tipi_i_kontrates": ColumnType("Categorical", "Nominal", "Discrete"),
    "Lloji_i_marreveshjes_kuader": ColumnType("Categorical", "Nominal", "Discrete"),
    "Anulluar": ColumnType("Categorical", "Binary (Po/Jo)", "Discrete"),
    "Arsyeja_e_anullimit": ColumnType("Categorical", "Text", "Discrete"),
    "Pezulluar": ColumnType("Categorical", "Binary (Po/Jo)", "Discrete"),
    "Numri_i_ofertave_te_dorezuara": ColumnType("Numeric", "Count", "Discrete"),
    "Numri_i_ofertave_te_kualifikuara": ColumnType("Numeric", "Count", "Discrete"),
    "Kodet_CPV": ColumnType("Categorical", "Multi-valued nominal", "Discrete"),
}

NUMERIC = [
    "Numri_i_ofertave_te_dorezuara",
    "Numri_i_ofertave_te_kualifikuara",
]
BINARY = ["Anulluar", "Pezulluar"]
TEXT = [
    "Autoriteti_kontraktues", "Objekti_i_prokurimit", "Lloji_i_procedures",
    "Tipi_i_kontrates", "Lloji_i_marreveshjes_kuader",
    "Arsyeja_e_anullimit", "Kodet_CPV",
]
