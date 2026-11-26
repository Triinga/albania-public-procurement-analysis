# Albanian Public Procurement 2016-2025 - ADASYN
# Grupi 13 - Pergatitja dhe vizualizimi i te dhenave
# Repository: https://github.com/Triinga/albania-public-procurement-analysis (src/balancing/adasyn.py)
# Ekzekutimi nga rrenja e repository-t, me 10 CSV-te e APP-se ne data/raw/:
#     python -m src.balancing.adasyn

"""Balancing an imbalanced class with ADASYN (Adaptive Synthetic Sampling).

Target: `single_bidder`, a procedure that received exactly one offer (weak
competition, a common risk signal in procurement). Only about 13% of the
procedures have it, so the classes are imbalanced.

ADASYN creates synthetic examples of the minority class (like SMOTE), but it
creates MORE of them where the minority class is hard to learn: around each
minority example it counts how many of its k nearest neighbours belong to the
majority class, and generates more synthetic points for the examples that are
surrounded by the majority class.

Steps (kept simple, but done in the correct order):
1. Features known when the tender is published (fund, procedure and contract
   type, CPV division, timing, elections, COVID). Nothing about offers, winners
   or cancellation is used: it would reveal the answer (data leakage).
2. Train/test split 80/20, stratified by the class.
3. Missing fund -> median of the TRAINING set + a missing flag; categories ->
   one-hot; all features -> z-score (ADASYN uses distances, so scale matters).
4. ADASYN only on the training set. The test set keeps the real class ratio.
5. The same model (logistic regression) is trained without and with ADASYN and
   evaluated on the untouched test set.

Usage (from the repository root):
    python -m src.balancing.adasyn [csv_folder]

If no folder is given, data/raw/ is used. Tables are saved to reports/balancing/.
"""
import sys
from pathlib import Path

import pandas as pd
from imblearn.over_sampling import ADASYN
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (balanced_accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

OUT_DIR = Path("reports/balancing")
SEED = 42
TEST_SIZE = 0.20
N_NEIGHBORS = 5  # neighbours ADASYN uses to measure how hard each example is

TARGET = "single_bidder"
NUMERIC = [
    "Fondi_limit_log",          # size of the tender (log, the amounts are skewed)
    "cpv_count",                # how many CPV codes the tender covers
    "ditet_publikim_hapje",     # days from publication to opening
    "kohezgjatja_e_tenderit",   # days from opening to closing
    "muaji_publikimit",
    "year",
]
BINARY = [
    "Fondi_limit_missing",
    "is_framework_agreement",
    "periudhe_parazgjedhore",   # published in the 4 months before elections
    "gjate_covid",
    "publikim_ne_dhjetor",
]
CATEGORICAL = ["Lloji_i_procedures", "Tipi_i_kontrates", "primary_cpv_division"]


def select(df):
    """Features and target; rows without a target are left out."""
    df = df[df[TARGET].notna()]
    X = df[NUMERIC + BINARY + CATEGORICAL].copy()
    y = df[TARGET].astype(int)
    return X, y


def fit_preprocess(X_train):
    """Learn the preprocessing from the training set only."""
    return {
        "fund_median": X_train["Fondi_limit_log"].median(),
        "columns": None,  # set after one-hot
        "scaler": StandardScaler(),
    }


def apply_preprocess(X, prep, fit=False):
    """Impute, one-hot and scale; with fit=True the steps are learned from X."""
    X = X.copy()
    X["Fondi_limit_log"] = X["Fondi_limit_log"].fillna(prep["fund_median"])
    for col in BINARY:
        X[col] = X[col].astype("Int8").fillna(0).astype(int)
    for col in CATEGORICAL:
        X[col] = X[col].astype("string").fillna("[MISSING]")
    X = pd.get_dummies(X, columns=CATEGORICAL, dtype=int)
    if fit:
        prep["columns"] = X.columns
    # Categories seen only in the test set get no column; missing ones are 0.
    X = X.reindex(columns=prep["columns"], fill_value=0).astype(float)
    values = prep["scaler"].fit_transform(X) if fit else prep["scaler"].transform(X)
    return pd.DataFrame(values, columns=prep["columns"], index=X.index)


def class_table(y_before, y_after):
    """Number and share of each class before and after ADASYN (training set)."""
    rows = []
    for name, y in [("Trajnimi para ADASYN", y_before), ("Trajnimi pas ADASYN", y_after)]:
        counts = y.value_counts().reindex([0, 1], fill_value=0)
        rows.append({
            "set": name,
            "klasa_0_jo_single_bidder": int(counts[0]),
            "klasa_1_single_bidder": int(counts[1]),
            "pct_klasa_1": round(counts[1] / len(y) * 100, 2),
            "raporti_0_me_1": round(counts[0] / counts[1], 2),
        })
    return pd.DataFrame(rows)


def evaluate(name, model, X_test, y_test):
    """Metrics of the minority class on the untouched test set."""
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    return {
        "modeli": name,
        "precision_klasa_1": round(precision_score(y_test, pred, zero_division=0), 4),
        "recall_klasa_1": round(recall_score(y_test, pred), 4),
        "f1_klasa_1": round(f1_score(y_test, pred), 4),
        "balanced_accuracy": round(balanced_accuracy_score(y_test, pred), 4),
        "roc_auc": round(roc_auc_score(y_test, prob), 4),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp),
    }


def run(df):
    """Final dataset -> tables describing ADASYN and its effect."""
    X, y = select(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=SEED)

    prep = fit_preprocess(X_train)
    X_train_s = apply_preprocess(X_train, prep, fit=True)
    X_test_s = apply_preprocess(X_test, prep)

    adasyn = ADASYN(n_neighbors=N_NEIGHBORS, random_state=SEED)
    X_res, y_res = adasyn.fit_resample(X_train_s, y_train)
    y_res = pd.Series(y_res, name=TARGET)

    base = LogisticRegression(max_iter=1000).fit(X_train_s, y_train)
    balanced = LogisticRegression(max_iter=1000).fit(X_res, y_res)

    split = pd.DataFrame([
        {"set": "I gjithë dataset-i", "rreshta": len(y), "pct_klasa_1": round(y.mean() * 100, 2)},
        {"set": "Trajnimi (80%)", "rreshta": len(y_train), "pct_klasa_1": round(y_train.mean() * 100, 2)},
        {"set": "Testi (20%), pa ADASYN", "rreshta": len(y_test), "pct_klasa_1": round(y_test.mean() * 100, 2)},
    ])
    return {
        "adasyn_split": split,
        "adasyn_class_balance": class_table(y_train, y_res),
        "adasyn_model_comparison": pd.DataFrame([
            evaluate("Pa ADASYN", base, X_test_s, y_test),
            evaluate("Me ADASYN", balanced, X_test_s, y_test),
        ]),
        "adasyn_features": pd.DataFrame({
            "veti": NUMERIC + BINARY + CATEGORICAL,
            "lloji": ["numerike"] * len(NUMERIC) + ["binare"] * len(BINARY)
                     + ["kategorike (one-hot)"] * len(CATEGORICAL),
        }),
        "adasyn_settings": pd.DataFrame([
            ("Synimi (klasa)", TARGET),
            ("Ndarja trajnim/test", f"{int((1 - TEST_SIZE) * 100)}/{int(TEST_SIZE * 100)}, e shtresëzuar"),
            ("ADASYN n_neighbors", N_NEIGHBORS),
            ("random_state", SEED),
            ("Kolona pas one-hot", X_train_s.shape[1]),
            ("Shembuj sintetikë të krijuar", len(y_res) - len(y_train)),
            ("Modeli", "LogisticRegression(max_iter=1000)"),
        ], columns=["parametri", "vlera"]),
    }


def main():
    from src.common.data_loading import DATA_DIR, read_years
    from src.final.final_dataset import build

    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df, _ = build(read_years(folder))
    tables = run(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        for name, table in tables.items():
            print(f"{name}:\n{table.to_string(index=False)}\n")


if __name__ == "__main__":
    main()
