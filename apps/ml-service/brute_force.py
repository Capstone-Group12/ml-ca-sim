import pandas as pd
import numpy as np
import feather
import os

from scipy import stats

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# cache the dataframe file so every time the program is run, pd doesn't spend time re-reading it
cache_brute = "cached_data.feather"
source_file = "data/DictionaryBruteForce.pcap_Flow.csv"

use_cache = False
if os.path.exists(cache_brute) and os.path.exists(source_file):
    cache_time = os.path.getmtime(cache_brute)
    source_time = os.path.getmtime(source_file)
    
    if source_time > cache_time:
        print("Source file is newer - reloading data ...")
        use_cache = False

    else:
        use_cache = True
        print("Cache is up to date - loading from cache ...")

if use_cache:
    df = feather.read_dataframe(cache_brute)
    print("Dataframe loaded from cache.")

else:
    df = pd.read_csv(source_file)
    feather.write_dataframe(df, cache_brute) 
    print("Dataframe read from source and cached.")


# this function encodes text and string values into integer values for the random forest model
def engineer_features(df):
    df = df.copy()
    
    # encode port features to integer values
    if 'Dst Port' in df.columns:
        df['Dst Port'] = pd.to_numeric(df['Dst Port'], errors='coerce').fillna(0).astype(int)
        
        df['is_ssh'] = (df['Dst Port'] == 22).astype(int)
        df['is_telnet'] = (df['Dst Port'] == 23).astype(int)
        df['is_auth_port'] = df['Dst Port'].isin([21, 22, 23, 3389]).astype(int)    # where passwords are checked!
    
    # encode ips to integer values
    if 'Src IP' in df.columns:
        le = LabelEncoder()
        df['Src IP int'] = le.fit_transform(df['Src IP'].fillna('0.0.0.0'))
    
    if 'Dst IP' in df.columns:
        le = LabelEncoder()
        df['Dst IP int'] = le.fit_transform(df['Dst IP'].fillna('0.0.0.0'))
    
    # remove any leftover string values, we already have the ones we need
    df = df.select_dtypes(include=[np.number])
    
    # fill any missing values to avoid analysis complications
    df = df.fillna(0)

    return df

# this function edits the dataframe to make supervised learning possible
#   essentially, we find aspects of the data that would indicate if its a port scan
#   based on these characteristics, we add a col w/ values 0 or 1
#   0 => normal behaviour, 1 => possible port probing

# here, we are detecting brute force attacks based on:
#   - common ports taken advantage of
#       -> 21 (FTP)
#       -> 22 (SSH)
#       -> 23 (Telnet)
#       -> 3389 (RDP)
def find_brute_force(df):
    df = df.copy()
    
    # 4 obvious signs of brute force attacks
    #   -> authentication port access (i.e., port 22/23)
    #   -> automated attempts (> 10 packets/s)
    #   -> quick, failed attempt (< 2 s)
    #   -> small packets - usually username/password exchange (< 10 packets)
    rule_score = (
        df['Dst Port'].isin([22, 23]).astype(int) * 25 +
        (df['Flow Packets/s'] > 10).astype(int) * 25 +
        (df['Flow Duration'] < 2000000).astype(int) * 25 +
        (df['Total Fwd Packet'] < 10).astype(int) * 25
    )
    
    # now, we use z-score to find statistically unusual packet rates
    #   -> i.e., unusual = suspicious!!
    packet_rate_z = np.abs(stats.zscore(df['Flow Packets/s'].fillna(0)))
    anomaly_score = np.where(packet_rate_z > 2, 25, 0)
    
    # now, if timestamp is available, check for regular intervals
    #   -> intervals could indicate bot-like behaviour
    #   -> e.g., human won't wait 5s every single time for a password attempt
    time_score = 0
    if 'Timestamp' in df.columns:
        try:
            df['timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True)                # convert timestamp to DateTime obj
            df['time_diff'] = df.groupby('Src IP')['timestamp'].diff().dt.total_seconds()   # calculate time between attacks from same ip
            
            time_std = df.groupby('Src IP')['time_diff'].transform('std').fillna(10)        # calculate std. dev. of the time differences
            time_score = np.where(time_std < 1.0, 20, 0)                                    # suspicious (bot-like) behaviour gets higher score

        except Exception as e:
            print("Timestamp failing! Temporal analysis not available.")
    
    # now, protocol analysis will reveal if there's a high ratio of failed attempts to successful
    # the pattern of a brute force attack will include:
    #   -> many failed attempts (SYN flags)
    #   -> few successful attempts (ACK flags)
    # so that's what we look for!
    protocol_score = 0
    if 'SYN Flag Count' in df.columns and 'ACK Flag Count' in df.columns:
        syn_ack_ratio = df['SYN Flag Count'] / (df['ACK Flag Count'] + 1)
        protocol_score = np.where(syn_ack_ratio > 2, 15, 0)
    
    # now, we combine all the scores
    df['bf_score'] = rule_score + anomaly_score + time_score + protocol_score
    
    # with our scores, we're going to calculate thresholds based on the data we collected
    #   -> calculate average of all trafic
    #   -> find any variation (i.e., std. dev.)
    #   -> create a threshold to flag attacks as brute force
    mean_score = df['bf_score'].mean()
    std_score = df['bf_score'].std()
    threshold = mean_score + (1.5 * std_score)  
    
    df['is_bruteforce'] = df['bf_score'] > threshold    
    df['confidence'] = df['bf_score'] / 100  # 0-1 confidence score
    
    # not all brute force attacks will be the same
    # with a confidence scaling, you can better detect the more dangerous attacks 
    df['classification'] = 'Normal'
    df.loc[df['confidence'] > 0.5, 'classification'] = 'Suspicious'
    df.loc[df['confidence'] > 0.7, 'classification'] = 'Likely Brute-force'
    df.loc[df['confidence'] > 0.9, 'classification'] = 'Confirmed Brute-force Attack'
    
    return df

df_scored = find_brute_force(df)

X = df_scored.drop(columns=['is_bruteforce', 'bf_score', 'confidence', 'classification'])
y = df_scored['is_bruteforce'].astype(int)

X_encoded = engineer_features(X)

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42, stratify=y)

rf = RandomForestClassifier(
    n_estimators=150, 
    random_state=42, 
    min_samples_split=2,
    class_weight='balanced'
)

rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)
y_pred_proba = rf.predict_proba(X_test)[:, 1]

print("\nRANDOM FOREST MODEL RESULTS:")
print(f"ACCURACY (correct identification of attacks): {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall: {recall_score(y_test, y_pred):.4f}")
print(f"F1-Score: {f1_score(y_test, y_pred):.4f}")