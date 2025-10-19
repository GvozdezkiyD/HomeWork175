"""
Готовит данные для обучения/тестирования из UCI Default of Credit Card Clients.
Задачи:
1) загрузка CSV из data/raw/
2) базовая очистка/переименование
3) разбиение на train/test и сохранение в data/processed/
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Приводим имена к snake_case, убираем пробелы и точки
    mapping = {
        "default.payment.next.month": "target",
        "PAY_0": "PAY_1",  # выравниваем распространённое несоответствие в колонках
    }
    df = df.rename(columns=mapping)
    df.columns = [c.strip().lower().replace(" ", "_").replace(".", "_") for c in df.columns]
    return df


def prepare_dataset(raw_csv: Path, out_dir: Path, test_size: float = 0.2, random_state: int = 42) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(raw_csv)
    df = _rename_columns(df)

    # Явно приводим типы базовых признаков
    int_like = ["sex", "education", "marriage", "age"]
    for c in int_like:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    # Удаляем явные дубликаты
    df = df.drop_duplicates()

    # Целевая метка
    if "target" not in df.columns:
        raise ValueError("В датасете нет столбца 'target' (default.payment.next.month).")

    # Разбиение
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state, stratify=df["target"])

    train_df.to_csv(out_dir / "train.csv", index=False)
    test_df.to_csv(out_dir / "test.csv", index=False)


if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[2]
    prepare_dataset(
        raw_csv=ROOT / "data" / "raw" / "UCI_Credit_Card.csv",
        out_dir=ROOT / "data" / "processed",
    )
