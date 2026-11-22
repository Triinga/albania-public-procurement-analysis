"""Generic outlier detection: IQR and a robust (MAD-based) z-score.

Both methods work on any numeric series, optionally on the log scale (for
right-skewed amounts), and can be applied globally or within groups (e.g. per
`Lloji_i_procedures`) so that large-but-normal procedures are not flagged just
because they differ in scale from small ones.

Detecting an outlier and deciding what it means are kept separate: `detect`
only flags; `outlier_status` sorts the flagged rows into "gabim" (a known
impossible value), "e vërtetë por e rrallë" (both methods agree it stands out,
but nothing says it is impossible) or "e pasigurt" (the two methods disagree).
Nothing is changed or removed; callers add the flags as new columns.
"""
import numpy as np
import pandas as pd

IQR_MULTIPLIER = 1.5
MAD_THRESHOLD = 3.5  # standard cutoff for the modified z-score (Iglewicz & Hoaglin)

ERROR = "gabim"
RARE = "e vërtetë por e rrallë"
UNCERTAIN = "e pasigurt"
STATUS_CATEGORIES = [ERROR, RARE, UNCERTAIN]


def log_safe(series):
    """log(1 + x); NaN where x is negative (log is undefined there)."""
    return np.log1p(series.where(series >= 0))


def iqr_outliers(series, multiplier=IQR_MULTIPLIER):
    """True where a value is outside [Q1 - k*IQR, Q3 + k*IQR]."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - multiplier * iqr, q3 + multiplier * iqr
    return (series < lower) | (series > upper)


def mad_zscore_outliers(series, threshold=MAD_THRESHOLD):
    """True where the modified z-score (median/MAD) exceeds `threshold`."""
    median = series.median()
    mad = (series - median).abs().median()
    if not mad:
        return pd.Series(False, index=series.index)
    modified_z = 0.6745 * (series - median) / mad
    return modified_z.abs() > threshold


def detect(df, column, group=None, log=False):
    """IQR and MAD outlier flags for `column`, globally and (if given) within `group`.

    Returns a DataFrame indexed like `df`, with boolean columns
    `outlier_iqr_global`, `outlier_mad_global` and, when `group` is given,
    `outlier_iqr_group`, `outlier_mad_group`. Missing values are never flagged.
    """
    values = log_safe(df[column]) if log else df[column]
    flags = pd.DataFrame(index=df.index)
    flags["outlier_iqr_global"] = iqr_outliers(values).fillna(False)
    flags["outlier_mad_global"] = mad_zscore_outliers(values).fillna(False)
    if group is not None:
        flags["outlier_iqr_group"] = values.groupby(df[group]).transform(iqr_outliers).fillna(False)
        flags["outlier_mad_group"] = values.groupby(df[group]).transform(mad_zscore_outliers).fillna(False)
    return flags


def is_outlier(flags):
    """True if any method (global or group) flagged the row."""
    return flags.any(axis=1)


def methods_agree(flags):
    """True where the IQR and MAD flags agree (both methods flagged the same columns)."""
    iqr_cols = [c for c in flags.columns if c.startswith("outlier_iqr")]
    mad_cols = [c for c in flags.columns if c.startswith("outlier_mad")]
    return flags[iqr_cols].any(axis=1) == flags[mad_cols].any(axis=1)


def outlier_status(flags, is_impossible):
    """Classify every row flagged by `detect` as "gabim", "e vërtetë por e rrallë"
    or "e pasigurt"; rows not flagged at all get `NaN`.

    `is_impossible` marks values that are impossible regardless of the
    statistical flag (e.g. a negative duration), and always wins.
    """
    outlier = is_outlier(flags)
    agree = methods_agree(flags)
    status = pd.Series(pd.NA, index=flags.index, dtype="object")
    status[outlier & agree] = RARE
    status[outlier & ~agree] = UNCERTAIN
    status[is_impossible.reindex(flags.index, fill_value=False)] = ERROR
    return pd.Categorical(status, categories=STATUS_CATEGORIES)


def status_counts(status, column):
    counts = pd.Series(status).value_counts(dropna=False).reindex(STATUS_CATEGORIES + [np.nan])
    return pd.DataFrame({
        "column": column,
        "outlier_status": [c if c is not np.nan else "(nuk është përjashtues)" for c in counts.index],
        "procedures": counts.fillna(0).astype(int).values,
    })
