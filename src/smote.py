"""
smote.py
--------
A minimal, dependency-light implementation of SMOTE (Synthetic Minority
Over-sampling Technique), as referenced in the project's Discussion Post
for handling class imbalance in DLP alert data.

Why a custom implementation instead of importing `imbalanced-learn`?
This keeps the project runnable in restricted/offline environments
(e.g., CI sandboxes without internet access) while still demonstrating
the SMOTE algorithm explicitly for grading/review purposes. If
`imbalanced-learn` is installed, train.py will prefer it automatically
(see train.py's import block) since it is a more robust, widely-used
implementation for production use; this module is the fallback.

Algorithm (Chawla et al., 2002):
    For each minority-class sample, find its k nearest minority-class
    neighbors and generate synthetic samples along the line segments
    connecting the sample to randomly chosen neighbors.
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors


def smote_oversample(X: np.ndarray, y: np.ndarray, k_neighbors: int = 5,
                      random_state: int = 42, target_ratio: float = 1.0):
    """
    Oversamples the minority class in (X, y) using SMOTE.

    Args:
        X: feature matrix (n_samples, n_features), numeric/dense (e.g.,
           output of a fitted ColumnTransformer's .transform()).
        y: binary labels (0 = majority/low-risk, 1 = minority/high-risk).
        k_neighbors: number of nearest neighbors considered per sample.
        random_state: reproducibility seed.
        target_ratio: desired minority:majority ratio after oversampling.
            1.0 = fully balanced classes. 0.5 = minority becomes half
            the size of the majority class.

    Returns:
        X_resampled, y_resampled (np.ndarray)
    """
    rng = np.random.default_rng(random_state)

    X = np.asarray(X)
    y = np.asarray(y)

    classes, counts = np.unique(y, return_counts=True)
    minority_class = classes[np.argmin(counts)]
    majority_count = counts.max()
    minority_count = counts.min()

    n_to_generate = int(majority_count * target_ratio) - minority_count
    if n_to_generate <= 0:
        return X, y  # already balanced enough

    X_minority = X[y == minority_class]

    k = min(k_neighbors, len(X_minority) - 1)
    if k < 1:
        raise ValueError(
            "Not enough minority-class samples to run SMOTE. "
            "Need at least 2 minority samples."
        )

    nn = NearestNeighbors(n_neighbors=k + 1)  # +1 because a point is its own neighbor
    nn.fit(X_minority)
    _, neighbor_idx = nn.kneighbors(X_minority)

    synthetic_samples = []
    for _ in range(n_to_generate):
        i = rng.integers(0, len(X_minority))
        # Pick one of the k real neighbors (skip index 0, which is self)
        neighbor_choice = rng.integers(1, k + 1)
        j = neighbor_idx[i, neighbor_choice]

        gap = rng.random()
        synthetic_point = X_minority[i] + gap * (X_minority[j] - X_minority[i])
        synthetic_samples.append(synthetic_point)

    X_synthetic = np.vstack(synthetic_samples)
    y_synthetic = np.full(len(X_synthetic), minority_class)

    X_resampled = np.vstack([X, X_synthetic])
    y_resampled = np.concatenate([y, y_synthetic])

    # Shuffle so synthetic samples aren't all appended at the end
    shuffle_idx = rng.permutation(len(X_resampled))
    return X_resampled[shuffle_idx], y_resampled[shuffle_idx]
