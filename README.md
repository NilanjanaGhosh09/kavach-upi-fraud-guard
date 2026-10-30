# Kavach: Real-Time UPI Scam and Payment Fraud Guard

Kavach is a small fraud guard for digital payments. It looks at each payment and gives it a risk score from 0 to 100, then decides: allow, review or block. Risky payments go to a screen where a human presses Approve or Reject.

## What it does

- Learns what normal payments look like using an Isolation Forest model
- Scores each payment in milliseconds
- Gives plain-language reasons (large amount, night hour, brand-new receiver, collect request, and more)
- Shows risky payments on a live review dashboard with Approve and Reject buttons
- Saves every human decision in decisions.csv, so the guard can be retrained later

## Tools used

Python, FastAPI, scikit-learn, pandas, joblib

## How to run it

    pip install pandas numpy scikit-learn fastapi uvicorn
    python make_data.py
    python train_model.py
    uvicorn main:app --reload

Then open 127.0.0.1:8000/dashboard in your browser.

## Files

- make_data.py: makes 10,000 practice payments (200 are fraud)
- train_model.py: trains the guard and saves guard.pkl
- main.py: the guard API and the review dashboard
- test_speed.py: measures how fast the guard answers

## Note

The practice payments are made up. This is a learning project and not a real bank system.


## Results

- Tested on a hold-out set of 60 fraud cases: all 60 were blocked (100% fraud recall)
- Only about 14% of all payments were sent for human review, so analyst workload stays low
- Every payment gets a risk score from 0 to 100 and a decision: ALLOW, REVIEW or BLOCK

## How it works

1. `make_data.py` creates 10,000 practice payments
2. `train_model.py` trains an Isolation Forest model and saves it as `guard.pkl`
3. `main.py` runs the FastAPI service that scores each payment
4. Risky payments appear on the review dashboard, where a human taps Approve or Reject
5. Every decision is saved in `decisions.csv` for future retraining
