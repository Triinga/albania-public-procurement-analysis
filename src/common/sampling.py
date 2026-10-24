"""Generic sampling helpers, reusable for any dataset."""
import pandas as pd

SEED = 42  # fixed so every run gives the same sample


def random_sample(df, frac, seed=SEED):
    """Simple random sample without replacement."""
    return df.sample(frac=frac, random_state=seed)


def stratified_sample(df, by, frac, seed=SEED):
    """The same fraction from every group, so the group shares are kept."""
    return df.groupby(by, group_keys=False, observed=True).sample(frac=frac, random_state=seed)


def compare_distributions(population, samples, columns):
    """Share (%) of every value in the population and in each sample."""
    rows = []
    for col in columns:
        shares = {"population": population[col].value_counts(normalize=True, sort=False)}
        shares.update({name: s[col].value_counts(normalize=True, sort=False) for name, s in samples.items()})
        table = (pd.DataFrame(shares).fillna(0) * 100).round(2)
        rows.append(table.rename_axis("value").reset_index().assign(variable=col))
    result = pd.concat(rows, ignore_index=True)
    result["value"] = result["value"].astype(str)
    return result[["variable", "value", "population", *samples]]


def max_deviation(comparison, samples):
    """Largest gap (percentage points) between a sample and the population, per variable."""
    gaps = comparison[list(samples)].sub(comparison["population"], axis=0).abs()
    return gaps.assign(variable=comparison["variable"]).groupby("variable", sort=False).max().round(2)
