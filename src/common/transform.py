"""Generic transformations for numeric columns: log, normalization and standardization."""
import numpy as np
import pandas as pd


def log_transform(series):
    """log(1 + x) for non-negative values; reduces the long right tail of amounts."""
    if (series.dropna() < 0).any():
        raise ValueError(f"{series.name}: log transform needs non-negative values")
    return np.log1p(series)


def min_max(series):
    """Scale to the range [0, 1]."""
    lo, hi = series.min(), series.max()
    return (series - lo) / (hi - lo)


def z_score(series):
    """Standardize to mean 0 and standard deviation 1."""
    return (series - series.mean()) / series.std()


def describe_transformation(before, after, column, transformation):
    """Range and shape of a column before and after one transformation."""
    return {
        "column": column,
        "transformation": transformation,
        "min_before": round(before.min(), 4),
        "max_before": round(before.max(), 4),
        "skew_before": round(before.skew(), 2),
        "min_after": round(after.min(), 4),
        "max_after": round(after.max(), 4),
        "mean_after": round(after.mean(), 4),
        "std_after": round(after.std(), 4),
        "skew_after": round(after.skew(), 2),
    }


def summarize(rows):
    return pd.DataFrame(rows)
