"""Temporal, election and COVID features of the time columns (2016-2025),
their discretization and binarization.

Builds on the cleaned dates (see cleaning) with missing values filled (see
missing_values), so the gaps in days are never negative.

Usage (from the repository root):
    python -m src.time_integration.features [csv_folder]

If no folder is given, data/raw/ is used. The result is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.features import to_binary
from src.time_integration.cleaning import clean
from src.time_integration.columns import COLUMNS
from src.time_integration.elections import ELECTIONS
from src.time_integration.missing_values import CLOSE, OPEN, PUB, fill_missing_dates, parse_dates

OUT_DIR = Path("reports/time_integration")
PROCESSED_DIR = Path("data/processed")

# WHO declared the pandemic on 11 March 2020; restrictions lasted through 2021
COVID_START = pd.Timestamp(2020, 3, 11)
COVID_END = pd.Timestamp(2021, 12, 31)
COVID_LABELS = ["Para COVID", "Gjatë COVID", "Pas COVID"]

# More than half of the tenders last exactly 1 day, so equal-frequency bins
# collapse; the duration is split at meaningful limits instead.
DURATION_BINS = [-1, 0, 3, 14, 30, np.inf]
DURATION_LABELS = ["E njëjta ditë", "1-3 ditë", "4-14 ditë", "15-30 ditë", "Mbi 30 ditë"]

# Pre-election period: 4 months before voting day, when the Electoral Code
# (art. 91/4) restricts the use of public resources
ELECTION_WINDOW = pd.DateOffset(months=4)
ELECTION_LABELS = ["Mbi 4 muaj para", "Periudha parazgjedhore (4 muaj)",
                   "Deri 4 muaj pas", "Mbi 4 muaj pas"]

FLAGS = [f"{PUB}_corrected", f"{OPEN}_invalid", f"{CLOSE}_invalid",
         f"{OPEN}_imputed", f"{CLOSE}_imputed"]


def prepare(raw):
    """Parsed and cleaned dates with missing opening/closing dates filled."""
    return fill_missing_dates(clean(parse_dates(raw)))


def add_time_features(df):
    """Calendar parts of the publication date and the gaps between the dates."""
    df = df.copy()
    df["muaji_publikimit"] = df[PUB].dt.month
    df["tremujori_publikimit"] = df[PUB].dt.quarter
    df["dita_e_javes_publikimit"] = df[PUB].dt.dayofweek  # 0 = e hënë, 6 = e diel
    df["ditet_publikim_hapje"] = (df[OPEN] - df[PUB]).dt.days
    df["kohezgjatja_e_tenderit"] = (df[CLOSE] - df[OPEN]).dt.days
    return df


def add_election_features(df):
    """Nearest election to the publication date and the signed distance to it.

    Negative days: published before the election; positive: after it.
    """
    df = df.copy()
    dates = np.array(sorted(start for periods in ELECTIONS.values() for start, _ in periods),
                     dtype="datetime64[ns]")
    pub = df[PUB].to_numpy(dtype="datetime64[ns]")

    # Candidates are the elections right before and right after each date
    after = np.searchsorted(dates, pub).clip(1, len(dates) - 1)
    before = after - 1
    use_before = np.abs(pub - dates[before]) <= np.abs(dates[after] - pub)
    nearest = np.where(use_before, dates[before], dates[after])

    df["zgjedhjet_me_te_aferta"] = pd.to_datetime(nearest).where(df[PUB].notna())
    df["ditet_nga_zgjedhjet"] = (df[PUB] - df["zgjedhjet_me_te_aferta"]).dt.days
    return df


def add_covid_features(df):
    df = df.copy()
    bins = [pd.Timestamp.min, COVID_START, COVID_END + pd.Timedelta(days=1), pd.Timestamp.max]
    df["periudha_covid"] = pd.cut(df[PUB], bins, labels=COVID_LABELS, right=False)
    return df


def election_proximity(df):
    """Publication date relative to the 4 months before/after the nearest election.

    Voting day belongs to the pre-election period.
    """
    election, pub = df["zgjedhjet_me_te_aferta"], df[PUB]
    conditions = [
        pub < election - ELECTION_WINDOW,
        pub <= election,
        pub <= election + ELECTION_WINDOW,
    ]
    labels = np.select(conditions, ELECTION_LABELS[:3], default=ELECTION_LABELS[3])
    return pd.Categorical(labels, categories=ELECTION_LABELS, ordered=True)


def discretize(df):
    df = df.copy()
    df["kategoria_e_kohezgjatjes"] = pd.cut(df["kohezgjatja_e_tenderit"], DURATION_BINS,
                                            labels=DURATION_LABELS)
    df["afersia_me_zgjedhjet"] = election_proximity(df)
    return df


def binarize(df):
    """Yes/no columns as 0/1."""
    df = df.copy()
    df["gjate_covid"] = to_binary(df["periudha_covid"] == "Gjatë COVID")
    df["periudhe_parazgjedhore"] = to_binary(df["afersia_me_zgjedhjet"] == ELECTION_LABELS[1])
    df["publikim_ne_fundjave"] = to_binary(df["dita_e_javes_publikimit"] >= 5)
    df["publikim_ne_dhjetor"] = to_binary(df["muaji_publikimit"] == 12)
    df["hapje_mbyllje_e_njejta_dite"] = to_binary(df["kohezgjatja_e_tenderit"] == 0)
    for flag in FLAGS:
        df[flag] = to_binary(df[flag])
    return df


def discretization_comparison(values, n_bins, bins, labels):
    """Rows per bin for equal width, equal frequency and the chosen limits."""
    schemes = {
        "Equal width": pd.cut(values, n_bins),
        # Repeated quantiles are merged, so fewer than n_bins remain
        "Equal frequency": pd.qcut(values, n_bins, duplicates="drop"),
        "Chosen limits": pd.cut(values, bins, labels=labels),
    }
    return pd.concat([
        counts.value_counts(sort=False).rename_axis("bin").reset_index(name="rows")
        .assign(method=method, bin=lambda t: t["bin"].astype(str))
        for method, counts in schemes.items()
    ])[["method", "bin", "rows"]]


def binary_summary(df):
    binaries = ["gjate_covid", "periudhe_parazgjedhore", "publikim_ne_fundjave", "publikim_ne_dhjetor",
                "hapje_mbyllje_e_njejta_dite", *FLAGS]
    return pd.DataFrame([
        {"feature": name, "ones": int(df[name].sum()), "pct_ones": round(df[name].mean() * 100, 2)}
        for name in binaries
    ])


def features_summary(df):
    rows = [
        ("muaji_publikimit", "Kohore", "Muaji i Data_e_publikimit (1-12)"),
        ("tremujori_publikimit", "Kohore", "Tremujori i Data_e_publikimit (1-4)"),
        ("dita_e_javes_publikimit", "Kohore", "Dita e javës e Data_e_publikimit (0 = e hënë)"),
        ("ditet_publikim_hapje", "Kohore", "Data_e_hapjes - Data_e_publikimit (ditë)"),
        ("kohezgjatja_e_tenderit", "Kohore", "Data_e_mbylljes - Data_e_hapjes (ditë)"),
        ("zgjedhjet_me_te_aferta", "Zgjedhore", "Data e zgjedhjeve më afër Data_e_publikimit"),
        ("ditet_nga_zgjedhjet", "Zgjedhore", "Data_e_publikimit - zgjedhjet_me_te_aferta (ditë, < 0 = para)"),
        ("periudha_covid", "COVID", "Para (< 11.03.2020), Gjatë (deri 31.12.2021), Pas COVID"),
        ("kategoria_e_kohezgjatjes", "Diskretizuar", "kohezgjatja_e_tenderit në 5 grupe me kufij të zgjedhur"),
        ("afersia_me_zgjedhjet", "Diskretizuar", "Data_e_publikimit në 4 grupe (±4 muaj nga zgjedhjet)"),
        ("gjate_covid", "Binarizuar", "1 nëse periudha_covid = Gjatë COVID"),
        ("periudhe_parazgjedhore", "Binarizuar", "1 nëse publikuar në 4 muajt para zgjedhjeve (Kodi Zgjedhor, neni 91/4)"),
        ("publikim_ne_fundjave", "Binarizuar", "1 nëse publikuar të shtunën ose të dielën"),
        ("publikim_ne_dhjetor", "Binarizuar", "1 nëse publikuar në dhjetor (fundi i vitit buxhetor)"),
        ("hapje_mbyllje_e_njejta_dite", "Binarizuar", "1 nëse kohezgjatja_e_tenderit = 0"),
        *[(f, "Binarizuar", "Flamuri i pastrimit/plotësimit -> 1/0") for f in FLAGS],
    ]
    summary = pd.DataFrame([
        {"feature": name, "group": group, "definition": definition,
         "non_null": int(df[name].notna().sum()), "dtype": str(df[name].dtype),
         "negative": int(df[name].lt(0).sum()) if pd.api.types.is_numeric_dtype(df[name]) else None}
        for name, group, definition in rows
    ])
    summary["negative"] = summary["negative"].astype("Int64")
    return summary


def numeric_profile(df, cols):
    """Distribution of the numeric day features."""
    profile = df[cols].describe(percentiles=[0.25, 0.5, 0.75]).T.round(2)
    return profile.rename_axis("feature").reset_index()


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    raw = read_years(folder, columns=cols_to_read)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    df = add_covid_features(add_election_features(add_time_features(prepare(raw))))
    df = binarize(discretize(df))
    assert len(df) == len(raw), "rows must never be dropped"

    summary = features_summary(df)
    profile = numeric_profile(df, ["ditet_publikim_hapje", "kohezgjatja_e_tenderit", "ditet_nga_zgjedhjet"])
    covid = pd.crosstab(df["year"], df["periudha_covid"])
    by_month = pd.crosstab(df["year"], df["muaji_publikimit"])
    duration_bins = discretization_comparison(df["kohezgjatja_e_tenderit"], len(DURATION_LABELS),
                                              DURATION_BINS, DURATION_LABELS)
    election_bins = pd.crosstab(df["year"], df["afersia_me_zgjedhjet"])
    binaries = binary_summary(df)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "features_summary.csv", index=False)
    profile.to_csv(OUT_DIR / "features_profile.csv", index=False)
    covid.to_csv(OUT_DIR / "covid_periods_by_year.csv")
    by_month.to_csv(OUT_DIR / "procedures_by_month.csv")
    duration_bins.to_csv(OUT_DIR / "discretization_duration.csv", index=False)
    election_bins.to_csv(OUT_DIR / "election_proximity_by_year.csv")
    binaries.to_csv(OUT_DIR / "binary_summary.csv", index=False)
    df.to_csv(PROCESSED_DIR / "time_features.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 70):
        print(summary.to_string(index=False))
        print("\nDay features:")
        print(profile.to_string(index=False))
        print("\nCOVID periods by year:")
        print(covid.to_string())
        print("\nProcedures by publication month:")
        print(by_month.to_string())
        print("\nDiscretization of kohezgjatja_e_tenderit:")
        print(duration_bins.to_string(index=False))
        print("\nElection proximity by year:")
        print(election_bins.to_string())
        print("\nBinary features:")
        print(binaries.to_string(index=False))


if __name__ == "__main__":
    main()
