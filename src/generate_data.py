
import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================
# SALES SIGHT 360 - DATA GENERATION
# ==========================================

rng = np.random.default_rng(42)

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ==========================================
# 1. SALES REPRESENTATIVES
# ==========================================

regions = ["North", "South", "East", "West", "Central"]

teams = [
    f"{region}_Team_{i}"
    for region in regions
    for i in [1, 2]
]

reps = []

for i in range(30):
    team = teams[i // 3]
    region = team.split("_")[0]

    reps.append({
        "rep_id": f"REP{i+1:03}",
        "rep_name": f"Sales Rep {i+1}",
        "team": team,
        "region": region,
        "monthly_target": int(rng.integers(100000, 180000))
    })

reps_df = pd.DataFrame(reps)

# ==========================================
# 2. PRODUCTS
# ==========================================

categories = [
    "Electronics",
    "Software",
    "Furniture",
    "Accessories"
]

products = []

for i in range(20):
    products.append({
        "product_id": f"PROD{i+1:03}",
        "product_name": f"Product {i+1}",
        "category": categories[i % 4],
        "unit_price": int(rng.integers(2000, 50000))
    })

products_df = pd.DataFrame(products)

# ==========================================
# 3. CRM LEADS
# ==========================================

channels = [
    "Website",
    "Social Media",
    "Direct Sales",
    "Partner",
    "Email"
]

stages = [
    "New",
    "Contacted",
    "Qualified",
    "Proposal",
    "Negotiation",
    "Closed Won",
    "Closed Lost"
]

stage_probabilities = [
    0.08, 0.10, 0.12, 0.15, 0.10, 0.30, 0.15
]

start_date = pd.Timestamp("2025-01-01")
end_date = pd.Timestamp("2026-10-31")

lead_dates = pd.to_datetime(
    rng.integers(
        start_date.value // 10**9,
        end_date.value // 10**9,
        5000
    ),
    unit="s"
).normalize()

leads = []

for i in range(5000):

    rep = reps_df.iloc[rng.integers(0, len(reps_df))]
    product = products_df.iloc[
        rng.integers(0, len(products_df))
    ]

    stage = rng.choice(
        stages,
        p=stage_probabilities
    )

    leads.append({
        "lead_id": f"LEAD{i+1:05}",
        "customer_id": f"CUST{i+1:05}",
        "lead_date": lead_dates[i],
        "rep_id": rep["rep_id"],
        "product_id": product["product_id"],
        "region": rep["region"],
        "channel": rng.choice(channels),
        "stage": stage,
        "expected_deal_value": round(
            product["unit_price"] * rng.uniform(1, 5), 2
        )
    })

leads_df = pd.DataFrame(leads)

# ==========================================
# 4. ORDERS
# ==========================================

won_leads = leads_df[
    leads_df["stage"] == "Closed Won"
]

order_leads = won_leads.sample(
    frac=0.90,
    random_state=42
)

orders = []

for i, (_, lead) in enumerate(order_leads.iterrows()):

    product = products_df[
        products_df["product_id"] == lead["product_id"]
    ].iloc[0]

    quantity = int(rng.integers(1, 6))

    discount = round(
        float(rng.uniform(0, 0.15)), 2
    )

    revenue = round(
        quantity * product["unit_price"] * (1 - discount),
        2
    )

    days_to_order = int(rng.integers(1, 46))

    order_date = min(
        lead["lead_date"] + pd.Timedelta(days=days_to_order),
        end_date
    )

    orders.append({
        "order_id": f"ORD{i+1:05}",
        "lead_id": lead["lead_id"],
        "customer_id": lead["customer_id"],
        "order_date": order_date,
        "product_id": lead["product_id"],
        "rep_id": lead["rep_id"],
        "region": lead["region"],
        "quantity": quantity,
        "discount": discount,
        "revenue": revenue,
        "order_status": rng.choice(
            ["Delivered", "Processing", "Cancelled"],
            p=[0.82, 0.13, 0.05]
        )
    })

orders_df = pd.DataFrame(orders)

# ==========================================
# 5. PAYMENT RECORDS
# ==========================================

payments = []
payment_number = 1

for _, order in orders_df.iterrows():

    number_of_payments = int(
        rng.choice([1, 2])
    )

    remaining = order["revenue"]

    for j in range(number_of_payments):

        if j == number_of_payments - 1:
            amount = round(remaining, 2)
        else:
            amount = round(remaining * 0.5, 2)

        remaining = round(remaining - amount, 2)

        payments.append({
            "payment_id": f"PAY{payment_number:05}",
            "order_id": order["order_id"],
            "payment_date": order["order_date"] +
                pd.Timedelta(days=int(rng.integers(0, 15))),
            "amount": amount,
            "payment_status": rng.choice(
                ["Success", "Failed", "Pending"],
                p=[0.85, 0.10, 0.05]
            )
        })

        payment_number += 1

payments_df = pd.DataFrame(payments)

# ==========================================
# 6. MONTHLY SALES TARGETS
# ==========================================

targets = []

months = pd.date_range(
    "2025-01-01",
    "2026-10-01",
    freq="MS"
)

for team in teams:
    for month in months:

        targets.append({
            "team": team,
            "region": team.split("_")[0],
            "month": month,
            "sales_target": int(
                rng.integers(250000, 400000)
            )
        })

targets_df = pd.DataFrame(targets)

# ==========================================
# 7. LEAD STAGE HISTORY
# ==========================================

history = []

for _, lead in leads_df.iterrows():

    current_stage = lead["stage"]

    if current_stage == "Closed Lost":
        path = [
            "New",
            "Contacted",
            "Qualified",
            "Closed Lost"
        ]
    else:
        path = stages[
            :stages.index(current_stage) + 1
        ]

    previous_date = lead["lead_date"]

    for stage in path:

        history.append({
            "history_id": f"HIST{len(history)+1:06}",
            "lead_id": lead["lead_id"],
            "stage": stage,
            "stage_date": previous_date
        })

        previous_date += pd.Timedelta(
            days=int(rng.integers(1, 8))
        )

history_df = pd.DataFrame(history)

# ==========================================
# 8. SAVE DATASETS
# ==========================================

datasets = {
    "sales_reps.csv": reps_df,
    "products.csv": products_df,
    "crm_leads.csv": leads_df,
    "orders.csv": orders_df,
    "payments.csv": payments_df,
    "sales_targets.csv": targets_df,
    "lead_stage_history.csv": history_df
}

print("\nGENERATING SALES SIGHT 360 DATASETS\n")

for filename, dataframe in datasets.items():

    file_path = RAW / filename

    dataframe.to_csv(
        file_path,
        index=False
    )

    print(
        f"Created: {filename} | "
        f"Records: {len(dataframe)}"
    )

print("\n===================================")
print("ALL DATASETS GENERATED SUCCESSFULLY")
print("===================================")

print(f"\nSaved location: {RAW}")
