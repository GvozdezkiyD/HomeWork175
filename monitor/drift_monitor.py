"""
Простейший расчёт PSI для одной числовой фичи по бинам.
Сохраняет JSON-отчёт в reports/drift/.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def calc_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    # дискретизация совместной шкалой
    quantiles = np.linspace(0, 1, bins + 1)
    cut_points = np.quantile(expected, quantiles)
    cut_points[0], cut_points[-1] = -np.inf, np.inf

    e_counts, _ = np.histogram(expected, bins=cut_points)
    a_counts, _ = np.histogram(actual, bins=cut_points)

    e_perc = e_counts / max(e_counts.sum(), 1)
    a_perc = a_counts / max(a_counts.sum(), 1)

    # защищаемся от нулей
    e_perc = np.where(e_perc == 0, 1e-6, e_perc)
    a_perc = np.where(a_perc == 0, 1e-6, a_perc)

    psi = np.sum((a_perc - e_perc) * np.log(a_perc / e_perc))
    return float(psi)


def run_psi(train_csv: Path, new_csv: Path, feature: str, out_json: Path) -> None:
    train = pd.read_csv(train_csv)
    new = pd.read_csv(new_csv)

    assert feature in train.columns and feature in new.columns, "Нет нужной фичи."

    psi = calc_psi(train[feature].values, new[feature].values, bins=10)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"feature": feature, "psi": psi}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[1]
    run_psi(
        train_csv=ROOT / "data" / "processed" / "train.csv",
        new_csv=ROOT / "data" / "processed" / "test.csv",
        feature="age",
        out_json=ROOT / "reports" / "drift" / "psi_age.json",
    )
