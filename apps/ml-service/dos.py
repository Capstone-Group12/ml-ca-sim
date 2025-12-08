from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

BASE_DIR = Path(__file__).parent
SOURCE_FILE = BASE_DIR / "data" / "DoS-HTTP_Flood.pcap_Flow.csv"

# let's limit the features to only those that will help detect DoS traffic
DETECTION_FEATURES = [
    "Dst Port",
    "Flow Packets/s",
    "Flow Bytes/s",
    "Total Fwd Packet",
    "Flow Duration",
    "Total Length of Fwd Packet",
    "Src IP",
    "Dst IP",
]

MODEL_PARAMS = {
    "n_estimators": 35,
    "random_state": 42,
    "class_weight": "balanced",
    "n_jobs": 1,
}

def load_dataframe(source_file: Path = SOURCE_FILE) -> pd.DataFrame:
    # we skip caching here and just read the source CSV directly
    if not source_file.exists():
        raise FileNotFoundError(f"Training data not found at {source_file}")

    return pd.read_csv(source_file)

# this function encodes text and string values into integer values for the random forest model
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # replace infinity with very large finite number (1 billion)
    #   -> we need to do this since CICFlowMeter computed them
    #   -> they break the model, so let's switch them
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].replace([np.inf, -np.inf], 1000000000)

    if "Dst Port" in df.columns:
        df["Dst Port"] = pd.to_numeric(df["Dst Port"], errors="coerce").fillna(0).astype(int)

        df["is_ssh"] = (df["Dst Port"] == 22).astype(int)
        df["is_telnet"] = (df["Dst Port"] == 23).astype(int)
        df["is_web"] = df["Dst Port"].isin([80, 443, 8080, 8443]).astype(int)

    if "Src IP" in df.columns:
        le = LabelEncoder()
        df["src_ip_code"] = le.fit_transform(df["Src IP"].fillna("0.0.0.0").astype(str))

    if "Dst IP" in df.columns:
        le = LabelEncoder()
        df["dst_ip_code"] = le.fit_transform(df["Dst IP"].fillna("0.0.0.0").astype(str))

    # remove any remaining features with string values, we've already converted what we need
    #   -> precaution more than anything
    string_cols = df.select_dtypes(include=["object", "string"]).columns
    if len(string_cols) > 0:
        df = df.drop(columns=string_cols, errors="ignore")

    # fill any missing values to avoid analysis complications
    df = df.fillna(0)

    return df


# this function helps highlight abnormalities in traffic that point towards DoS attacks
#   -> it's a multi-phase scoring system as to focus on all characteristics
#   -> rule-scoring = a blanket/catch-all the obvious signs - a quick and easy check sort of thing
#   -> extreme value scoriing =
def find_dos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 4 obvious signs of dos attacks
    #   -> http port access (i.e., port 80/443)
    #   -> very high packet rates (flooding, > 25 packets/s)
    #   -> very large byte rates (bandwidth flood)
    #   -> request flood in 1 flow (> 500 packets)
    rule_score = (
        df["Dst Port"].isin([80, 443, 8080, 8443]).astype(int) * 25
        + (df["Flow Packets/s"] > 25).astype(int) * 25
        + (df["Flow Bytes/s"] > 100).astype(int) * 25
        + (df["Total Fwd Packet"] > 500).astype(int) * 25
    )

    # now, instead of z-score, we're going to manually look very huge outliers
    #   -> since DoS attacks are so abnormal, we can do this without stats
    #   -> plus this is a lot faster than calculating z-score for 900k rows
    extreme_vals_score = (
        (df["Flow Packets/s"] > 75).astype(int) * 30            # super high packet rate!
        + (df["Flow Bytes/s"] > 1000).astype(int) * 30          # super high bandwidth!
    )

    # now, we check if a single source is very active, with large volumes of traffic
    source_intensity_score = 0
    if "Src IP" in df.columns:
        ip_counts = df["Src IP"].value_counts()
        avg_packets = df["Total Fwd Packet"].mean()

        # Estimated total packets = count * average
        estimated_totals = ip_counts * avg_packets

        df["estimated_source_total"] = df["Src IP"].map(estimated_totals).fillna(0)

        # Single source sending >100 estimated packets = DoS
        source_intensity_score = np.where(df["estimated_source_total"] > 100, 30, 0)


    # now, we look for patterns within the http requests and the flow
    #   -> before, we were looking for single obvious signs
    #   -> this part looks for the patterns together
    #   -> e.g., large uploads, request flood
    http_pattern_score = 0

    # pattern 1 - very large HTTP POST flood (large uploads)
    if "Total Length of Fwd Packet" in df.columns:
        post_flood = (
            df["Dst Port"].isin([80, 443, 8080, 8443])
            & (df["Total Length of Fwd Packet"] > 50000)
        )
        http_pattern_score += np.where(post_flood, 20, 0)

    # pattern 2 - very fast HTTP requests (request flood)
    if all(col in df.columns for col in ["Flow Duration", "Total Fwd Packet"]):
        request_flood = (
            df["Dst Port"].isin([80, 443, 8080, 8443])
            & (df["Flow Duration"] < 50000)
            & (df["Total Fwd Packet"] > 100)                # so, so, so many requests!!
            & (df["Flow Packets/s"] > 50)
        )
        http_pattern_score += np.where(request_flood, 20, 0)

    # now, we combine all the scores
    df["dos_score"] = rule_score + extreme_vals_score + source_intensity_score + http_pattern_score

    # with our scores, we're going to calculate thresholds based on the data we collected
    #   -> calculate average of all trafic
    #   -> find any variation (i.e., std. dev.)
    #   -> create a threshold to flag attacks as DoS
    mean_score = df["dos_score"].mean()
    std_score = df["dos_score"].std()
    threshold = mean_score + (2.0 * std_score)

    df["is_dos"] = df["dos_score"] > threshold
    df["dos_confidence"] = df["dos_score"] / 100  # 0-1 confidence score

    df["dos_classification"] = "Normal"
    df.loc[df["dos_confidence"] > 0.6, "dos_classification"] = "Suspiciously High Traffic"
    df.loc[df["dos_confidence"] > 0.8, "dos_classification"] = "Likely DoS"
    df.loc[df["dos_confidence"] > 0.9, "dos_classification"] = "Confirmed DoS Attack"

    return df

def train_dos_model() -> Tuple[RandomForestClassifier, Dict[str, float]]:
    df = load_dataframe()
    df_scored = find_dos(df)

    missing = [c for c in DETECTION_FEATURES if c not in df_scored.columns]
    if missing:
        raise ValueError(f"Missing expected columns for training: {missing}")

    X = df_scored[DETECTION_FEATURES]
    y = df_scored["is_dos"].astype(int)

    X_encoded = engineer_features(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42, stratify=y
    )

    rf = RandomForestClassifier(**MODEL_PARAMS)
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
    }

    return rf, metrics

def predict_dos(
    model: RandomForestClassifier, sample: Dict[str, object]
) -> Tuple[int, float | None]:
    sample_frame = pd.DataFrame([sample], columns=DETECTION_FEATURES)
    sample_frame = engineer_features(sample_frame)

    label = int(model.predict(sample_frame)[0])

    if hasattr(model, "predict_proba"):
        proba = float(model.predict_proba(sample_frame)[0][1])
    else:
        proba = None

    return label, proba

if __name__ == "__main__":
    model, metrics = train_dos_model()
    print("\nRANDOM FOREST MODEL RESULTS:")
    print(f"Accuracy (correct identification of attacks):  {metrics['accuracy']:.4f}")
    print(f"Precision (accurate predictions v.s. false alarms): {metrics['precision']:.4f}")
    print(f"Recall (how many attacks are caught):    {metrics['recall']:.4f}")
    print(f"F1-Score (balance of precission and recall):  {metrics['f1_score']:.4f}")