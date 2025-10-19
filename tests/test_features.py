from __future__ import annotations

import pandas as pd

from src.features.build_features import add_domain_features


def test_add_domain_features_creates_age_bin():
    df = pd.DataFrame({"age": [20, 30, 40], "limit_bal": [10000, 20000, 30000]})
    out = add_domain_features(df)
    assert "age_bin" in out.columns
    assert out["age_bin"].notna().all()
