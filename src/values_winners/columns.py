"""Value and winner columns and their data types."""
from src.common.data_types import ColumnType

COLUMNS = {
    "Fondi_limit": ColumnType("Numeric", "Ratio", "Continuous"),
    "Vlera_e_fituesit": ColumnType("Numeric", "Ratio", "Continuous"),
    "Vlera_e_fituesit_ne_lidhjen_e_kontrates": ColumnType("Numeric", "Ratio", "Continuous"),
    "Lidhja_e_kontrates_me_TVSH": ColumnType("Categorical", "Binary (Po/Jo)", "Discrete"),
    "Fituesi": ColumnType("Categorical", "Nominal", "Discrete"),
    "NIPT_i_fituesit": ColumnType("Categorical", "Nominal (identifier)", "Discrete"),
}

NUMERIC = [c for c, t in COLUMNS.items() if t.is_numeric]
