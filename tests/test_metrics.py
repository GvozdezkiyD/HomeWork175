from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score


def test_roc_auc_in_range():
    y_true = np.array([0, 1, 0, 1])
    y_prob = np.array([0.1, 0.9, 0.2, 0.8])
    score = roc_auc_score(y_true, y_prob)
    assert 0.5 <= score <= 1.0
