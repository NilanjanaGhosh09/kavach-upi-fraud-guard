import csv
import os
import time
from datetime import datetime

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Kavach")

# Load the trained guard once, when the door opens
saved = joblib.load("guard.pkl")
model = saved["model"]
low = saved["low"]
high = saved["high"]
features = saved["features"]

# The manager's desk: risky payments wait here for a human
cases = []


class Payment(BaseModel):
    amount: float
    hour: int
    receiver_age_days: int
    is_collect_request: int
    txns_last_10min: int
    new_device: int
    distance_from_home: float


def decide(score):
    if score < 40:
        return "allow"
    elif score <= 75:
        return "review"
    return "block"


def find_reasons(p):
    reasons = []
    if p.amount > 5000:
        reasons.append("Amount is very large")
    if p.hour <= 4 or p.hour >= 23:
        reasons.append("Payment at an unusual night hour")
    if p.receiver_age_days < 10:
        reasons.append("Receiver account is brand new")
    if p.is_collect_request == 1:
        reasons.append("This is a collect request (someone asking for money)")
    if p.txns_last_10min >= 3:
        reasons.append("Many payments in the last 10 minutes")
    if p.new_device == 1:
        reasons.append("Payment from a new device")
    if p.distance_from_home > 100:
        reasons.append("Far away from the usual location")
    return reasons


def save_feedback(case):
    # Remember what the human decided, so we can teach the guard later
    new_file = not os.path.exists("decisions.csv")
    with open("decisions.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(features + ["risk_score", "human_decision"])
        writer.writerow(
            [case["payment"][k] for k in features]
            + [case["risk_score"], case["status"]]
        )


@app.get("/")
def home():
    return {"message": "Kavach is guarding"}


@app.post("/score")
def score_payment(p: Payment):
    start = time.time()
    row = pd.DataFrame([p.model_dump()])[features]
    strange = -model.score_samples(row)[0]
    risk = (strange - low) / (high - low) * 100
    risk = max(0.0, min(100.0, float(risk)))
    decision = decide(risk)
    reasons = find_reasons(p)

    result = {
        "risk_score": round(risk, 1),
        "decision": decision,
        "reasons": reasons,
    }

    if decision != "allow":
        case = {
            "id": len(cases) + 1,
            "time": datetime.now().strftime("%H:%M:%S"),
            "payment": p.model_dump(),
            "risk_score": round(risk, 1),
            "decision": decision,
            "reasons": reasons,
            "status": "PENDING",
        }
        cases.append(case)
        print(f"ALERT: case {case['id']} is {decision.upper()} (risk {case['risk_score']})")
        result["case_id"] = case["id"]

    result["latency_ms"] = round((time.time() - start) * 1000, 1)
    return result


@app.get("/queue")
def get_queue():
    return cases


@app.post("/decide/{case_id}/{action}")
def decide_case(case_id: int, action: str):
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be approve or reject")
    for case in cases:
        if case["id"] == case_id:
            case["status"] = "APPROVED" if action == "approve" else "REJECTED"
            save_feedback(case)
            return case
    raise HTTPException(status_code=404, detail="case not found")
DASHBOARD = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kavach Dashboard</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f1f5fb;
    color: #17365d;
}
header {
    background: linear-gradient(120deg, #073568, #1262a5);
    color: white;
    padding: 24px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.brand { display: flex; align-items: center; gap: 14px; }
.shield {
    background: white;
    color: #07539a;
    padding: 10px;
    border-radius: 10px;
    font-size: 30px;
}
h1 { margin: 0; font-size: 30px; }
.subtitle { margin-top: 7px; color: #dceaff; }
main { max-width: 1500px; margin: 25px auto; padding: 0 20px; }
.layout {
    display: grid;
    grid-template-columns: minmax(0, 3fr) minmax(230px, 1fr);
    gap: 20px;
}
.card {
    background: white;
    border: 1px solid #e1e9f4;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 3px 12px #17365d0b;
}
.actions { display: flex; flex-wrap: wrap; gap: 10px; }
button {
    border: none;
    border-radius: 7px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
}
.blue { background: #0868d9; color: white; }
.ok { background: #198754; color: white; }
.bad { background: #dc3545; color: white; }
button:hover { filter: brightness(.92); }
#msg {
    margin: 18px 0 0;
    padding: 13px;
    background: #edf3fb;
    border-radius: 8px;
    font-weight: bold;
}
h2 { font-size: 21px; margin: 0 0 17px; }
h3 { margin-top: 0; font-size: 18px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: white; font-size: 13px; }
th {
    background: #eaf2fc;
    color: #17365d;
    text-align: left;
    white-space: nowrap;
}
th, td {
    padding: 11px 9px;
    border-bottom: 1px solid #e4ebf4;
    vertical-align: top;
}
tr:hover td { background: #f8fbff; }
.tag {
    display: inline-block;
    padding: 5px 8px;
    border-radius: 6px;
    font-weight: bold;
    white-space: nowrap;
}
.allow, .approved { background: #d9f5e4; color: #14753d; }
.block, .rejected { background: #ffe1e1; color: #b42323; }
.review { background: #fff0c2; color: #986500; }
.pending { background: #e4edff; color: #2259a5; }
.reason { min-width: 190px; line-height: 1.5; }
.info-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid #edf1f7;
    font-size: 14px;
}
.legend { margin: 14px 0; font-size: 14px; }
footer { text-align: center; color: #657995; padding: 10px 20px 25px; }
@media (max-width: 850px) {
    .layout { grid-template-columns: 1fr; }
    header { padding: 20px; }
    h1 { font-size: 25px; }
    main { padding: 0 12px; }
    .card { padding: 14px; }
}
</style>
</head>
<body>
<header>
    <div class="brand">
        <div class="shield">✓</div>
        <div>
            <h1>Kavach</h1>
            <div class="subtitle">Smarter Guard for Safer Payments</div>
        </div>
    </div>
    <div>Fraud Detection Dashboard</div>
</header>

<main>
<div class="layout">
<section>
    <div class="card">
        <div class="actions">
            <button class="blue" onclick="send('normal')">Send normal payment</button>
            <button class="blue" onclick="send('scam')">Send scam payment</button>
        </div>
        <p id="msg">Ready to check a test payment.</p>
    </div>

    <div class="card">
        <h2>Recent Transactions</h2>
        <div class="table-wrap">
        <table>
            <thead>
            <tr>
                <th>ID</th><th>Time</th><th>Amount</th><th>Risk</th>
                <th>Guard said</th><th>Reasons</th><th>Status</th><th>Your decision</th>
            </tr>
            </thead>
            <tbody id="rows"></tbody>
        </table>
        </div>
    </div>
</section>

<aside>
    <div class="card">
        <h3>Model Information</h3>
        <div class="info-row"><span>Model</span><strong>Isolation Forest</strong></div>
        <div class="info-row"><span>Training data</span><strong>payments.csv</strong></div>
        <div class="info-row"><span>Review process</span><strong>Human decision</strong></div>
    </div>

    <div class="card">
        <h3>Decision Legend</h3>
        <div class="legend"><span class="tag allow">ALLOW</span> Low risk</div>
        <div class="legend"><span class="tag review">REVIEW</span> Needs review</div>
        <div class="legend"><span class="tag block">BLOCK</span> High risk</div>
        <div class="legend"><span class="tag approved">APPROVED</span> Approved by reviewer</div>
        <div class="legend"><span class="tag rejected">REJECTED</span> Rejected by reviewer</div>
    </div>

    <div class="card">
        <h3>About Kavach</h3>
        <p>Detecting fraud. Enabling trust.</p>
        <p>Educational payment-fraud detection prototype.</p>
    </div>
</aside>
</div>
</main>

<footer>Kavach Payment Review System | Educational Prototype</footer>

<script>
const normalPayment = {
    amount: 500, hour: 14, receiver_age_days: 800,
    is_collect_request: 0, txns_last_10min: 0,
    new_device: 0, distance_from_home: 3
};

const scamPayment = {
    amount: 25000, hour: 3, receiver_age_days: 1,
    is_collect_request: 1, txns_last_10min: 6,
    new_device: 1, distance_from_home: 300
};

async function send(kind) {
    try {
        const body = kind === 'scam' ? scamPayment : normalPayment;
        const r = await fetch('/score', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body)
        });
        const d = await r.json();
        if (!r.ok) throw new Error(d.detail || 'Payment failed');

        const decision = String(d.decision).toUpperCase();
        const msg = document.getElementById('msg');
        msg.innerText = 'Guard said: ' + decision + ' (risk ' + d.risk_score + ')';
        msg.style.background = decision === 'ALLOW' ? '#e8f7ee' :
            decision === 'BLOCK' ? '#ffe8e8' : '#fff3cd';
        msg.style.color = decision === 'ALLOW' ? '#13733c' :
            decision === 'BLOCK' ? '#b42323' : '#986500';
        await load();
    } catch (e) {
        document.getElementById('msg').innerText = 'Error: ' + e.message;
    }
}

async function decideCase(id, action) {
    try {
        const r = await fetch('/decide/' + id + '/' + action, {method: 'POST'});
        if (!r.ok) throw new Error('Could not save the decision');
        await load();
    } catch (e) {
        alert(e.message);
    }
}

async function load() {
    try {
        const r = await fetch('/queue');
        const list = await r.json();
        let html = '';

        list.slice().reverse().forEach(c => {
            const decision = String(c.decision).toLowerCase();
            const status = String(c.status).toLowerCase();
            const buttons = c.status === 'PENDING'
                ? `<button class="ok" onclick="decideCase(${c.id}, 'approve')">Approve</button>
                   <button class="bad" onclick="decideCase(${c.id}, 'reject')">Reject</button>`
                : '-';

            html += `<tr>
                <td>${c.id}</td>
                <td>${c.time}</td>
                <td>${c.payment.amount}</td>
                <td>${c.risk_score}</td>
                <td><span class="tag ${decision}">${decision.toUpperCase()}</span></td>
                <td class="reason">${(c.reasons || []).join('<br>') || 'No warning signs'}</td>
                <td><span class="tag ${status}">${c.status}</span></td>
                <td>${buttons}</td>
            </tr>`;
        });

        document.getElementById('rows').innerHTML = html ||
            '<tr><td colspan="8">No flagged transactions yet. Send a test payment.</td></tr>';
    } catch (e) {
        document.getElementById('rows').innerHTML =
            '<tr><td colspan="8">Could not load transactions. Check the server.</td></tr>';
    }
}

load();
setInterval(load, 3000);
</script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return DASHBOARD