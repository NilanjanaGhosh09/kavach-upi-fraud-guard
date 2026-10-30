import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

# 1. Read the practice payments
data = pd.read_csv("payments.csv")

features = [
    "amount",
    "hour",
    "receiver_age_days",
    "is_collect_request",
    "txns_last_10min",
    "new_device",
    "distance_from_home",
]

X = data[features]
y = data["is_fraud"]

# 2. Keep some payments aside for a test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=1, stratify=y
)

# 3. Teach the guard using ONLY normal payments
normal_only = X_train[y_train == 0]
model = IsolationForest(n_estimators=200, random_state=1)
model.fit(normal_only)

# 4. Work out how to turn strangeness into a 0 to 100 score
train_strange = -model.score_samples(normal_only)
low = np.percentile(train_strange, 50)
high = np.percentile(train_strange, 99.5)

def risk_score(rows):
    strange = -model.score_samples(rows)
    score = (strange - low) / (high - low) * 100
    return np.clip(score, 0, 100)

# 5. Test the guard on payments it has never seen
scores = risk_score(X_test)

def decide(s):
    if s < 40:
        return "allow"
    elif s <= 75:
        return "review"
    return "block"

decisions = pd.Series([decide(s) for s in scores], index=X_test.index)

print("----- RESULTS -----")
print("Normal payments in test:", int((y_test == 0).sum()))
print("Fraud payments in test:", int((y_test == 1).sum()))
print()
print("What the guard decided for NORMAL payments:")
print(decisions[y_test == 0].value_counts())
print()
print("What the guard decided for FRAUD payments:")
print(decisions[y_test == 1].value_counts())

# 6. Save the trained guard
joblib.dump({"model": model, "low": low, "high": high, "features": features}, "guard.pkl")
print()
print("Guard saved in file: guard.pkl")