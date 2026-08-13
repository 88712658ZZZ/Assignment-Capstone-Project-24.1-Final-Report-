"""
generate_users.py
------------------
Generates a synthetic roster of 100 users that the DLP alert dataset
(`generate_data.py`) attributes alerts to. Each user has stable traits
(department, device type, tenure, baseline risk propensity, watchlist
status) so that alert-level features for the same user are internally
consistent across their alert history, rather than independently
randomized per alert.

This is SYNTHETIC DATA -- no real employee data is used or represented.

Run:
    python src/generate_users.py --n 100 --seed 42 --out data/raw/users.csv
"""

import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DEPARTMENTS = [
    "Finance", "Engineering", "Sales", "HR", "Legal",
    "Customer_Support", "IT", "Marketing", "Executive",
]

JOB_LEVELS = ["IC1", "IC2", "IC3", "Senior", "Manager", "Director", "VP"]

DEVICE_TYPES = ["corporate_managed", "byod_mobile", "byod_laptop", "unmanaged"]

LOCATIONS = [
    "New York, US", "San Francisco, US", "Austin, US", "Chicago, US",
    "London, UK", "Dublin, IE", "Toronto, CA", "Singapore, SG",
    "Sydney, AU", "Remote",
]

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Jamie", "Avery",
    "Quinn", "Drew", "Skylar", "Reese", "Rowan", "Emerson", "Hayden", "Parker",
    "Dakota", "Sage", "Finley", "Charlie", "Sam", "Robin", "Blake", "Cameron",
    "Elliot", "Harper", "Kai", "Lane", "Marlowe", "Noa", "Ode", "Peyton",
    "Remy", "Shay", "Toby", "Val", "Wren", "Yael", "Zion", "Aspen",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
]


def _dept_weights():
    w = np.array([0.16, 0.16, 0.14, 0.10, 0.10, 0.12, 0.10, 0.08, 0.04])
    return w / w.sum()


def _level_weights():
    # Most of the org is individual contributors; fewer senior/leadership roles
    w = np.array([0.20, 0.20, 0.16, 0.18, 0.14, 0.08, 0.04])
    return w / w.sum()


def generate_users(n=100, seed=42):
    rng = np.random.default_rng(seed)
    today = datetime(2026, 6, 30)  # anchor "today" for tenure calculations

    used_names = set()
    rows = []

    for i in range(n):
        user_id = f"U-{1000 + i}"

        # Ensure unique display names within the roster
        while True:
            full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            if full_name not in used_names:
                used_names.add(full_name)
                break

        department = rng.choice(DEPARTMENTS, p=_dept_weights())
        job_level = rng.choice(JOB_LEVELS, p=_level_weights())
        device_type = rng.choice(DEVICE_TYPES, p=[0.55, 0.15, 0.20, 0.10])
        location = rng.choice(LOCATIONS)

        tenure_days = int(rng.integers(30, 3650))  # 1 month to 10 years
        hire_date = today - timedelta(days=tenure_days)

        # Departing/flagged employees are rare but drive disproportionate risk
        is_departing_soon = int(rng.random() < 0.05)
        on_watchlist = int(is_departing_soon or rng.random() < 0.04)

        # Stable per-user baseline risk propensity (0-1). Most users cluster
        # low; a long tail of higher-propensity users exists, consistent
        # with insider-threat research showing risk concentrates in a
        # small subset of the population.
        base_propensity = float(np.round(np.clip(rng.beta(1.5, 6) +
                                 (0.25 if on_watchlist else 0), 0, 1), 3))

        email = f"{full_name.lower().replace(' ', '.')}@example-corp.com"

        rows.append({
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "department": department,
            "job_level": job_level,
            "primary_device_type": device_type,
            "location": location,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "tenure_days": tenure_days,
            "is_departing_soon": is_departing_soon,
            "on_watchlist": on_watchlist,
            "baseline_risk_propensity": base_propensity,
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic user roster.")
    parser.add_argument("--n", type=int, default=100, help="Number of users to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--out", type=str, default="data/raw/users.csv", help="Output CSV path.")
    args = parser.parse_args()

    df = generate_users(n=args.n, seed=args.seed)
    df.to_csv(args.out, index=False)

    print(f"Generated {len(df)} synthetic users -> {args.out}")
    print(f"Watchlist users: {df['on_watchlist'].sum()} | Departing soon: {df['is_departing_soon'].sum()}")


if __name__ == "__main__":
    main()
