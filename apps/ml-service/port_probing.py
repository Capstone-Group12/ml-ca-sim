from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import feather
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).parent

# cache the dataframe file so every time the program is run, pd doesn't spend time re-reading it
CACHE_FILE = BASE_DIR / "cached_data.feather"
SOURCE_FILE = BASE_DIR / "data" / "Recon-PortScan.csv"

# let's limit the features to only those that will help detect port probing
DETECTION_FEATURES = [
    "dst_port",             # which port is being accessed
    "src_port",             # source port
    "inter_arrival_time",   # time between packets
    "stream_1_count",       # recent activity
    "l4_tcp",               # is this TCP traffic?
    "l4_udp"                # is this UDP traffic?
]

MODEL_PARAMS = {
    "n_estimators": 250,
    "max_depth": 9,
    "learning_rate": 0.1,
    "random_state": 42,
}

def load_dataframe(
    cache_file: Path = CACHE_FILE,
    source_file: Path = SOURCE_FILE
) -> pd.DataFrame:
    use_cache = False

    if cache_file.exists() and source_file.exists():
        if source_file.stat().st_mtime > cache_file.stat().st_mtime:
            use_cache = False
        else:
            use_cache = True

    if use_cache:
        df = feather.read_dataframe(cache_file)
    elif source_file.exists():
        df = pd.read_csv(source_file)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        feather.write_dataframe(df, cache_file)
    else:
        raise FileNotFoundError(f"Training data not found at {source_file}")

    return df

# this function edits the dataframe to make supervised learning possible
#   essentially, we find aspects of the data that would indicate if its a port scan
#   based on these characteristics, we add a col w/ values 0 or 1
#   0 => normal behaviour, 1 => possible port probing
def find_port_prob(df: pd.DataFrame) -> pd.DataFrame:
    ip_stats = df.groupby("src_ip").agg(
        {"dst_port": "nunique", "inter_arrival_time": "mean", "stream_1_count": "max"}
    )

    port_prob_ips = ip_stats[
        (ip_stats["dst_port"] > 10)                   # trying several different ports
        & (
            (ip_stats["inter_arrival_time"] > 1.0)    # fast connection attempts, <1s
            | (ip_stats["stream_1_count"] > 10)       # many attempts in a short period
        )
    ].index

    df = df.copy()
    df["is_port_prob"] = df["src_ip"].isin(port_prob_ips).astype(int)

    return df

def train_port_probing_model() -> Tuple[XGBClassifier, Dict[str, float]]:
    df = load_dataframe()

    # apply labeling for supervised learning
    df = find_port_prob(df)

    # fill missing values w/ 0 to avoid complications w/ analysis
    X = df[DETECTION_FEATURES].fillna(0)
    y = df["is_port_prob"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBClassifier(**MODEL_PARAMS)
    model.fit(X_train, y_train)

    metrics = {
        "train_accuracy": float(model.score(X_train, y_train)),
        "test_accuracy": float(model.score(X_test, y_test)),
    }

    return model, metrics

def predict_port_probing(
    model: XGBClassifier, sample: Dict[str, float]
) -> Tuple[int, float | None]:
    sample_frame = pd.DataFrame([sample], columns=DETECTION_FEATURES).fillna(0)
    label = int(model.predict(sample_frame)[0])

    if hasattr(model, "predict_proba"):
        proba = float(model.predict_proba(sample_frame)[0][1])
    else:
        proba = None

    return label, proba

if __name__ == "__main__":
    model, metrics = train_port_probing_model()
    print("\nXGBOOST MODEL RESULTS:")
    print(f"Training accuracy: {(metrics['train_accuracy'] * 100):.4f}%")
    print(f"Testing accuracy:  {(metrics['test_accuracy'] * 100):.4f}%")
