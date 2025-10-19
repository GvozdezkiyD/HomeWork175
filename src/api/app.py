"""
Простой REST API для /predict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, field_validator

APP = FastAPI(title="Credit Default Prediction API")
MODEL = joblib.load(Path(__file__).resolve().parents[2] / "models" / "credit_default_model.pkl")


class ClientData(BaseModel):
    limit_bal: float
    sex: int
    education: int
    marriage: int
    age: int
    pay_1: int
    bill_amt1: float
    pay_amt1: float

    @field_validator("sex", "education", "marriage", "age", "pay_1")
    @classmethod
    def _ints(cls, v: int) -> int:
        return int(v)


@APP.get("/")
def read_root() -> Dict[str, str]:
    return {"message": "Credit Default Prediction API is alive!"}


@APP.post("/predict")
def predict(data: ClientData):
    # Преобразуем в DataFrame строго с теми колонками, что ждала модель
    row = pd.DataFrame([data.model_dump()])
    prob = float(MODEL.predict_proba(row)[0][1])
    pred = int(prob >= 0.5)
    return {"default_prediction": pred, "default_probability": prob}
