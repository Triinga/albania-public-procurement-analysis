"""Phase II, Tringa's columns: outliers in competition, procedures and winners.

1. Univariate detection (same methods as src.outliers.amounts_time, from
   src.common.outliers): IQR and the robust MAD z-score, on the log scale,
   globally and within `Lloji_i_procedures`, for:
   - `Numri_i_ofertave_te_dorezuara`, `Numri_i_ofertave_te_kualifikuara`;
   - `cpv_count` (0 means the CPV code is missing, so 0 is left out);
   - the number of contracts won by each winner (one row per NIPT).

2. Removing false detections ("mënjanimi i zbulimeve jo të sakta"):
   - Counts are discrete: when more than half of a group has the same value,
     the IQR (or MAD) is 0 and the method would flag every other value. Such
     groups are not "tested" by that method (see `drop_zero_spread`).
   - A value flagged only by the global threshold, but normal within its own
     procedure type, is a false detection caused by scale (Small Value
     procedures dominate the global distribution). The status therefore uses
     the within-group flags; the global ones are kept in the report.
   - Known impossible values (qualified offers > submitted, negative counts,
     invalid NIPT typos) are "gabim" whatever the statistics say.
   - The cases Phase I left for Part II are reviewed one by one: the 5,054
     contradictory cancellations, the 74 winners with 0 qualified offers, the
     NIPTs outside the Albanian format and the winners with very many contracts.

3. Multivariate detection: Mahalanobis distance (NumPy) on the 9 standardized
   PCA features, compared with the chi-square threshold. The mean and
   covariance are re-estimated without the known errors and the first-pass
   outliers, so that the outliers do not hide themselves (masking). It is done
   globally and within each procedure type, like the univariate step. A KNN
   distance check (the method from the course exercises) on a sample confirms
   that both methods point at the same procedures.

Nothing is removed; the flags go to data/processed/ for the final dataset.

Usage (from the repository root):
    python -m src.outliers.competition_winners [csv_folder]
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.common.outliers import ERROR, RARE, UNCERTAIN, detect, outlier_status, status_counts
from src.final.final_dataset import build
from src.outliers.amounts_time import AMOUNT_ERROR_ABOVE
from src.values_winners.pca import feature_matrix

OUT_DIR = Path("reports/outliers")
PROCESSED_DIR = Path("data/processed")
KEYS = ["Numri_i_references", "Autoriteti_kontraktues", "year"]
GROUP = "Lloji_i_procedures"

SUBMITTED = "Numri_i_ofertave_te_dorezuara"
QUALIFIED = "Numri_i_ofertave_te_kualifikuara"
COUNT_COLUMNS = [SUBMITTED, QUALIFIED, "cpv_count"]

# Albanian NIPT: one letter, 8 digits, one letter (e.g. K31528061N).
NIPT_PATTERN = r"[A-Z]\d{8}[A-Z]"
# Foreign VAT numbers start with the country code (SI, HR, ATU, IT, ...).
FOREIGN_VAT_PATTERN = r"[A-Z]{2,3}\d{5,14}"
# An Albanian NIPT with one letter missing, or with extra characters around it.
NIPT_TYPO_PATTERN = r"\d{8}[A-Z]|[A-Z]\d{8}|.*[A-Z]\d{8}[A-Z].*"

# Chi-square 99.9% quantile with 9 degrees of freedom (9 PCA features):
# scipy.stats.chi2.ppf(0.999, 9) = 27.877. A standardized, roughly normal
# point exceeds it with probability 0.1%.
CHI2_999_DF9 = 27.877
# Procedure types with fewer complete rows than this get no group covariance
# (9x9 covariance needs enough rows); the global flag is used for them.
MIN_GROUP_ROWS = 1000
# The cancellation contradictions with a signed contract are almost all from
# one export year, so they are a recording error of that year, not behaviour.
SYSTEMATIC_YEAR = 2017
# Winner value this many times above (or below) the fund limit = unit/decimal error.
SCALE_ERROR_FACTOR = 100
KNN_SAMPLE, KNN_NEIGHBOURS, SEED = 20_000, 5, 42


# --- 1. Univariate detection -------------------------------------------------

def drop_zero_spread(values, flags, group):
    """Turn off the IQR/MAD flags in groups where that spread is 0.

    With discrete counts a single value can cover more than half of a group
    (e.g. cpv_count = 1); then IQR or MAD is 0 and every other value would be
    "outside". The method cannot judge such a group, so it flags nothing there.
    """
    def iqr(s):
        return s.quantile(0.75) - s.quantile(0.25)

    def mad(s):
        return (s - s.median()).abs().median()

    flags = flags.copy()
    if iqr(values.dropna()) == 0:
        flags["outlier_iqr_global"] = False
    if mad(values.dropna()) == 0:
        flags["outlier_mad_global"] = False
    by_group = values.groupby(group)
    flags.loc[by_group.transform(iqr).eq(0), "outlier_iqr_group"] = False
    flags.loc[by_group.transform(mad).eq(0), "outlier_mad_group"] = False
    return flags


def count_flags(df, column):
    """IQR/MAD flags for one count column (log scale, global and per procedure type)."""
    data = df[[column, GROUP]].copy()
    data[column] = data[column].astype("float64")
    if column == "cpv_count":
        data.loc[data[column].eq(0), column] = np.nan  # 0 = CPV code missing
    flags = detect(data, column, group=GROUP, log=True)
    return drop_zero_spread(np.log1p(data[column]), flags, data[GROUP])


def impossible_counts(df):
    """Values that cannot be true, independent of any threshold."""
    sub, qual = df[SUBMITTED], df[QUALIFIED]
    share = df["qualified_offer_share"]
    return {
        "Oferta të kualifikuara > të dorëzuara": qual.gt(sub).fillna(False),
        "Numër negativ ofertash": (sub.lt(0) | qual.lt(0)).fillna(False),
        "cpv_count negativ": df["cpv_count"].lt(0).fillna(False),
        "qualified_offer_share jashtë [0, 1]": (share.lt(0) | share.gt(1)).fillna(False),
    }


def univariate(df):
    """Status per count column, plus the comparison global vs within group."""
    impossible = impossible_counts(df)
    any_impossible = pd.concat(impossible, axis=1).any(axis=1)
    statuses, summaries, comparison = {}, [], []
    for column in COUNT_COLUMNS:
        flags = count_flags(df, column)
        group_flags = flags[["outlier_iqr_group", "outlier_mad_group"]]
        status = outlier_status(group_flags, any_impossible)
        statuses[column] = status
        summaries.append(status_counts(status, column))

        global_any = flags[["outlier_iqr_global", "outlier_mad_global"]].any(axis=1)
        group_any = group_flags.any(axis=1)
        comparison.append({
            "column": column,
            "flagged_global": int(global_any.sum()),
            "flagged_within_group": int(group_any.sum()),
            "global_only (false detection, scale)": int((global_any & ~group_any).sum()),
            "group_only (hidden by the global scale)": int((group_any & ~global_any).sum()),
            "both": int((global_any & group_any).sum()),
        })
    impossible_table = pd.DataFrame({"check": list(impossible),
                                     "procedures": [int(m.sum()) for m in impossible.values()]})
    return statuses, pd.concat(summaries, ignore_index=True), pd.DataFrame(comparison), impossible_table


def count_spread(df):
    """Quartiles, IQR and MAD of each count column (log scale), globally and per group."""
    rows = []
    for column in COUNT_COLUMNS:
        values = df[column].astype("float64")
        if column == "cpv_count":
            values = values.where(values > 0)
        logged = np.log1p(values)
        for name, part in [("(global)", logged)] + list(logged.groupby(df[GROUP])):
            part = part.dropna()
            if len(part) == 0:
                continue
            q1, q3 = part.quantile(0.25), part.quantile(0.75)
            mad = (part - part.median()).abs().median()
            rows.append({"column": column, "group": name, "rows": len(part),
                         "median": round(np.expm1(part.median()), 1),
                         "q1": round(np.expm1(q1), 1), "q3": round(np.expm1(q3), 1),
                         "upper_iqr_limit": round(np.expm1(q3 + 1.5 * (q3 - q1)), 1),
                         "iqr_log": round(q3 - q1, 3), "mad_log": round(mad, 3),
                         "zero_spread": bool(q3 == q1 or mad == 0)})
    return pd.DataFrame(rows)


# --- 2. Winners: NIPT and number of contracts ------------------------------

def nipt_class(nipt):
    """Classify one NIPT cell: valid, consortium, foreign, typo or unknown."""
    if pd.isna(nipt):
        return pd.NA
    parts = [p.strip() for p in str(nipt).split("|")]
    if len(parts) > 1:
        if all(re.fullmatch(NIPT_PATTERN, p) for p in parts):
            return "Konsorcium (NIPT të vlefshëm)"
        return "Konsorcium me NIPT të pavlefshëm"
    nipt = parts[0]
    if re.fullmatch(NIPT_PATTERN, nipt):
        return "I vlefshëm"
    if re.fullmatch(FOREIGN_VAT_PATTERN, nipt):
        return "Kompani e huaj (numër TVSH)"
    if re.fullmatch(NIPT_TYPO_PATTERN, nipt):
        return "Gabim shtypi në NIPT shqiptar"
    return "I panjohur (vetëm shifra ose format tjetër)"


NIPT_STATUS = {
    "I vlefshëm": pd.NA,
    "Konsorcium (NIPT të vlefshëm)": pd.NA,
    "Kompani e huaj (numër TVSH)": RARE,
    "Gabim shtypi në NIPT shqiptar": ERROR,
    "Konsorcium me NIPT të pavlefshëm": UNCERTAIN,
    "I panjohur (vetëm shifra ose format tjetër)": UNCERTAIN,
}


def winner_profile(df):
    """One row per winner (NIPT): contracts won, authorities, years, NIPT class, outlier status."""
    winners = df[df["NIPT_i_fituesit"].notna()]
    profile = winners.groupby("NIPT_i_fituesit").agg(
        fituesi=("Fituesi", "first"),
        kontrata=("Numri_i_references", "size"),
        autoritete=("Autoriteti_kontraktues", "nunique"),
        vite=("year", "nunique"),
        lloje_procedure=(GROUP, "nunique"),
    ).reset_index()
    profile["nipt_klasa"] = profile["NIPT_i_fituesit"].map(nipt_class)

    flags = detect(profile, "kontrata", log=True)
    typo = profile["nipt_klasa"].eq("Gabim shtypi në NIPT shqiptar")
    profile["outlier_status"] = outlier_status(flags, typo)
    # A winner with very many contracts from many authorities over several
    # years is a large real supplier; one that depends on 1-2 authorities is
    # real too, but a sign of market dependence worth reading.
    many = profile["outlier_status"].notna() & ~typo
    profile["interpretimi"] = pd.NA
    profile.loc[many & profile["autoritete"].ge(3) & profile["vite"].ge(2), "interpretimi"] = \
        "Furnitor i madh real (shumë autoritete, disa vite)"
    profile.loc[many & profile["autoritete"].le(2), "interpretimi"] = \
        "Real, por i varur nga 1-2 autoritete"
    profile.loc[many & profile["interpretimi"].isna(), "interpretimi"] = "Për shqyrtim"
    return profile.sort_values("kontrata", ascending=False)


# --- 3. Phase I cases left for Part II -------------------------------------

def review_contradictions(df):
    """Classify the 5,054 contradictory cancellations and the 74 winners with 0 qualified offers.

    Returns the status per procedure (gabim / e vërtetë por e rrallë / e pasigurt /
    NaN = the detection was not correct) and the reason for it.
    """
    signed = df["flag_kontrate_anuluar"].eq(1)
    no_offer = df["flag_pa_oferte_kontradikte"].eq(1)
    winner = df["Fituesi"].notna()
    qualified = df[QUALIFIED].fillna(0).gt(0)
    cancelled = df["Anulluar"].eq(True).fillna(False)
    zero_qualified_winner = winner & df[QUALIFIED].eq(0).fillna(False)

    status = pd.Series(pd.NA, index=df.index, dtype="object")
    reason = pd.Series(pd.NA, index=df.index, dtype="object")

    rules = [  # later rules win, so the strongest evidence comes last
        (no_offer, UNCERTAIN, "Arsyeja 'asnjë ofertë', ka oferta, pa provë tjetër"),
        (no_offer & ~qualified & ~winner, pd.NA,
         "Zbulim jo i saktë: oferta pa asnjë të kualifikuar, arsyeja do të thotë 'asnjë ofertë e vlefshme'"),
        (no_offer & qualified & winner, ERROR,
         "Arsyeja 'asnjë ofertë', por ka oferta të kualifikuara dhe fitues"),
        (signed, UNCERTAIN, "E anuluar me vlerë kontrate (mund të jetë anulim i pjesshëm)"),
        (signed & df["year"].eq(SYSTEMATIC_YEAR), ERROR,
         f"E anuluar me vlerë kontrate: gabim sistematik i eksportit {SYSTEMATIC_YEAR}"),
        (zero_qualified_winner & cancelled, RARE,
         "Fitues me 0 oferta të kualifikuara, por procedura u anulua (konsistente)"),
        (zero_qualified_winner & ~cancelled, ERROR,
         "Fitues me 0 oferta të kualifikuara dhe procedura nuk u anulua"),
    ]
    for mask, label, why in rules:
        status[mask] = label
        reason[mask] = why
    checked = no_offer | signed | zero_qualified_winner
    summary = (pd.DataFrame({"rasti": reason[checked], "outlier_status": status[checked]})
               .fillna({"outlier_status": "(nuk është gabim)"})
               .value_counts().rename("procedures").reset_index())
    by_year = pd.crosstab(df.loc[checked, "year"], reason[checked])
    return status, reason, summary, by_year


# --- 4. Multivariate detection (Mahalanobis) -------------------------------

def mahalanobis_d2(X, fit_rows):
    """Squared Mahalanobis distance of every row of X, with mean/covariance from `fit_rows`."""
    fit = X[fit_rows]
    mean = fit.mean().to_numpy()
    inverse = np.linalg.pinv(np.cov(fit.to_numpy(), rowvar=False))
    diff = X.to_numpy() - mean
    return pd.Series(np.einsum("ij,jk,ik->i", diff, inverse, diff), index=X.index)


def robust_d2(X, known_errors):
    """Two-step estimate: fit without known errors, then refit without the first-pass outliers.

    A plain mean/covariance is pulled towards the outliers and makes them look
    closer than they are (masking); dropping them once and refitting is a
    simple version of the robust-covariance idea.
    """
    first = mahalanobis_d2(X, ~known_errors)
    return mahalanobis_d2(X, ~known_errors & (first <= CHI2_999_DF9))


def amount_errors(df):
    """Amounts already known to be impossible.

    - Semine's threshold (above 100 billion lek) and the values <= 1 lek (Phase I);
    - a winner value 100 times above or below the fund limit. The ratio
      value/fund is 0.1-3.2 for 96% of procedures; beyond a factor of 100 the
      values sit in separate clusters (a peak at exactly x1000, i.e. one amount
      entered in thousands of lek), so they are a unit or decimal error, not a
      real price. See docs/outliers.md, section 4.5.
    """
    amounts = df[["Fondi_limit", "Vlera_e_fituesit"]]
    ratio = df["Vlera_e_fituesit"] / df["Fondi_limit"].where(df["Fondi_limit"] > 1)
    scale_error = ratio.ge(SCALE_ERROR_FACTOR) | ratio.le(1 / SCALE_ERROR_FACTOR)
    return (amounts.gt(AMOUNT_ERROR_ABOVE) | amounts.le(1)).any(axis=1) | scale_error.fillna(False)


def value_fund_ratio_profile(df):
    """Distribution of log10(winner value / fund limit), the evidence for SCALE_ERROR_FACTOR."""
    both = df["Fondi_limit"].gt(1) & df["Vlera_e_fituesit"].gt(1)
    log_ratio = np.log10(df.loc[both, "Vlera_e_fituesit"] / df.loc[both, "Fondi_limit"])
    counts = pd.cut(log_ratio, np.arange(-6, 6.5, 0.5)).value_counts().sort_index()
    return pd.DataFrame({"log10_ratio": counts.index.astype(str),
                         "ratio_from": [10 ** i.left for i in counts.index],
                         "ratio_to": [10 ** i.right for i in counts.index],
                         "procedures": counts.values})


def multivariate(df, count_impossible):
    """Mahalanobis status per procedure, globally and within procedure type."""
    X = feature_matrix(df)
    known = (amount_errors(df) | count_impossible).reindex(X.index, fill_value=False)
    d2_global = robust_d2(X, known)

    d2_group = pd.Series(np.nan, index=X.index)
    groups = df.loc[X.index, GROUP]
    for name, rows in groups.groupby(groups).groups.items():
        if len(rows) >= MIN_GROUP_ROWS:
            # Mahalanobis does not depend on the scaling, so the global z-scores
            # can be reused; only the mean and covariance are the group's own.
            d2_group[rows] = robust_d2(X.loc[rows], known[rows])
    out_global = d2_global > CHI2_999_DF9
    out_group = (d2_group > CHI2_999_DF9).where(d2_group.notna(), out_global)

    status = pd.Series(pd.NA, index=X.index, dtype="object")
    status[out_global & out_group] = RARE
    status[out_global ^ out_group] = UNCERTAIN
    status[(out_global | out_group) & known] = ERROR

    # Which feature pushes each outlier furthest from the centre (largest |z|)
    centre = X[~known & ~out_global].mean()
    driver = (X - centre).abs().idxmax(axis=1).where(out_global | out_group)

    result = pd.DataFrame({"mahalanobis_d2": d2_global.round(3),
                           "outlier_global": out_global, "outlier_group": out_group,
                           "status": status, "driver": driver})
    summary = pd.DataFrame([
        ("Procedures with all 9 features", len(X)),
        ("Chi-square threshold (99.9%, df=9)", CHI2_999_DF9),
        ("Expected share above the threshold if normal (%)", 0.1),
        ("Known amount/count errors among them", int(known.sum())),
        ("Outliers, global", int(out_global.sum())),
        ("Outliers, within procedure type", int(out_group.sum())),
        ("Global only (false detection, scale)", int((out_global & ~out_group).sum())),
        ("Group only (hidden by the global scale)", int((out_group & ~out_global).sum())),
        (f"Status: {ERROR}", int(status.eq(ERROR).sum())),
        (f"Status: {RARE}", int(status.eq(RARE).sum())),
        (f"Status: {UNCERTAIN}", int(status.eq(UNCERTAIN).sum())),
    ], columns=["metric", "value"])
    drivers = (driver.dropna().value_counts().rename_axis("feature")
               .reset_index(name="outliers"))
    return result, summary, drivers, X


def knn_check(X, outlier, d2):
    """Cross-check with the KNN distance method from the exercises, on a sample.

    Mean distance to the 5 nearest neighbours; the same share of points as
    Mahalanobis flags is taken as KNN outliers, and the overlap is measured.
    """
    try:
        from sklearn.neighbors import NearestNeighbors
    except ImportError:
        return pd.DataFrame([("scikit-learn is not installed; check skipped", np.nan)],
                            columns=["metric", "value"])
    sample = X.sample(min(KNN_SAMPLE, len(X)), random_state=SEED)
    distances, _ = NearestNeighbors(n_neighbors=KNN_NEIGHBOURS + 1).fit(sample).kneighbors(sample)
    knn_distance = pd.Series(distances[:, 1:].mean(axis=1), index=sample.index)
    maha = outlier.reindex(sample.index)
    share = maha.mean()
    knn_out = knn_distance > knn_distance.quantile(1 - share)
    both = (maha & knn_out).sum()
    return pd.DataFrame([
        ("Sample size", len(sample)),
        ("Neighbours (k)", KNN_NEIGHBOURS),
        ("Share flagged by Mahalanobis in the sample (%)", round(share * 100, 2)),
        ("Flagged by Mahalanobis", int(maha.sum())),
        ("Flagged by KNN (same share)", int(knn_out.sum())),
        ("Flagged by both", int(both)),
        ("Mahalanobis outliers also found by KNN (%)", round(both / max(maha.sum(), 1) * 100, 1)),
        ("Expected overlap if unrelated (%)", round(share * 100, 2)),
        ("Spearman correlation, Mahalanobis D2 vs KNN distance",
         round(d2.reindex(sample.index).corr(knn_distance, method="spearman"), 3)),
    ], columns=["metric", "value"])


# --- Flags for the final dataset -------------------------------------------

def flag_columns(df, statuses, profile, contradiction, contradiction_reason, multi):
    """One row per procedure: keys plus the Phase II flags of this part."""
    flags = df[KEYS].copy()
    names = {SUBMITTED: "ofertat_dorezuara", QUALIFIED: "ofertat_kualifikuara",
             "cpv_count": "cpv_count"}
    for column, status in statuses.items():
        flags[f"outlier_status_{names[column]}"] = status
    winner_status = profile.set_index("NIPT_i_fituesit")["outlier_status"].astype("object")
    flags["outlier_status_fituesi"] = df["NIPT_i_fituesit"].map(winner_status)
    nipt = profile.set_index("NIPT_i_fituesit")["nipt_klasa"]
    flags["nipt_klasa"] = df["NIPT_i_fituesit"].map(nipt)
    flags["outlier_status_konsistenca"] = contradiction
    flags["arsye_konsistenca"] = contradiction_reason
    flags["mahalanobis_d2"] = multi["mahalanobis_d2"]
    flags["outlier_status_multivariant"] = multi["status"]
    return flags


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    df, _ = build(read_years(folder))

    statuses, univariate_summary, global_vs_group, impossible = univariate(df)
    spread = count_spread(df)
    profile = winner_profile(df)
    winner_summary = status_counts(profile["outlier_status"], "kontrata për fitues")
    nipt_summary = (profile.loc[profile["nipt_klasa"].ne("I vlefshëm")]
                    .groupby("nipt_klasa").agg(fitues=("NIPT_i_fituesit", "size"),
                                               kontrata=("kontrata", "sum"))
                    .reset_index())
    nipt_summary["outlier_status"] = nipt_summary["nipt_klasa"].map(NIPT_STATUS)
    contradiction, reason, contradiction_summary, contradiction_by_year = review_contradictions(df)
    any_impossible = pd.concat(impossible_counts(df), axis=1).any(axis=1)
    multi, multi_summary, drivers, X = multivariate(df, any_impossible)
    knn = knn_check(X, multi["outlier_global"], multi["mahalanobis_d2"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    tables = {
        "competition_outlier_summary": univariate_summary,
        "competition_global_vs_group": global_vs_group,
        "competition_count_spread": spread,
        "competition_impossible_values": impossible,
        "winners_outlier_summary": winner_summary,
        "winners_top_contracts": profile.head(50),
        "winners_nipt_review": nipt_summary,
        "winners_nipt_invalid": profile[~profile["nipt_klasa"].isin(
            ["I vlefshëm", "Konsorcium (NIPT të vlefshëm)"])],
        "consistency_review": contradiction_summary,
        "consistency_review_by_year": contradiction_by_year.reset_index(),
        "multivariate_summary": multi_summary,
        "multivariate_drivers": drivers,
        "multivariate_knn_check": knn,
        "value_fund_ratio": value_fund_ratio_profile(df),
    }
    for name, table in tables.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    flags = flag_columns(df, statuses, profile, contradiction, reason, multi)
    flags.to_csv(PROCESSED_DIR / "outliers_competition_winners.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_rows", 200,
                           "display.max_colwidth", 90):
        for name in ["competition_outlier_summary", "competition_global_vs_group",
                     "competition_impossible_values", "winners_outlier_summary",
                     "winners_nipt_review", "consistency_review", "multivariate_summary",
                     "multivariate_drivers", "multivariate_knn_check"]:
            print(f"{name}:\n{tables[name].to_string(index=False)}\n")
    print(f"Flags for {len(flags):,} procedures saved to "
          f"{PROCESSED_DIR / 'outliers_competition_winners.csv'}")


if __name__ == "__main__":
    main()
