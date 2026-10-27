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


def compare_categorical_strategies(values):
    """Compare deletion, mode imputation and keeping categorical missing values.

    The report makes row loss and mode distortion explicit so that a treatment
    strategy can be selected without changing the input data.
    """
    values = values.astype("string").replace(r"^\s*$", pd.NA, regex=True)
    observed = values.dropna()
    total_rows = len(values)
    missing_before = int(values.isna().sum())

    if observed.empty:
        mode_value = pd.NA
        mode_rows = 0
    else:
        counts = observed.value_counts()
        highest_count = int(counts.max())
        mode_value = sorted(counts[counts.eq(highest_count)].index.tolist())[0]
        mode_rows = highest_count

    def result_row(
        strategy,
        rows_kept,
        rows_removed,
        missing_after,
        imputed_rows,
        mode_rows_after,
        distinct_after,
        effect,
        recommended=False,
    ):
        return {
            "strategy": strategy,
            "input_rows": total_rows,
            "missing_before": missing_before,
            "missing_pct_before": round(missing_before * 100 / total_rows, 2) if total_rows else 0.0,
            "rows_kept": rows_kept,
            "rows_removed": rows_removed,
            "missing_after": missing_after,
            "imputed_rows": imputed_rows,
            "mode_value": mode_value,
            "mode_rows_after": mode_rows_after,
            "mode_pct_of_rows_kept": round(mode_rows_after * 100 / rows_kept, 2) if rows_kept else 0.0,
            "distinct_non_missing_after": distinct_after,
            "recommended": recommended,
            "effect": effect,
        }

    rows = [
        result_row(
            "Deletion (drop missing rows)",
            len(observed),
            missing_before,
            0,
            0,
            mode_rows,
            int(observed.nunique()),
            "Removes every row without a recorded source value",
        )
    ]

    if pd.isna(mode_value):
        rows.append(result_row(
            "Mode imputation",
            total_rows,
            0,
            missing_before,
            0,
            0,
            0,
            "Unavailable because the column has no observed mode",
        ))
    else:
        rows.append(result_row(
            "Mode imputation",
            total_rows,
            0,
            0,
            missing_before,
            mode_rows + missing_before,
            int(observed.nunique()),
            "Assigns the most frequent observed value to every missing row",
        ))

    rows.append(result_row(
        "Keep missing values",
        total_rows,
        0,
        missing_before,
        0,
        mode_rows,
        int(observed.nunique()),
        "Preserves all rows and does not invent a source value",
        recommended=True,
    ))
    return pd.DataFrame(rows)
