import pandas as pd
import feather
import os

from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# cache the dataframe file so every time the program is run, pd doesn't spend time re-reading it
cache_port = "cached_data.feather"
source_file = "data/Recon-PortScan.csv"

use_cache = False
if os.path.exists(cache_port) and os.path.exists(source_file):
    cache_time = os.path.getmtime(cache_port)
    source_time = os.path.getmtime(source_file)
    
    if source_time > cache_time:
        print("Source file is newer - reloading data ...")
        use_cache = False

    else:
        use_cache = True
        print("Cache is up to date - loading from cache ...")


if use_cache:
    df = feather.read_dataframe(cache_port)
    print("Dataframe loaded from cache.")

else:
    df = pd.read_csv(source_file)
    feather.write_dataframe(df, cache_port) 
    print("Dataframe read from source and cached.")


# this function edits the dataframe to make supervised learning possible
#   essentially, we find aspects of the data that would indicate if its a port scan
#   based on these characteristics, we add a col w/ values 0 or 1
#   0 => normal behaviour, 1 => possible port probing
def find_port_prob(df):

    ip_stats = df.groupby('src_ip').agg({
        'dst_port' : 'nunique',
        'inter_arrival_time' : 'mean',
        'stream_1_count' : 'max'
    })

    port_prob_ips = ip_stats[
        (ip_stats['dst_port'] > 10) &                   # trying several different ports
        (
            (ip_stats['inter_arrival_time'] > 1.0) |    # fast connection attempts, <1s
            (ip_stats['stream_1_count'] > 10)           # many attempts in a short period
        )
    ].index

    df['is_port_prob'] = df['src_ip'].isin(port_prob_ips).astype(int)

    return df

# apply labeling for supervised learning
df = find_port_prob(df)

# let's limit the features to only those that will help detect port probing
detection_features = [
    'dst_port',             # which port is being accessed
    'src_port',             # source port
    'inter_arrival_time',   # time between packets
    'stream_1_count',       # recent activity
    'l4_tcp',               # is this TCP traffic?
    'l4_udp'                # is this UDP traffic?
]

# fill missing values w/ 0 to avoid complications w/ analysis
X = df[detection_features].fillna(0)
y = df['is_port_prob']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

xg = XGBClassifier(
    n_estimators=250,
    max_depth=9,
    learning_rate=0.1,
    random_state=42
)

xg.fit(X_train, y_train)

print("\nXGBOOST MODEL RESULTS:")
print(f"Training accuracy: {(xg.score(X_train, y_train) * 100):.4f}%")
print(f"Testing accuracy:  {(xg.score(X_test, y_test) * 100):.4f}%")
