"""Generic cleaning helpers, reusable for any group of columns."""
import pandas as pd

JOINT_SEPARATOR = " | "  # separator for joint winners (consortia) after cleaning


def clean_text(series):
    """Trim whitespace, collapse inner spaces and join multi-line cells with ' | '.

    Multi-line cells hold several entries (e.g. the members of a consortium).
    """
    def _clean(value):
        if pd.isna(value):
            return value
        parts = [" ".join(p.split()) for p in str(value).splitlines()]
        parts = [p for p in parts if p]
        return JOINT_SEPARATOR.join(parts) if parts else pd.NA

    return series.map(_clean)


def po_jo_to_bool(series):
    """Convert the APP 'Po'/'Jo' answers to a nullable boolean."""
    return series.map({"Po": True, "Jo": False}).astype("boolean")


def canonical_by_key(names, keys):
    """Give every key one name: the most frequent spelling used with that key.

    Rows without a key keep their own name.
    """
    frame = pd.DataFrame({"key": keys, "name": names}).dropna()
    most_frequent = (frame.groupby(["key", "name"]).size()
                     .sort_values(ascending=False)
                     .reset_index()
                     .drop_duplicates("key")
                     .set_index("key")["name"])
    return keys.map(most_frequent).fillna(names)
