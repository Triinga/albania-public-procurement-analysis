"""Principal Component Analysis with numpy (no extra dependency)."""
import numpy as np
import pandas as pd


def pca(standardized):
    """PCA of an already standardized DataFrame (no missing values).

    Returns the explained variance per component, the loadings (weight of each
    feature in each component) and the component scores of every row.
    """
    X = standardized.to_numpy(dtype=float)
    _, singular_values, vt = np.linalg.svd(X - X.mean(axis=0), full_matrices=False)
    variance = singular_values ** 2 / (len(X) - 1)
    names = [f"PC{i + 1}" for i in range(len(variance))]

    pct = variance / variance.sum() * 100
    explained = pd.DataFrame({
        "component": names,
        "eigenvalue": variance.round(4),
        "explained_variance_pct": pct.round(2),
        "cumulative_pct": pct.cumsum().round(2),
    })

    loadings = pd.DataFrame(vt.T, index=standardized.columns, columns=names).round(4)
    scores = pd.DataFrame((X - X.mean(axis=0)) @ vt.T, index=standardized.index, columns=names)
    return explained, loadings, scores


def components_for(explained, threshold_pct):
    """Smallest number of components whose cumulative variance reaches the threshold."""
    return int((explained["cumulative_pct"] < threshold_pct).sum() + 1)
