"""Sampling of the procurement data (2016-2025): simple random vs stratified by year.

Both samples take the same fraction with the same seed and are compared with
the full data on the time features. The stratified sample keeps the share of
every year exactly, so no year is over- or under-represented.

Usage (from the repository root):
    python -m src.time_integration.sampling [csv_folder]

If no folder is given, data/raw/ is used. The sample is saved to
data/processed/ (not tracked by git); the tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.sampling import SEED, compare_distributions, max_deviation, random_sample, stratified_sample
from src.time_integration.columns import COLUMNS
from src.time_integration.features import build_features

OUT_DIR = Path("reports/time_integration")
PROCESSED_DIR = Path("data/processed")
FRACTION = 0.10
STRATA = {
    "stratified_by_year": ["year"],
    "stratified_by_year_election": ["year", "afersia_me_zgjedhjet"],
}
CHOSEN = "stratified_by_year_election"
N_SEEDS = 50
COMPARED =["year", "periudha_covid", "afersia_me_zgjedhjet", "kategoria_e_kohezgjatjes",
            "periudhe_parazgjedhore", "publikim_ne_dhjetor", "hapje_mbyllje_e_njejta_dite"]
NUMERIC = ["kohezgjatja_e_tenderit", "ditet_publikim_hapje", "ditet_nga_zgjedhjet"]


def draw_samples(df, seed=SEED):
    return {
        "random": random_sample(df, FRACTION, seed),
        **{name: stratified_sample(df, by, FRACTION, seed) for name, by in STRATA.items()},
    }


def stability(df):
    """Average and worst largest gap over many seeds, so one lucky seed decides nothing."""
    runs = []
    for seed in range(N_SEEDS):
        samples = draw_samples(df, seed)
        runs.append(max_deviation(compare_distributions(df, samples, COMPARED), samples))
    runs = pd.concat(runs)
    grouped = runs.groupby(level="variable", sort=False)
    return pd.concat({"mean": grouped.mean(), "worst": grouped.max()}, axis=1).round(2)


def numeric_comparison(population, samples):
    """Mean and median of the day features in the population and each sample."""
    frames = {"population": population, **samples}
    rows = []
    for col in NUMERIC:
        for stat in ["mean", "median"]:
            rows.append({"variable": col, "statistic": stat,
                         **{name: round(getattr(f[col], stat)(), 2) for name, f in frames.items()}})
    return pd.DataFrame(rows)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    cols_to_read = [c for c in COLUMNS if c != "viti"]
    df = build_features(read_years(folder, columns=cols_to_read))
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(df):,} procedures\n")

    samples = draw_samples(df)
    comparison = compare_distributions(df, samples, COMPARED)
    numeric = numeric_comparison(df, samples)
    deviation = stability(df)
    sizes = pd.DataFrame([{"sample": "population", "rows": len(df)}]
                         + [{"sample": name, "rows": len(s)} for name, s in samples.items()])
    sizes["fraction_pct"] = (sizes["rows"] / len(df) * 100).round(2)
    sizes["seed"] = SEED

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sizes.to_csv(OUT_DIR / "sampling_sizes.csv", index=False)
    comparison.to_csv(OUT_DIR / "sampling_comparison.csv", index=False)
    deviation.to_csv(OUT_DIR / "sampling_max_deviation.csv")
    numeric.to_csv(OUT_DIR / "sampling_numeric.csv", index=False)
    samples[CHOSEN].to_csv(PROCESSED_DIR / "time_sample.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(sizes.to_string(index=False))
        print(f"\nLargest gap from the population over {N_SEEDS} seeds (percentage points):")
        print(deviation.to_string())
        print("\nDay features:")
        print(numeric.to_string(index=False))
        print("\nShare by year (%):")
        print(comparison[comparison["variable"] == "year"].to_string(index=False))


if __name__ == "__main__":
    main()
