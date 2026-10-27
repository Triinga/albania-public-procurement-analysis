"""Missing values of the time columns (2016-2025): impute, never drop rows.

Missing opening dates are filled with the publication date plus the typical
publication -> opening delay; missing closing dates with the opening date plus
the typical opening -> closing duration. "Typical" is the median of procedures
of the same type in the same year (falling back to the same type, then to all
procedures), because deadlines depend mostly on the procedure type. The four
strategies (deletion, global median, median by year, median by type and year)
are compared in `compare_strategies`.

Only valid (non-negative) gaps are used to compute the typical values, so an
imputed date can never fall before the date it is derived from. Every imputed
value is flagged in a separate boolean column.

Usage (from the repository root):
    python -m src.time_integration.missing_values [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.data_loading import DATA_DIR, read_years
from src.common.missing import missing_by_year, missing_summary
from src.time_integration.columns import DATETIME_COLS, INPUT_COLS, PROCEDURE_TYPE

OUT_DIR = Path("reports/time_integration")
PUB, OPEN, CLOSE = "Data_e_publikimit", "Data_e_hapjes", "Data_e_mbylljes"
TIME_COLS = [PUB, OPEN, CLOSE, "Numri_i_references"]
N_SEEDS = 20
CHOSEN = "Mediana sipas llojit x vitit (e zgjedhur)"
STRATEGIES = {  # name -> grouping, from the most to the least specific
    "Mediana globale": [],
    "Mediana sipas vitit": ["year"],
    "Mediana sipas llojit": ["type"],
    CHOSEN: ["type", "year"],
}


def parse_dates(df):
    """Convert date columns from text to datetime."""
    for col in DATETIME_COLS:
        df[col] = pd.to_datetime(df[col], format="%d.%m.%Y", errors="coerce")
    return df


def groups(df):
    """Grouping columns: the procedure type (whitespace normalized) and the year."""
    return {"type": df[PROCEDURE_TYPE].str.split().str.join(" "), "year": df["year"]}


def typical_gap(gap, keys):
    """Median of the known gaps (>= 0) per group; falls back to coarser groups, then to all."""
    gap = gap.where(gap >= 0)
    typical = pd.Series(float("nan"), index=gap.index)
    for i in range(len(keys), 0, -1):
        typical = typical.fillna(gap.groupby(keys[:i]).transform("median"))
    return typical.fillna(gap.median()).round()


def fill_missing_dates(df):
    """Fill missing opening/closing dates and flag every imputed value."""
    keys = list(groups(df).values())
    df[f"{OPEN}_imputed"] = df[OPEN].isna()
    df[f"{CLOSE}_imputed"] = df[CLOSE].isna()

    open_gap = typical_gap((df[OPEN] - df[PUB]).dt.days, keys)
    df[OPEN] = df[OPEN].fillna(df[PUB] + pd.to_timedelta(open_gap, unit="D"))
    # A filled opening date can never fall after a known closing date
    too_late = df[f"{OPEN}_imputed"] & (df[OPEN] > df[CLOSE])
    df.loc[too_late, OPEN] = df.loc[too_late, CLOSE]

    # The duration is learned only from real opening dates, then applied to the filled one
    real_open = df[OPEN].where(~df[f"{OPEN}_imputed"])
    close_gap = typical_gap((df[CLOSE] - real_open).dt.days, keys)
    df[CLOSE] = df[CLOSE].fillna(df[OPEN] + pd.to_timedelta(close_gap, unit="D"))
    return df


def hidden_sample(df, known, end, seed):
    """Known rows with the same procedure-type and year mix as the missing ones."""
    g = groups(df)
    mix = df[df[end].isna()].groupby([g["type"], g["year"]]).size()
    pools = known.groupby([g["type"][known.index], g["year"][known.index]])
    parts = [pools.get_group(key).sample(n=min(n, len(pools.get_group(key))), random_state=seed)
             for key, n in mix.items() if key in pools.groups]
    return pd.concat(parts).index


def compare_strategies(df, n_seeds=N_SEEDS):
    """Deletion vs. the median strategies, for each date that can be missing.

    The medians are tested on known dates: known values with the same procedure
    type and year mix as the missing ones are hidden, filled from the rest and
    compared with the truth. Repeated over several seeds.
    """
    g = groups(df)
    rows = []
    for start, end in [(PUB, OPEN), (OPEN, CLOSE)]:
        missing = int(df[end].isna().sum())
        gap = (df[end] - df[start]).dt.days
        known = df[gap.ge(0)]
        rows.append({"column": end, "strategy": "Fshirja e rreshtave", "rows_lost": missing,
                     "tested": None, "mean_error_days": None, "exact_pct": None, "within_3_days_pct": None})

        errors = {name: [] for name in STRATEGIES}
        for seed in range(n_seeds):
            hidden = hidden_sample(df, known, end, seed)
            visible = gap.drop(hidden).reindex(gap.index)
            for name, keys in STRATEGIES.items():
                guess = typical_gap(visible, [g[k] for k in keys])
                errors[name].append((gap[hidden] - guess[hidden]).abs())
        for name, err in errors.items():
            err = pd.concat(err)
            rows.append({"column": end, "strategy": name, "rows_lost": 0, "tested": len(err) // n_seeds,
                         "mean_error_days": round(err.mean(), 2),
                         "exact_pct": round(err.eq(0).mean() * 100, 1),
                         "within_3_days_pct": round(err.le(3).mean() * 100, 1)})
    return pd.DataFrame(rows)


def imputation_report(df, before):
    """Before/after missing counts and the number of imputed values per column."""
    after = missing_summary(df, TIME_COLS)
    report = before.merge(after, on="column", suffixes=("_before", "_after"))
    report["imputed"] = report["column"].map({
        OPEN: int(df[f"{OPEN}_imputed"].sum()),
        CLOSE: int(df[f"{CLOSE}_imputed"].sum()),
    }).fillna(0).astype(int)
    return report


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    cols_to_read = INPUT_COLS
    df = parse_dates(read_years(folder, columns=cols_to_read))
    rows_before = len(df)

    before = missing_summary(df, TIME_COLS)
    by_year = missing_by_year(df, [OPEN, CLOSE])
    strategies = compare_strategies(df)

    df = fill_missing_dates(df)
    assert len(df) == rows_before, "rows must never be dropped"

    report = imputation_report(df, before)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUT_DIR / "missing_summary.csv", index=False)
    by_year.to_csv(OUT_DIR / "missing_by_year.csv")
    strategies.to_csv(OUT_DIR / "missing_strategies.csv", index=False)

    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(report.to_string(index=False))
        print()
        print(by_year.to_string())
        print(f"\nStrategies (imputations tested on hidden known dates, {N_SEEDS} seeds):")
        print(strategies.to_string(index=False))
    print(f"\nRows: {rows_before:,} -> {len(df):,} (none dropped)")
    print(f"Opening before publication after fill: {(df[OPEN] < df[PUB]).sum():,} "
          "(pre-existing logical issue, fixed in cleaning)")
    print(f"Closing before opening among imputed: "
          f"{((df[CLOSE] < df[OPEN]) & df[f'{CLOSE}_imputed']).sum():,}")


if __name__ == "__main__":
    main()
