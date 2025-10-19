"""
Минимальный feature engineering под скоринг:
- биннинг возраста
- отношение задолженностей к лимиту
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "age" in df.columns:
        df["age_bin"] = pd.cut(df["age"], bins=[17, 25, 35, 50, 65, 120], labels=False, include_lowest=True).astype("Int64")

    # пример: отношение сумм счетов к лимиту (если колонки присутствуют)
    bill_cols = [c for c in df.columns if c.startswith("bill_amt")]
    for col in bill_cols:
        ratio_col = f"{col}_to_limit"
        df[ratio_col] = np.where(df["limit_bal"] > 0, df[col] / df["limit_bal"], 0.0)

    return df
