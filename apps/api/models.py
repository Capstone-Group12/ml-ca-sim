from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Sequence

from pydantic import BaseModel, Field, field_validator

class AttackType(str, Enum):
    DDOS = "DDOS"
    XSS_SQL_INJECTION = "XSS_SQL_INJECTION"
    SLOWLORIS = "SLOWLORIS"
    BRUTE_FORCE = "BRUTE_FORCE"
    DNS_POISONING = "DNS_POISONING"

class MLModel(str, Enum):
    LSTM = "LSTM"
    RANDOM_FOREST = "RANDOM_FOREST"
    NAIVE_BAYES = "NAIVE_BAYES"
    LOGISTIC_REGRESSION = "LOGISTIC_REGRESSION"
    DECISION_TREE = "DECISION_TREE"
    ISOLATION_FOREST = "ISOLATION_FOREST"
    GRADIENT_BOOSTING = "GRADIENT_BOOSTING"
    SMALL_NN = "SMALL_NN"

class Attack(BaseModel):
    name: AttackType
    mlModels: List[MLModel]

    @field_validator("mlModels")
    @classmethod
    def non_empty_mlmodels(cls, v: List[MLModel]) -> List[MLModel]:
        if not v:
            raise ValueError("mlModels must be a non-empty array")
        return v

class ScanRow(BaseModel):
    timestamp: datetime
    target: str
    port: int
    state: str
    banner: str | None = ""

class ScanCSV(BaseModel):
    csv_text: str = Field(..., description="CSV with columns: timestamp,target,port,state,banner")

AttackList = Sequence[Attack]
