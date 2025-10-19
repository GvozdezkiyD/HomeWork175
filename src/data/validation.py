"""
Валидация данных через Pandera (универсальный стиль).
Проверяем train и test, сохраняем отчёты в data/expectations/.
При нарушениях завершаем скрипт кодом 1 (для CI).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check


# Схема в стиле DataFrameSchema — работает в любых версиях Pandera
SCHEMA = pa.DataFrameSchema(
    {
        "limit_bal": Column(float, Check.ge(0), nullable=False, coerce=True),
        "age": Column(int, [Check.ge(18), Check.le(100)], nullable=False, coerce=True),
        "target": Column(int, Check.isin([0, 1]), nullable=False, coerce=True),
    },
    strict=False,   # допускаем лишние колонки
)


def validate_csv(csv_path: Path, out_json: Path) -> bool:
    df = pd.read_csv(csv_path)
    result = {"file": csv_path.name, "success": True, "errors": []}

    try:
        SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        result["success"] = False
        # failure_cases есть во всех версиях Pandera
        result["errors"] = exc.failure_cases.to_dict(orient="records")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result["success"]


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    exp_dir = ROOT / "data" / "expectations"

    ok_train = validate_csv(ROOT / "data" / "processed" / "train.csv", exp_dir / "validation_train.json")
    ok_test = validate_csv(ROOT / "data" / "processed" / "test.csv", exp_dir / "validation_test.json")

    if not (ok_train and ok_test):
        print("Найдены нарушения правил качества данных (см. data/expectations/*.json).")
        raise SystemExit(1)

    print("Валидация пройдена.")
