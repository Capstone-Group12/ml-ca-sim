# models.py
from enum import Enum
from typing import List
from pydantic import BaseModel, validator

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

    @validator("mlModels")
    def non_empty_mlmodels(cls, v):
        if not v:
            raise ValueError("mlModels must be a non-empty array")
        return v

# If you want a top-level list type alias
from typing import Sequence
AttackList = Sequence[Attack]
