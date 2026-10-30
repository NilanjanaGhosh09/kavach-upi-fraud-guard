import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

def make_normal(n):
    return pd.DataFrame({
        "amount": rng.gamma(2.0, 400, n).round(2),
        "hour": rng.choice(range(7, 23), n),
        "receiver_age_days": rng.integers(60, 2000, n),
        "is_collect_request": rng.choice([0, 1], n, p=[0.95, 0.05]),
        "txns_last_10min": rng.choice([0, 1, 2], n, p=[0.7, 0.25, 0.05]),
        "new_device": rng.choice([0, 1], n, p=[0.97, 0.03]),
        "distance_from_home": rng.exponential(5, n).round(1),
        "is_fraud": 0,
    })

def make_fraud(n):
    return pd.DataFrame({
        "amount": rng.gamma(4.0, 3000, n).round(2),
        "hour": rng.choice([0, 1, 2, 3, 4, 23], n),
        "receiver_age_days": rng.integers(0, 10, n),
        "is_collect_request": rng.choice([0, 1], n, p=[0.3, 0.7]),
        "txns_last_10min": rng.integers(3, 12, n),
        "new_device": rng.choice([0, 1], n, p=[0.3, 0.7]),
        "distance_from_home": rng.exponential(200, n).round(1),
        "is_fraud": 1,
    })

data = pd.concat([make_normal(9800), make_fraud(200)])
data = data.sample(frac=1, random_state=1)
data.to_csv("payments.csv", index=False)

print(data.head())
print("Total payments:", len(data))
print("Fraud payments:", data["is_fraud"].sum())