"""
Generates the fictional "Riverside Community Services" casework dataset used
throughout the curriculum, plus the answer key for every checkpoint.

Everything here is made up. No real people, no real agency.

Run:  python3 data/generate.py
Uses only the Python standard library and a fixed seed, so the output is
identical every time.
"""

import csv
import json
import os
import random
from collections import defaultdict
from datetime import date, timedelta

SEED = 2026
HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(SEED)

START = date(2025, 4, 1)        # fiscal year start
DATA_END = date(2026, 8, 31)    # last day in the main services file
NEW_MONTH_START = date(2026, 9, 1)
NEW_MONTH_END = date(2026, 9, 30)

PROGRAMS = [("Housing Support", 0.32), ("Mental Health", 0.26),
            ("Youth Services", 0.22), ("Newcomer Settlement", 0.20)]
REGIONS = [("North", 0.22), ("South", 0.18), ("East", 0.20),
           ("West", 0.17), ("Central", 0.23)]
AGE_BANDS = [("16-24", 0.22), ("25-34", 0.24), ("35-44", 0.20),
             ("45-54", 0.16), ("55-64", 0.11), ("65+", 0.07)]

WORKERS = [
    ("W-01", "Amara Okafor", "Community Help Worker"),
    ("W-02", "Ben Tremblay", "Community Help Worker"),
    ("W-03", "Chloe Nguyen", "Community Help Worker"),
    ("W-04", "Dev Patel", "Community Help Worker"),
    ("W-05", "Elena Rossi", "Community Help Worker"),
    ("W-06", "Farid Haddad", "Community Help Worker"),
    ("W-07", "Grace Kim", "Case Manager"),
    ("W-08", "Hugo Lefebvre", "Case Manager"),
    ("W-09", "Isla MacDonald", "Case Manager"),
    ("W-10", "Jonah Whitehorse", "Case Manager"),
    ("W-11", "Keisha Brown", "Counsellor"),
    ("W-12", "Liam O'Connor", "Counsellor"),
    ("W-13", "Maya Singh", "Housing Navigator"),
    ("W-14", "Noah Fischer", "Housing Navigator"),
]

# code, description, category, unit cost (per service), who delivers it
SERVICE_CODES = [
    ("CN01", "Case note / file review", "Admin", 0.00, "assigned"),
    ("PH01", "Phone check-in", "Outreach", 0.00, "assigned"),
    ("RF01", "Referral to partner agency", "Admin", 0.00, "assigned"),
    ("HV01", "Home visit", "Outreach", 85.00, "Community Help Worker"),
    ("CH02", "Community accompaniment", "Outreach", 60.00, "Community Help Worker"),
    ("CO01", "Individual counselling session", "Counselling", 120.00, "Counsellor"),
    ("CO02", "Group counselling session", "Counselling", 45.00, "Counsellor"),
    ("TR01", "Monthly transit pass", "Transportation", 128.75, "assigned"),
    ("TR02", "Taxi / ride to appointment", "Transportation", 32.50, "assigned"),
    ("FA01", "Emergency grocery card", "Financial Assistance", 75.00, "assigned"),
    ("FA02", "Rent supplement", "Financial Assistance", 450.00, "Housing Navigator"),
    ("FA03", "Utility arrears payment", "Financial Assistance", 220.00, "Housing Navigator"),
    ("ID01", "ID replacement fee", "Admin", 35.00, "assigned"),
    ("IN01", "Interpreter (per session)", "Support", 55.00, "assigned"),
]

# How likely each code is, per program (relative weights)
CODE_WEIGHTS = {
    "Housing Support":     {"CN01": 18, "PH01": 14, "RF01": 4, "HV01": 14, "CH02": 6, "CO01": 2, "CO02": 1,
                            "TR01": 3, "TR02": 5, "FA01": 6, "FA02": 8, "FA03": 6, "ID01": 3, "IN01": 2},
    "Mental Health":       {"CN01": 18, "PH01": 14, "RF01": 4, "HV01": 8, "CH02": 6, "CO01": 16, "CO02": 8,
                            "TR01": 2, "TR02": 6, "FA01": 3, "FA02": 1, "FA03": 1, "ID01": 1, "IN01": 2},
    "Youth Services":      {"CN01": 18, "PH01": 16, "RF01": 5, "HV01": 7, "CH02": 10, "CO01": 6, "CO02": 9,
                            "TR01": 6, "TR02": 4, "FA01": 4, "FA02": 1, "FA03": 1, "ID01": 4, "IN01": 1},
    "Newcomer Settlement": {"CN01": 18, "PH01": 12, "RF01": 8, "HV01": 8, "CH02": 9, "CO01": 2, "CO02": 3,
                            "TR01": 5, "TR02": 4, "FA01": 5, "FA02": 3, "FA03": 2, "ID01": 6, "IN01": 12},
}

N_CLIENTS = 300
N_NO_SERVICE = 12  # waitlisted clients: on the client list but no services yet


def pick(weighted):
    items, weights = zip(*weighted)
    return rng.choices(items, weights=weights, k=1)[0]


def rand_date(a, b):
    return a + timedelta(days=rng.randint(0, (b - a).days))


def money(x):
    return round(x + 1e-9, 2)


# ---------------------------------------------------------------- workers
workers_by_role = defaultdict(list)
for wid, _, role in WORKERS:
    workers_by_role[role].append(wid)
generalists = workers_by_role["Community Help Worker"] + workers_by_role["Case Manager"]

# ---------------------------------------------------------------- clients
clients = []
for i in range(1, N_CLIENTS + 1):
    cid = f"C-{i:04d}"
    program = pick(PROGRAMS)
    intake = rand_date(START, date(2026, 8, 15))
    discharge = None
    # Roughly half of clients have been discharged
    if rng.random() < 0.5:
        stay = rng.randint(30, 320)
        d = intake + timedelta(days=stay)
        if d <= DATA_END:
            discharge = d
    clients.append({
        "ClientID": cid,
        "IntakeDate": intake,
        "DischargeDate": discharge,
        "Program": program,
        "Region": pick(REGIONS),
        "AgeBand": pick(AGE_BANDS),
        "AssignedWorker": rng.choice(generalists),
    })

no_service_ids = set(c["ClientID"] for c in rng.sample(clients, N_NO_SERVICE))

code_info = {c[0]: c for c in SERVICE_CODES}
code_cost = {c[0]: c[3] for c in SERVICE_CODES}


def make_service(client, day):
    weights = CODE_WEIGHTS[client["Program"]]
    code = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
    who = code_info[code][4]
    worker = client["AssignedWorker"] if who == "assigned" else rng.choice(workers_by_role[who])
    if code in ("CN01", "RF01"):
        mins = rng.choice([10, 15, 20, 30])
    elif code == "PH01":
        mins = rng.choice([5, 10, 15, 20])
    elif code in ("CO01", "CO02"):
        mins = rng.choice([50, 60, 90])
    elif code in ("HV01", "CH02"):
        mins = rng.choice([45, 60, 90, 120])
    else:
        mins = rng.choice([15, 20, 30, 45])
    return {"ClientID": client["ClientID"], "ServiceDate": day, "ServiceCode": code,
            "WorkerID": worker, "DurationMins": mins}


def services_between(client, a, b):
    out = []
    days = (b - a).days + 1
    if days <= 0:
        return out
    # about 1.6 services a week, with some clients more intensive than others
    intensity = rng.uniform(0.6, 2.6)
    n = max(1, int(days / 7 * intensity))
    for _ in range(n):
        out.append(make_service(client, rand_date(a, b)))
    return out


services = []
for c in clients:
    if c["ClientID"] in no_service_ids:
        continue
    end = c["DischargeDate"] or DATA_END
    services.extend(services_between(c, c["IntakeDate"], end))

services.sort(key=lambda s: (s["ServiceDate"], s["ClientID"]))
for n, s in enumerate(services, 1):
    s["ServiceID"] = f"S-{n:06d}"

# New month (September 2026) for the "refresh" lesson: active clients only
new_month = []
for c in clients:
    if c["ClientID"] in no_service_ids or c["DischargeDate"] is not None:
        continue
    a = max(c["IntakeDate"], NEW_MONTH_START)
    new_month.extend(services_between(c, a, NEW_MONTH_END))
new_month.sort(key=lambda s: (s["ServiceDate"], s["ClientID"]))
for n, s in enumerate(new_month, len(services) + 1):
    s["ServiceID"] = f"S-{n:06d}"


# ---------------------------------------------------------------- messy export
def messy_rows(rows, n_dupes, n_blank, extra_rng):
    """Turn clean service rows into what a real system export looks like."""
    out = []
    blank_ids = set(s["ServiceID"] for s in extra_rng.sample(rows, n_blank))
    for s in rows:
        r = dict(s)
        code = r["ServiceCode"]
        roll = extra_rng.random()
        if r["ServiceID"] in blank_ids:
            code = ""
        elif roll < 0.04:
            code = code + " "          # trailing space
        elif roll < 0.07:
            code = code.lower()        # lower case
        elif roll < 0.08:
            code = " " + code.lower() + "  "
        r["ServiceCode"] = code
        out.append(r)
    for r in extra_rng.sample(out, n_dupes):  # exact duplicate rows (double export)
        out.insert(out.index(r) + 1, dict(r))
    return out, blank_ids


raw_services, blank_ids = messy_rows(services, 118, 37, random.Random(SEED + 1))
raw_new, blank_new = messy_rows(new_month, 9, 3, random.Random(SEED + 2))

# Clean = what Laura should end up with after week 3's three cleaning rules
clean_services = [s for s in services if s["ServiceID"] not in blank_ids]
clean_new = [s for s in new_month if s["ServiceID"] not in blank_new]


# ---------------------------------------------------------------- write CSVs
def fmt(v):
    if v is None:
        return ""
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float):
        return f"{v:.2f}"
    return v


def write_csv(name, rows, cols):
    with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([fmt(r[c]) for c in cols])


SVC_COLS = ["ServiceID", "ClientID", "ServiceDate", "ServiceCode", "WorkerID", "DurationMins"]
write_csv("clients.csv", clients,
          ["ClientID", "IntakeDate", "DischargeDate", "Program", "Region", "AgeBand", "AssignedWorker"])
write_csv("workers.csv", [dict(zip(["WorkerID", "Name", "Role"], w)) for w in WORKERS],
          ["WorkerID", "Name", "Role"])
write_csv("service_codes.csv",
          [dict(zip(["ServiceCode", "Description", "Category", "UnitCost"], c[:4])) for c in SERVICE_CODES],
          ["ServiceCode", "Description", "Category", "UnitCost"])
write_csv("services_raw.csv", raw_services, SVC_COLS)
write_csv("services_clean.csv", clean_services, SVC_COLS)
write_csv("services_2026-09.csv", raw_new, SVC_COLS)

# ---------------------------------------------------------------- answer key
client_by_id = {c["ClientID"]: c for c in clients}
worker_by_id = {w[0]: w for w in WORKERS}


def spend(rows):
    return money(sum(code_cost[s["ServiceCode"]] for s in rows))


def by(rows, keyfn):
    g = defaultdict(list)
    for s in rows:
        g[keyfn(s)].append(s)
    return g


S = clean_services
total = spend(S)
per_client = {k: spend(v) for k, v in by(S, lambda s: s["ClientID"]).items()}
per_program = {k: spend(v) for k, v in by(S, lambda s: client_by_id[s["ClientID"]]["Program"]).items()}
per_category = {k: spend(v) for k, v in by(S, lambda s: code_info[s["ServiceCode"]][2]).items()}
per_region = {k: spend(v) for k, v in by(S, lambda s: client_by_id[s["ClientID"]]["Region"]).items()}
per_month = {k: spend(v) for k, v in by(S, lambda s: s["ServiceDate"].strftime("%Y-%m")).items()}
per_worker = {k: spend(v) for k, v in by(S, lambda s: s["WorkerID"]).items()}

clients_served = len(per_client)
top_client = max(per_client.items(), key=lambda kv: kv[1])
top_program = max(per_program.items(), key=lambda kv: kv[1])
top_month = max(per_month.items(), key=lambda kv: kv[1])
top_worker = max(per_worker.items(), key=lambda kv: kv[1])

region_served = defaultdict(set)
for s in S:
    region_served[client_by_id[s["ClientID"]]["Region"]].add(s["ClientID"])
avg_by_region = {r: money(per_region[r] / len(region_served[r])) for r in per_region}
top_avg_region = max(avg_by_region.items(), key=lambda kv: kv[1])

mh_clients = [cid for cid in per_client if client_by_id[cid]["Program"] == "Mental Health"]
mh_avg = money(sum(per_client[c] for c in mh_clients) / len(mh_clients))

discharged = [c for c in clients if c["DischargeDate"]]
avg_los = round(sum((c["DischargeDate"] - c["IntakeDate"]).days for c in discharged) / len(discharged), 1)

zero_cost_pct = round(100 * sum(1 for s in S if code_cost[s["ServiceCode"]] == 0) / len(S), 1)

chw_ids = set(workers_by_role["Community Help Worker"])
chw_spend = spend([s for s in S if s["WorkerID"] in chw_ids])

ys_central = spend([s for s in S if client_by_id[s["ClientID"]]["Program"] == "Youth Services"
                    and client_by_id[s["ClientID"]]["Region"] == "Central"])

CHECK_CLIENTS = ["C-0042", "C-0117", "C-0250"]
for cid in CHECK_CLIENTS:
    assert cid in per_client, f"{cid} has no services; choose another check client"

combined = S + clean_new


def num(v, unit="", tol=0.01, note=""):
    return {"type": "number", "answer": v, "tolerance": tol, "unit": unit, "note": note}


def txt(v, accept=None, note=""):
    return {"type": "text", "answer": v, "accept": accept or [v], "note": note}


month_name = date(int(top_month[0][:4]), int(top_month[0][5:]), 1).strftime("%B %Y")

key = {
    # Week 1
    "w1-raw-rows": num(len(raw_services), "rows", 0),
    "w1-clients": num(len(clients), "clients", 0),
    # Week 2
    "w2-housing-clients": num(sum(1 for c in clients if c["Program"] == "Housing Support"), "clients", 0),
    "w2-active-clients": num(sum(1 for c in clients if c["DischargeDate"] is None), "clients", 0),
    # Week 3
    "w3-dupes-removed": num(len(raw_services) - len(services), "rows", 0),
    "w3-clean-rows": num(len(S), "rows", 0),
    # Week 4
    "w4-total-spend": num(total, "$", 0.01),
    "w4-paid-services": num(sum(1 for s in S if code_cost[s["ServiceCode"]] > 0), "services", 0),
    # Week 5
    **{f"w5-spend-{cid}": num(per_client[cid], "$") for cid in CHECK_CLIENTS},
    "w5-services-C-0042": num(sum(1 for s in S if s["ClientID"] == "C-0042"), "services", 0),
    "w5-avg-cost-per-service": num(money(total / len(S)), "$", 0.01),
    # Week 6
    "w6-top-program": txt(top_program[0]),
    "w6-top-program-spend": num(top_program[1], "$"),
    "w6-top-client": txt(top_client[0], [top_client[0], top_client[0].replace("C-", "")]),
    "w6-fa-spend": num(per_category["Financial Assistance"], "$"),
    # Week 7
    "w7-clean-rows": num(len(S), "rows", 0),
    "w7-distinct-codes": num(len(set(s["ServiceCode"] for s in S)), "codes", 0),
    # Week 8
    "w8-combined-rows": num(len(combined), "rows", 0),
    "w8-combined-spend": num(spend(combined), "$"),
    "w8-sept-spend": num(spend(clean_new), "$"),
    # Week 9
    "w9-services-rows": num(len(S), "rows", 0),
    # Week 10
    "w10-relationships": num(3, "relationships", 0),
    "w10-no-service-clients": num(N_NO_SERVICE, "clients", 0),
    # Week 11
    "w11-clients-served": num(clients_served, "clients", 0),
    "w11-avg-spend-per-client": num(money(total / clients_served), "$"),
    "w11-north-spend": num(per_region["North"], "$"),
    # Week 12
    "w12-top-month": txt(top_month[0], [top_month[0], month_name, month_name.replace(" ", ""),
                                        date(int(top_month[0][:4]), int(top_month[0][5:]), 1).strftime("%b %Y")]),
    "w12-mar-2026-spend": num(per_month["2026-03"], "$"),
    "w12-avg-los": num(avg_los, "days", 0.1),
    # Week 13
    "w13-second-category": txt(sorted(per_category.items(), key=lambda kv: -kv[1])[1][0]),
    # Week 14
    "w14-ys-central": num(ys_central, "$"),
    "w14-chw-spend": num(chw_spend, "$"),
    # Week 15 capstone
    "w15-q1-top-worker": txt(top_worker[0], [top_worker[0], worker_by_id[top_worker[0]][1]]),
    "w15-q2-mh-avg": num(mh_avg, "$"),
    "w15-q3-zero-cost-pct": num(zero_cost_pct, "%", 0.1),
    "w15-q4-top-avg-region": txt(top_avg_region[0]),
    "w15-q5-over-2000": num(sum(1 for v in per_client.values() if v > 2000), "clients", 0),
}

with open(os.path.join(HERE, "answer-key.json"), "w", encoding="utf-8") as f:
    json.dump(key, f, indent=2, sort_keys=True)
    f.write("\n")

if __name__ == "__main__":
    print(f"clients={len(clients)} services_raw={len(raw_services)} clean={len(S)} "
          f"sept_raw={len(raw_new)} total=${total:,.2f}")
