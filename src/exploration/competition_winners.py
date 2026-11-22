"""Phase II, Tringa's columns: exploration of competition, procedures and winners.

Univariate (summary statistics):
- frequency tables of the categorical columns (procedure type, contract type,
  competition band, analytic status, CPV division);
- mean, median, standard deviation, quartiles, skewness and kurtosis of the
  count columns, next to the robust measures (median, IQR, MAD), both on all
  procedures and without the Phase II errors ("gabim").

Multivariate:
- comparisons by group (procedure type, year): offers, single-bidder share,
  share without offers, cancellation share;
- cross-tabulations (procedure type x competition band, CPV division x fund
  category, contract type x competition band) with Cramér's V, which measures
  the strength of association (the chi-square p-value is always ~0 with
  277,764 rows, so it says nothing about strength);
- market concentration: top winners, CR4 and the Herfindahl-Hirschman index
  (HHI) by CPV division and by year;
- Pearson vs Spearman correlation of the competition features with the
  amounts, with and without the multivariate outliers;
- interpretation of the PCA components (largest loadings).

Usage (from the repository root):
    python -m src.exploration.competition_winners [csv_folder]
Run `python -m src.outliers.competition_winners` first: the flags it saves are
used to leave out the errors.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.common.outliers import ERROR
from src.common.pca import pca
from src.final.final_dataset import build
from src.outliers.competition_winners import (GROUP, KEYS, PROCESSED_DIR, QUALIFIED, SUBMITTED,
                                              amount_errors)
from src.values_winners.pca import feature_matrix

OUT_DIR = Path("reports/exploration")
FLAGS_FILE = PROCESSED_DIR / "outliers_competition_winners.csv"

COUNT_COLUMNS = [SUBMITTED, QUALIFIED, "qualified_offer_share", "cpv_count", "nr_fituesve"]
CATEGORICAL = [GROUP, "Tipi_i_kontrates", "competition_band", "statusi_analitik",
               "Anulluar", "kategoria_e_fondit"]
TOP_CPV = 15
# HHI on a 0-10,000 scale; US DOJ/FTC Merger Guidelines (2023):
# below 1,000 unconcentrated, 1,000-1,800 moderately, above 1,800 highly concentrated.
HHI_MODERATE, HHI_HIGH = 1000, 1800
CORRELATION_FEATURES = [SUBMITTED, QUALIFIED, "qualified_offer_share", "cpv_count",
                        "Fondi_limit", "Vlera_e_fituesit", "kohezgjatja_e_tenderit"]

# Reading of the components, from the largest loadings (pca_interpretation.csv).
PC_MEANING = {
    "PC1": "Madhësia dhe kompleksiteti kundrejt konkurrencës: fond/vlerë e madhe dhe "
           "tender i gjatë, me më pak oferta",
    "PC2": "Shkalla e përgjithshme: shumë oferta dhe shuma të mëdha bashkë",
    "PC3": "Cilësia e ofertave: pjesa e kualifikuar e ulët kundrejt shumë kodeve CPV",
    "PC4": "Afërsia me zgjedhjet (ditet_nga_zgjedhjet)",
    "PC5": "Koha nga publikimi deri te hapja",
    "PC6": "Shumë kode CPV me pjesë të lartë ofertash të kualifikuara",
}


# --- Univariate -----------------------------------------------------------

def frequencies(df):
    """Count and share of every category of the categorical columns."""
    tables = []
    for column in CATEGORICAL:
        counts = df[column].astype("object").fillna("(mungon)").value_counts()
        tables.append(pd.DataFrame({"column": column, "value": counts.index.astype(str),
                                    "procedures": counts.values,
                                    "pct": (counts.values / len(df) * 100).round(2)}))
    cpv = df["primary_cpv_division_name"].astype("object").fillna("(mungon CPV)").value_counts()
    tables.append(pd.DataFrame({"column": "primary_cpv_division_name", "value": cpv.index,
                                "procedures": cpv.values,
                                "pct": (cpv.values / len(df) * 100).round(2)}))
    return pd.concat(tables, ignore_index=True)


def describe(series):
    s = series.dropna().astype("float64")
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    return {"n": len(s), "mean": s.mean(), "std": s.std(), "min": s.min(), "q1": q1,
            "median": s.median(), "q3": q3, "max": s.max(), "iqr": q3 - q1,
            "mad": (s - s.median()).abs().median(), "skewness": s.skew(),
            "kurtosis": s.kurt()}


def summary_statistics(df, errors):
    """Classical and robust statistics, on all rows and without the errors."""
    rows = []
    for column in COUNT_COLUMNS:
        for subset, mask in [("Të gjitha", pd.Series(True, index=df.index)),
                             ("Pa gabimet", ~errors)]:
            rows.append({"column": column, "subset": subset, **describe(df.loc[mask, column])})
    return pd.DataFrame(rows).round(3)


# --- Multivariate: groups and cross-tabulations ----------------------------

def competition_profile(df, by):
    """Competition indicators per group."""
    grouped = df.groupby(by, observed=True)
    table = pd.DataFrame({
        "procedures": grouped.size(),
        "mean_offers": grouped[SUBMITTED].mean(),
        "median_offers": grouped[SUBMITTED].median(),
        "mean_qualified": grouped[QUALIFIED].mean(),
        "single_bidder_pct": grouped["single_bidder"].mean() * 100,
        "no_offers_pct": grouped["no_submitted_offers"].mean() * 100,
        "cancelled_pct": grouped["Anulluar"].mean() * 100,
        "mean_qualified_share": grouped["qualified_offer_share"].mean(),
    })
    return table.astype("float64").round(2).reset_index()


def cramers_v(table):
    """Strength of association of a contingency table, 0 (none) to 1 (perfect)."""
    observed = table.to_numpy(dtype=float)
    expected = observed.sum(axis=1, keepdims=True) @ observed.sum(axis=0, keepdims=True) / observed.sum()
    chi2 = ((observed - expected) ** 2 / expected).sum()
    k = min(observed.shape) - 1
    return float(np.sqrt(chi2 / (observed.sum() * k))) if k else np.nan


def crosstab_pct(df, rows, columns, top=None):
    """Row percentages of a cross-tabulation, plus its Cramér's V."""
    data = df[[rows, columns]].dropna()
    if top:
        data = data[data[rows].isin(data[rows].value_counts().head(top).index)]
    counts = pd.crosstab(data[rows].astype(str), data[columns].astype(str))
    pct = (counts.div(counts.sum(axis=1), axis=0) * 100).round(1)
    pct.insert(0, "procedures", counts.sum(axis=1))
    return pct.sort_values("procedures", ascending=False).reset_index(), cramers_v(counts)


# --- Market concentration --------------------------------------------------

def hhi(values):
    """Herfindahl-Hirschman index (0-10,000) of the winners' shares."""
    shares = values / values.sum() * 100
    return float((shares ** 2).sum())


def concentration_level(index):
    if index > HHI_HIGH:
        return "E përqendruar shumë"
    if index > HHI_MODERATE:
        return "Mesatarisht e përqendruar"
    return "E pa përqendruar"


def concentration(df, valid_amount):
    """Top winners overall, and CR4/HHI (by awarded value) per CPV division and per year."""
    won = df[df["NIPT_i_fituesit"].notna() & ~df["Anulluar"].eq(True).fillna(False)]
    valued = won[valid_amount.reindex(won.index, fill_value=False)
                 & won["Vlera_e_fituesit"].notna()]

    totals = valued.groupby("NIPT_i_fituesit").agg(
        fituesi=("Fituesi", "first"), kontrata=("Numri_i_references", "size"),
        vlera=("Vlera_e_fituesit", "sum"))
    totals["share_value_pct"] = totals["vlera"] / totals["vlera"].sum() * 100
    totals["share_contracts_pct"] = totals["kontrata"] / totals["kontrata"].sum() * 100
    top_winners = totals.sort_values("vlera", ascending=False).head(20).round(3).reset_index()

    def market(group):
        by_winner = group.groupby("NIPT_i_fituesit")["Vlera_e_fituesit"].sum().sort_values(ascending=False)
        index = hhi(by_winner)
        # HHI on the number of contracts: not moved by one very large contract
        # (e.g. a single PPP concession can take a third of a year's value).
        by_count = group["NIPT_i_fituesit"].value_counts()
        return pd.Series({"procedures": len(group), "winners": len(by_winner),
                          "cr4_pct": by_winner.head(4).sum() / by_winner.sum() * 100,
                          "hhi": index, "level": concentration_level(index),
                          "largest_contract_pct": group["Vlera_e_fituesit"].max()
                          / group["Vlera_e_fituesit"].sum() * 100,
                          "hhi_by_contracts": hhi(by_count)})

    top_divisions = valued["primary_cpv_division_name"].value_counts().head(TOP_CPV).index
    by_cpv = (valued[valued["primary_cpv_division_name"].isin(top_divisions)]
              .groupby("primary_cpv_division_name").apply(market, include_groups=False)
              .sort_values("hhi", ascending=False))
    by_year = valued.groupby("year").apply(market, include_groups=False)
    overall = pd.DataFrame([{
        "winners": len(totals),
        "top10_share_value_pct": totals["share_value_pct"].nlargest(10).sum(),
        "top10_share_contracts_pct": totals["share_contracts_pct"].nlargest(10).sum(),
        "hhi_overall": hhi(totals["vlera"]),
        "level": concentration_level(hhi(totals["vlera"])),
    }])
    rounded = [t.round(2) for t in (by_cpv, by_year)]
    return top_winners, rounded[0].reset_index(), rounded[1].reset_index(), overall.round(2)


# --- Correlation and PCA ---------------------------------------------------

def correlations(df, multivariate_outlier):
    """Pearson and Spearman on the same rows, with and without the multivariate outliers.

    Amounts and durations enter on the log scale for Pearson (it measures
    linear association and is pulled by the long right tail); Spearman uses
    ranks, so the scale does not matter.
    """
    data = df[CORRELATION_FEATURES].astype("float64")
    for column in ["Fondi_limit", "Vlera_e_fituesit", "kohezgjatja_e_tenderit"]:
        data[column] = np.log1p(data[column].where(data[column] >= 0))
    data = data.dropna()
    keep = ~multivariate_outlier.reindex(data.index, fill_value=False)

    pearson_all = data.corr("pearson")
    pearson_clean = data[keep].corr("pearson")
    spearman_all = data.corr("spearman")
    pairs = []
    columns = list(data.columns)
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            pairs.append({"feature_a": a, "feature_b": b,
                          "pearson_all": pearson_all.loc[a, b],
                          "pearson_without_outliers": pearson_clean.loc[a, b],
                          "spearman_all": spearman_all.loc[a, b]})
    pairs = pd.DataFrame(pairs)
    pairs["outlier_effect"] = pairs["pearson_without_outliers"] - pairs["pearson_all"]
    pairs["pearson_minus_spearman"] = pairs["pearson_all"] - pairs["spearman_all"]
    pairs = pairs.round(3).sort_values("spearman_all", key=abs, ascending=False)
    return pearson_all.round(3), spearman_all.round(3), pairs


def pca_interpretation(df, n_components=6, top=3):
    """The largest loadings of each kept component and its reading."""
    explained, loadings, _ = pca(feature_matrix(df))
    rows = []
    for component in loadings.columns[:n_components]:
        strongest = loadings[component].abs().sort_values(ascending=False).head(top).index
        rows.append({
            "component": component,
            "explained_variance_pct": explained.set_index("component").loc[component,
                                                                           "explained_variance_pct"],
            "largest_loadings": ", ".join(f"{f} ({loadings.loc[f, component]:+.2f})" for f in strongest),
            "interpretation": PC_MEANING.get(component, ""),
        })
    return pd.DataFrame(rows)


def load_flags(df):
    """Phase II flags of this part, aligned with `df` (by position; same build order)."""
    flags = pd.read_csv(FLAGS_FILE, low_memory=False)
    if len(flags) != len(df) or not flags["Numri_i_references"].astype(str).equals(
            df["Numri_i_references"].astype(str).reset_index(drop=True)):
        raise ValueError(f"{FLAGS_FILE} does not match the dataset; rerun "
                         "python -m src.outliers.competition_winners")
    flags.index = df.index
    return flags


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df, _ = build(read_years(folder))
    flags = load_flags(df)

    status_columns = [c for c in flags.columns if c.startswith("outlier_status_")]
    errors = flags[status_columns].eq(ERROR).any(axis=1)
    multivariate_outlier = flags["outlier_status_multivariant"].notna()
    valid_amount = ~amount_errors(df)

    by_type_band, v_type_band = crosstab_pct(df, GROUP, "competition_band")
    by_cpv_fund, v_cpv_fund = crosstab_pct(df, "primary_cpv_division_name", "kategoria_e_fondit",
                                           top=TOP_CPV)
    by_contract_band, v_contract_band = crosstab_pct(df, "Tipi_i_kontrates", "competition_band")
    by_status_type, v_status_type = crosstab_pct(df, GROUP, "statusi_analitik")
    association = pd.DataFrame([
        ("Lloji_i_procedures x competition_band", v_type_band),
        (f"Ndarja CPV (top {TOP_CPV}) x kategoria_e_fondit", v_cpv_fund),
        ("Tipi_i_kontrates x competition_band", v_contract_band),
        ("Lloji_i_procedures x statusi_analitik", v_status_type),
    ], columns=["crosstab", "cramers_v"]).round(3)

    top_winners, hhi_cpv, hhi_year, hhi_overall = concentration(df, valid_amount)
    pearson, spearman, pairs = correlations(df, multivariate_outlier)
    tables = {
        "frequencies": frequencies(df),
        "summary_statistics": summary_statistics(df, errors),
        "competition_by_procedure_type": competition_profile(df, GROUP),
        "competition_by_year": competition_profile(df, "year"),
        "competition_by_contract_type": competition_profile(df, "Tipi_i_kontrates"),
        "crosstab_procedure_type_competition": by_type_band,
        "crosstab_cpv_fund_category": by_cpv_fund,
        "crosstab_contract_type_competition": by_contract_band,
        "crosstab_procedure_type_status": by_status_type,
        "crosstab_association": association,
        "concentration_top_winners": top_winners,
        "concentration_by_cpv": hhi_cpv,
        "concentration_by_year": hhi_year,
        "concentration_overall": hhi_overall,
        "correlation_pairs": pairs,
        "pca_interpretation": pca_interpretation(df),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    pearson.to_csv(OUT_DIR / "correlation_pearson.csv")
    spearman.to_csv(OUT_DIR / "correlation_spearman.csv")

    with pd.option_context("display.width", 250, "display.max_rows", 200,
                           "display.max_columns", 20, "display.max_colwidth", 80):
        for name in ["summary_statistics", "competition_by_procedure_type", "crosstab_association",
                     "crosstab_procedure_type_competition", "concentration_overall",
                     "concentration_by_cpv", "concentration_by_year", "correlation_pairs",
                     "pca_interpretation"]:
            print(f"{name}:\n{tables[name].to_string(index=False)}\n")


if __name__ == "__main__":
    main()
