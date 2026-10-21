"""Generic helpers for discretization and binarization."""
import pandas as pd


def compare_discretizations(values, n_bins):
    """Rows per bin for equal-width and equal-frequency (quantile) binning."""
    width = pd.cut(values, n_bins).value_counts(sort=False)
    freq = pd.qcut(values, n_bins).value_counts(sort=False)
    return pd.DataFrame({
        "bin": range(1, n_bins + 1),
        "equal_width_interval": width.index.astype(str),
        "equal_width_rows": width.values,
        "equal_frequency_interval": freq.index.astype(str),
        "equal_frequency_rows": freq.values,
    })


def discretize_by_quantiles(values, labels):
    """Equal-frequency bins with readable labels; missing values stay missing."""
    return pd.qcut(values, len(labels), labels=labels)


def to_binary(series):
    """Boolean-like column -> 0/1 integers (missing stays missing)."""
    return series.astype("boolean").astype("Int8")
