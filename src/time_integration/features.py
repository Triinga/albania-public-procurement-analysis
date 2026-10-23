"""Temporal, election and COVID features of the time columns (2016-2025).

Builds on the cleaned dates (see cleaning) with missing values filled (see
missing_values), so the gaps in days are never negative.
Discretization and binarization of these features are a separate step.

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
    assert len(df) == len(raw), "rows must never be dropped"

    summary = features_summary(df)
    profile = numeric_profile(df, ["ditet_publikim_hapje", "kohezgjatja_e_tenderit", "ditet_nga_zgjedhjet"])
    covid = pd.crosstab(df["year"], df["periudha_covid"])
    by_month = pd.crosstab(df["year"], df["muaji_publikimit"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_DIR / "features_summary.csv", index=False)
    profile.to_csv(OUT_DIR / "features_profile.csv", index=False)
    covid.to_csv(OUT_DIR / "covid_periods_by_year.csv")
    by_month.to_csv(OUT_DIR / "procedures_by_month.csv")
    df.to_csv(PROCESSED_DIR / "time_features.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20, "display.max_colwidth", 70):
        print(summary.to_string(index=False))
        print("\nDay features:")
        print(profile.to_string(index=False))
        print("\nCOVID periods by year:")
        print(covid.to_string())
        print("\nProcedures by publication month:")
        print(by_month.to_string())


if __name__ == "__main__":
    main()
