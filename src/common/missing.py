"""Generic helpers for identifying missing values and comparing treatment strategies."""
import pandas as pd


def missing_summary(df, columns):
    """Number and percentage of missing values per column."""
    return pd.DataFrame({
        "missing": df[list(columns)].isna().sum(),
        "missing_pct": (df[list(columns)].isna().mean() * 100).round(2),
    }).rename_axis("column").reset_index()


def missing_by_year(df, columns):
    """Percentage of missing values per year for the given columns."""
    m = df.groupby("year")[list(columns)].apply(lambda g: g.isna().mean() * 100).round(1)
    m.insert(0, "procedures", df.groupby("year").size())
    return m


def missing_by_group(df, column, group):
    """Share of missing values of `column` inside each value of `group`."""
    g = df.groupby(group, dropna=False)[column]
    return pd.DataFrame({
        "procedures": g.size(),
        "missing": g.apply(lambda s: s.isna().sum()),
        "missing_pct": (g.apply(lambda s: s.isna().mean()) * 100).round(1),
    }).reset_index()


def compare_numeric_strategies(values, groups):
    """Apply several strategies for missing numeric values and compare the results.

    Strategies: listwise deletion, overall median, median within `groups`,
    and keeping NaN with a missing-indicator flag.
    """
    strategies = {
        "Original (with NaN)": values,
        "Deletion (drop rows)": values.dropna(),
        "Median imputation": values.fillna(values.median()),
        "Median by group": values.fillna(values.groupby(groups).transform("median")),
        "Keep NaN + missing flag": values,
    }
    rows = []
    for name, s in strategies.items():
        rows.append({
            "strategy": name,
            "rows_kept": int(len(s)),
            "still_missing": int(s.isna().sum()),
            "median": round(s.median(), 2),
            "mean": round(s.mean(), 2),
        })
    return pd.DataFrame(rows)
