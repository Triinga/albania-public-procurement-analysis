"""Dimensionality reduction (PCA) on the integrated dataset.

Uses the quantitative features of all three parts (values and winners, time,
procedure and competition). Binary flags and one-hot columns are left out: PCA
summarizes continuous variation, and the 0/1 columns would dominate it.

Excluded on purpose:
- `Vlera_e_fituesit_ne_lidhjen_e_kontrates`: missing in 81.5% of procedures;
- `kursimi`, `kursimi_pct`: contain the logically impossible values (Part II);
- `muaji_publikimit`: a cyclic month number, not a quantity.

Skewed non-negative features get log(1 + x); then every feature is z-scored so
all have the same weight. PCA needs complete rows, so only procedures with all
features present are used (the missing-value strategy keeps NaN, no imputation).

Usage (from the repository root):
    python -m src.values_winners.pca [csv_folder]

If no folder is given, data/raw/ is used. Component scores are saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.pca import components_for, pca
from src.common.transform import log_transform, z_score
from src.time_integration.integrated_dataset import integrate, prepare_parts

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
KEYS = ["Numri_i_references", "Autoriteti_kontraktues", "year"]

# feature: (part, transformation before z-score)
FEATURES = {
    "Fondi_limit": ("values_winners", "log"),
    "Vlera_e_fituesit": ("values_winners", "log"),
    "ditet_publikim_hapje": ("time_integration", "log"),
    "kohezgjatja_e_tenderit": ("time_integration", "log"),
    "ditet_nga_zgjedhjet": ("time_integration", "none"),
    "Numri_i_ofertave_te_dorezuara": ("procedure_competition", "log"),
    "Numri_i_ofertave_te_kualifikuara": ("procedure_competition", "log"),
    "qualified_offer_share": ("procedure_competition", "none"),
    "cpv_count": ("procedure_competition", "log"),
}


def feature_matrix(df):
    """Selected features, transformed and standardized, complete rows only."""
    X = df[list(FEATURES)].astype("float64")
    X = X.dropna()
    for col, (_, how) in FEATURES.items():
        if how == "log":
            X[col] = log_transform(X[col])
        X[col] = z_score(X[col])
    return X


def feature_table(df, X):
    return pd.DataFrame([
        {"feature": col, "part": part,
         "transformation": ("log(1 + x) + z-score" if how == "log" else "z-score"),
         "non_null_in_dataset": int(df[col].notna().sum())}
        for col, (part, how) in FEATURES.items()
    ]).assign(rows_used=len(X))


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")
    df = integrate(prepare_parts(raw))

    X = feature_matrix(df)
    explained, loadings, scores = pca(X)
    features = feature_table(df, X)
    correlation = X.corr().round(3)
    summary = pd.DataFrame([
        ("Procedures in the dataset", len(df)),
        ("Procedures used (all features present)", len(X)),
        ("Features", X.shape[1]),
        ("Components for 80% of the variance", components_for(explained, 80)),
        ("Components for 90% of the variance", components_for(explained, 90)),
    ], columns=["metric", "value"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUT_DIR / "pca_features.csv", index=False)
    correlation.to_csv(OUT_DIR / "pca_feature_correlation.csv")
    explained.to_csv(OUT_DIR / "pca_explained_variance.csv", index=False)
    loadings.to_csv(OUT_DIR / "pca_loadings.csv")
    summary.to_csv(OUT_DIR / "pca_summary.csv", index=False)
    df.loc[X.index, KEYS].join(scores).to_csv(PROCESSED_DIR / "pca_scores.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 20):
        for title, table in [("Summary", summary), ("Features", features),
                             ("Correlation", correlation), ("Explained variance", explained),
                             ("Loadings", loadings)]:
            print(f"{title}:\n{table.to_string(index=title in ('Correlation', 'Loadings'))}\n")


if __name__ == "__main__":
    main()
