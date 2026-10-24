"""Generic aggregation helpers."""
import pandas as pd


def aggregate(df, by, metrics):
    """Group `df` by `by` and compute named metrics.

    `metrics` maps an output name to (column, function), as in pandas named
    aggregation. The number of procedures in each group is always included.
    """
    grouped = df.groupby(by, observed=True, dropna=False)
    out = grouped.agg(**metrics)
    out.insert(0, "procedures", grouped.size())
    return out.reset_index()


def share(part, whole):
    """Percentage of `part` in `whole`, rounded to 2 decimals."""
    return (part / whole * 100).round(2)
