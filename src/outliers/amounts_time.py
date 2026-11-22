"""Phase II, Semine's columns: outlier detection for the amounts and the time columns.

Detects outliers with IQR and a robust (MAD) z-score, globally and within
`Lloji_i_procedures` (small and large procedures have a different scale, so a
single global threshold would flag almost every large procedure). Separates
known impossible values from genuine large-but-real values (see
`src.common.outliers.outlier_status`); nothing is removed, only flagged.

Also checks the two cases Phase I left for Part II:
- 26,749 procedures where the contract value differs from the winner value
  (could be VAT, negotiation or lots, or a real data problem).
- The 13 procedures published later than February of the year after the file
  (`late_publication`, after Phase I's date cleaning).

Thresholds (see `docs/outliers.md` for the data behind each one):
- A value above `AMOUNT_ERROR_ABOVE` is a known error: the largest real amount
  is ~39 billion lek, and the only values above 100 billion are the ~35,000
  billion lek entries Phase I already flagged as impossible.
- A contract/winner ratio in `[0.75, 1.25]` covers the entire real pattern
  (almost all cases are a ratio of exactly 1.0 or 1.2 = 20% TVSH); the 122
  cases outside it are mostly a contract value of 0 next to a real winner
  value, not a scale difference, so they go to Part II for review instead of
  being dropped.

Usage (from the repository root):
    python -m src.outliers.amounts_time [csv_folder]
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.common.outliers import detect, outlier_status, status_counts
from src.final.final_dataset import build
from src.time_integration.quality import late_publication

OUT_DIR = Path("reports/outliers")

# Columns checked here, with whether the log scale applies (amounts and most
# durations are right-skewed and non-negative; days-to-election can be
# negative, so it is left on its original scale).
AMOUNT_COLUMNS = ["Fondi_limit", "Vlera_e_fituesit", "Vlera_e_fituesit_ne_lidhjen_e_kontrates"]
TIME_COLUMNS_LOG = ["ditet_publikim_hapje", "kohezgjatja_e_tenderit"]
TIME_COLUMNS_LINEAR = ["ditet_nga_zgjedhjet"]
GROUP = "Lloji_i_procedures"

# A value this large is not a real procurement amount in Albania; it is the kind
# of entry Phase I already saw for other columns (a misplaced decimal/extra
# digits), so it is a known error rather than a genuine rare large procedure.
AMOUNT_ERROR_ABOVE = 1e11  # 100 billion lek (~ EUR 1 billion)
DURATION_ERROR_ABOVE = 3650  # 10 years; Phase I's cleaning already caps this near 440 days

# "Vlera e kontratës != vlera e fituesit" can be normal (VAT ~20%, negotiation
# after the offer, contracts covering several lots); treated as a data problem
# worth a closer look only outside a generous +/-25% band around the winner value.
CONTRACT_RATIO_LOW, CONTRACT_RATIO_HIGH = 0.75, 1.25


def detect_column(df, column, log):
    """Outlier flags, status and a one-row-per-status summary for one column."""
    flags = detect(df, column, group=GROUP, log=log)
    if column in AMOUNT_COLUMNS:
        impossible = df[column] > AMOUNT_ERROR_ABOVE
    elif column in TIME_COLUMNS_LOG:
        impossible = (df[column] < 0) | (df[column] > DURATION_ERROR_ABOVE)
    else:
        impossible = pd.Series(False, index=df.index)
    status = outlier_status(flags, impossible)
    return status, status_counts(status, column)


def contract_vs_winner_value(df):
    """The 26,749 cases where the contract value differs from the winner value."""
    both = df["Vlera_e_fituesit"].notna() & df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"].notna()
    # Same tolerance as src.values_winners.quality_after: differences under 1 lek are rounding.
    differ = both & (df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"] - df["Vlera_e_fituesit"]).abs().gt(1)
    ratio = df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"] / df["Vlera_e_fituesit"]
    plausible = ratio.between(CONTRACT_RATIO_LOW, CONTRACT_RATIO_HIGH)
    status = pd.Series(pd.NA, index=df.index, dtype="object")
    status[differ & plausible] = "E rregullt (brenda +/-25%)"
    status[differ & ~plausible] = "Për shqyrtim (jashtë +/-25%)"
    counts = (status[differ].value_counts()
              .rename_axis("statusi").reset_index(name="procedures"))
    return status, counts


def late_publications_phase2(df):
    """The procedures still published later than February of the next year, after cleaning."""
    late = late_publication(df, df["Data_e_publikimit"])
    columns = ["Numri_i_references", "Autoriteti_kontraktues", "Data_e_publikimit", "year"]
    rows = df.loc[late, columns].copy()
    rows["ditet_vonese"] = (rows["Data_e_publikimit"]
                             - pd.to_datetime(rows["year"].astype(str) + "-03-01")).dt.days
    return rows.sort_values("ditet_vonese", ascending=False)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    df, _ = build(raw)

    statuses, summaries = {}, []
    for column in AMOUNT_COLUMNS:
        statuses[column], summary = detect_column(df, column, log=True)
        summaries.append(summary)
    for column in TIME_COLUMNS_LOG:
        statuses[column], summary = detect_column(df, column, log=True)
        summaries.append(summary)
    for column in TIME_COLUMNS_LINEAR:
        statuses[column], summary = detect_column(df, column, log=False)
        summaries.append(summary)

    outlier_summary = pd.concat(summaries, ignore_index=True)
    contract_status, contract_summary = contract_vs_winner_value(df)
    late = late_publications_phase2(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outlier_summary.to_csv(OUT_DIR / "amounts_time_outlier_summary.csv", index=False)
    contract_summary.to_csv(OUT_DIR / "contract_vs_winner_value.csv", index=False)
    late.to_csv(OUT_DIR / "late_publications_phase2.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print("Outliers (amounts and time), by column and status:")
        print(outlier_summary.to_string(index=False))
        print(f"\nContract value vs winner value ({int((contract_status.notna()).sum()):,} differ):")
        print(contract_summary.to_string(index=False))
        print(f"\nPublished later than February of the next year, after cleaning ({len(late)}):")
        print(late.to_string(index=False))


if __name__ == "__main__":
    main()
