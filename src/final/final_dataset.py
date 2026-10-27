"""Final dataset of Part I (2016-2025): `prokurimi_final.csv`.

Builds on the integrated dataset (all three parts, see
src.time_integration.integrated_dataset) and adds the last steps:

1. Consistency between the parts: a procedure can be cancelled and still show
   a winner. Nothing is changed or removed; new columns describe these cases:
   - `kontrate_e_lidhur`: 1 if the procedure has a winner and is not cancelled.
     An operational classification from the procedure status, not independent
     proof that a contract was signed;
   - `flag_kontrate_anuluar`, `flag_pa_oferte_kontradikte`: the two kinds of
     contradictory cancellation; `anulim_kontradiktor` is 1 if at least one holds
     and `arsye_kontradikte` names which;
   - `statusi_analitik`: one analytic status per procedure (see STATUS_LABELS).
     A missing contract value does not mean there was no contract: the field is
     empty in 81.5% of the procedures.
   How the contradictory procedures are treated is decided in Part II.
2. Transformation of the amounts (log, min-max, z-score; see
   src.values_winners.transformation).
3. PCA components (see src.values_winners.pca); procedures without all PCA
   features keep NaN.
4. Columns with a single value carry no information and are dropped.

Usage (from the repository root):
    python -m src.final.final_dataset [csv_folder]

If no folder is given, data/raw/ is used. The dataset is saved to
data/processed/ (not tracked by git); the tables go to reports/final/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.features import to_binary
from src.common.pca import components_for, pca
from src.time_integration.integrated_dataset import integrate, prepare_parts
from src.values_winners.pca import feature_matrix
from src.values_winners.transformation import transform

OUT_DIR = Path("reports/final")
PROCESSED_DIR = Path("data/processed")
PCA_VARIANCE_PCT = 90  # keep the components that explain at least 90% of the variance
# Reason says no offer was submitted at all ("nuk është paraqitur asnjë ofertë brenda
# afateve kohore"). "Asnjë ofertë e përshtatshme / e vlefshme" means offers existed but
# none was suitable or valid, so it is not a contradiction.
NO_OFFER_REASON = r"asnjë ofert"
OFFERS_EXISTED_REASON = r"përshtatshme|vlefshme"

CONFIRMED = "Kontratë e konfirmuar"           # not cancelled, contract value recorded
UNCONFIRMED = "Me fitues, kontratë e pakonfirmuar"  # not cancelled, winner, no contract value
NOT_CONFIRMED = "Pa kontratë të konfirmuar"   # not cancelled, no winner, no contract value
NOT_CONCLUDED = "Jo e lidhur"                 # cancelled, without contradiction
CONTRADICTORY = "Kontradiktor"                # cancelled, but contradicts itself
STATUS_LABELS = [CONFIRMED, UNCONFIRMED, NOT_CONFIRMED, NOT_CONCLUDED, CONTRADICTORY]


def contradictions(df):
    """The two kinds of contradictory cancellation, as boolean masks."""
    cancelled = df["Anulluar"].eq(True).fillna(False)
    reason = df["Arsyeja_e_anullimit"]
    no_offer_reason = (reason.str.contains(NO_OFFER_REASON, case=False, na=False)
                       & ~reason.str.contains(OFFERS_EXISTED_REASON, case=False, na=False))
    offers = df["Numri_i_ofertave_te_dorezuara"].fillna(0).gt(0)
    return {
        "signed_contract": cancelled & df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"].notna(),
        "no_offer_reason_with_offers": cancelled & no_offer_reason & offers,
    }


def analytic_status(df, contradictory):
    """One status per procedure; the first matching rule wins."""
    cancelled = df["Anulluar"].eq(True).fillna(False)
    contract = df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"].notna()
    winner = df["Fituesi"].notna()
    rules = [
        (contradictory, CONTRADICTORY),
        (cancelled, NOT_CONCLUDED),
        (contract, CONFIRMED),
        (winner, UNCONFIRMED),
    ]
    status = pd.Series(NOT_CONFIRMED, index=df.index)
    for mask, label in reversed(rules):
        status = status.mask(mask, label)
    return pd.Categorical(status, categories=STATUS_LABELS)


def add_consistency_flags(df):
    """Flags and analytic status for procedures whose cancellation and winner disagree."""
    df = df.copy()
    cancelled = df["Anulluar"].eq(True).fillna(False)
    found = contradictions(df)
    signed, no_offer = found["signed_contract"], found["no_offer_reason_with_offers"]
    contradictory = signed | no_offer

    df["kontrate_e_lidhur"] = to_binary(df["Fituesi"].notna() & ~cancelled)
    df["flag_kontrate_anuluar"] = to_binary(signed)
    df["flag_pa_oferte_kontradikte"] = to_binary(no_offer)
    df["anulim_kontradiktor"] = to_binary(contradictory)
    df["arsye_kontradikte"] = pd.Series(pd.NA, index=df.index, dtype="string")
    df.loc[signed, "arsye_kontradikte"] = "E anuluar, por me vlerë kontrate të lidhur"
    df.loc[no_offer, "arsye_kontradikte"] = "Arsyeja: asnjë ofertë, por ka oferta"
    df.loc[signed & no_offer, "arsye_kontradikte"] = "Të dyja"
    df["statusi_analitik"] = analytic_status(df, contradictory)
    return df


def add_pca(df):
    """Add the PCA components that reach the variance threshold."""
    X = feature_matrix(df)
    explained, _, scores = pca(X)
    n = components_for(explained, PCA_VARIANCE_PCT)
    return df.join(scores.iloc[:, :n]), explained.head(n)


def drop_constant(df):
    """Drop columns that have the same value (or only missing) in every row."""
    constant = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    return df.drop(columns=constant), constant


def consistency_summary(df):
    cancelled = df["Anulluar"].eq(True).fillna(False)
    has_winner = df["Fituesi"].notna()
    found = contradictions(df)
    rows = [
        ("Procedures", len(df)),
        ("With a winner", int(has_winner.sum())),
        ("Cancelled", int(cancelled.sum())),
        ("Cancelled with a winner", int((cancelled & has_winner).sum())),
        ("kontrate_e_lidhur = 1 (winner and not cancelled)", int(df["kontrate_e_lidhur"].sum())),
        ("anulim_kontradiktor = 1", int(df["anulim_kontradiktor"].sum())),
        ("  of which: cancelled with a signed contract value",
         int(found["signed_contract"].sum())),
        ("  of which: reason says no offer was submitted, but offers exist",
         int(found["no_offer_reason_with_offers"].sum())),
        ("  of which: both", int((found["signed_contract"] & found["no_offer_reason_with_offers"]).sum())),
        ("Winner with 0 qualified offers",
         int((has_winner & df["Numri_i_ofertave_te_kualifikuara"].eq(0)).sum())),
    ]
    return pd.DataFrame(rows, columns=["check", "procedures"])


def column_summary(df, source):
    return pd.DataFrame([
        {"column": c, "added_in": source.get(c, "integrated dataset"), "dtype": str(df[c].dtype),
         "non_null": int(df[c].notna().sum()), "missing_pct": round(df[c].isna().mean() * 100, 2)}
        for c in df.columns
    ])


def build(raw):
    """Raw yearly files -> final dataset, with the tables describing each step."""
    integrated = integrate(prepare_parts(raw))
    df = add_consistency_flags(integrated)
    df, transformation = transform(df)
    df, variance = add_pca(df)
    df, constant = drop_constant(df)

    added = {c: "final: consistency" for c in [
        "kontrate_e_lidhur", "flag_kontrate_anuluar", "flag_pa_oferte_kontradikte",
        "anulim_kontradiktor", "arsye_kontradikte", "statusi_analitik"]}
    added |= {c: "final: transformation" for c in df.columns if c.endswith(("_log", "_log_minmax", "_log_z"))}
    added |= {c: "final: PCA" for c in variance["component"]}
    tables = {
        "final_summary": pd.DataFrame([
            ("Rows (procedures)", len(df)),
            ("Rows in the raw files", len(raw)),
            ("Columns in the integrated dataset", integrated.shape[1]),
            ("Columns added", len(added)),
            ("Constant columns dropped", len(constant)),
            ("Columns in the final dataset", df.shape[1]),
            (f"PCA components kept (>= {PCA_VARIANCE_PCT}% variance)", len(variance)),
            ("Procedures with PCA components", int(df["PC1"].notna().sum())),
        ], columns=["metric", "value"]),
        "final_columns": column_summary(df, added),
        "final_consistency": consistency_summary(df),
        "final_dropped_columns": pd.DataFrame({"column": constant,
                                               "reason": "Same value in every row"}),
        "final_status": df["statusi_analitik"].value_counts(sort=False).rename_axis("statusi_analitik")
                          .reset_index(name="procedures"),
    }
    return df, tables


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df, tables = build(raw)
    assert len(df) == len(raw), "rows must never be lost or duplicated"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    df.to_csv(PROCESSED_DIR / "prokurimi_final.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_rows", 200):
        for name in ["final_summary", "final_consistency", "final_status", "final_dropped_columns"]:
            print(f"{name}:\n{tables[name].to_string(index=False)}\n")
    print(f"Saved {len(df):,} rows x {df.shape[1]} columns to {PROCESSED_DIR / 'prokurimi_final.csv'}")


if __name__ == "__main__":
    main()
