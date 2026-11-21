
import pandas as pd
from pathlib import Path

# ==========================================
# SALES SIGHT 360 - DATA CLEANING
# ==========================================

BASE = Path(__file__).resolve().parent.parent

RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"

PROCESSED.mkdir(parents=True, exist_ok=True)

# ==========================================
# 1. LOAD ALL DATASETS
# ==========================================

datasets = {
    "sales_reps": "sales_reps.csv",
    "products": "products.csv",
    "crm_leads": "crm_leads.csv",
    "orders": "orders.csv",
    "payments": "payments.csv",
    "sales_targets": "sales_targets.csv",
    "lead_stage_history": "lead_stage_history.csv"
}

data = {}

for name, filename in datasets.items():

    data[name] = pd.read_csv(
        RAW / filename
    )

    print(f"Loaded: {filename}")

# ==========================================
# 2. DEFINE PRIMARY KEYS
# ==========================================

primary_keys = {
    "sales_reps": "rep_id",
    "products": "product_id",
    "crm_leads": "lead_id",
    "orders": "order_id",
    "payments": "payment_id",
    "lead_stage_history": "history_id"
}

# ==========================================
# 3. CLEAN TEXT AND REMOVE DUPLICATES
# ==========================================

for name, df in data.items():

    # Remove unwanted spaces from text columns
    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        df[column] = df[column].str.strip()

    # Remove completely duplicated rows
    df.drop_duplicates(inplace=True)

    # Remove duplicate primary key records
    if name in primary_keys:

        key = primary_keys[name]

        df.drop_duplicates(
            subset=[key],
            keep="first",
            inplace=True
        )

    # Convert date columns
    date_columns = [
        col for col in df.columns
        if "date" in col.lower()
        or col.lower() == "month"
    ]

    for column in date_columns:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    data[name] = df

# ==========================================
# 4. CHECK FOREIGN KEY RELATIONSHIPS
# ==========================================

relationships = [
    ("crm_leads", "rep_id", "sales_reps", "rep_id"),
    ("crm_leads", "product_id", "products", "product_id"),
    ("orders", "lead_id", "crm_leads", "lead_id"),
    ("orders", "rep_id", "sales_reps", "rep_id"),
    ("orders", "product_id", "products", "product_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("lead_stage_history", "lead_id", "crm_leads", "lead_id")
]

relationship_results = []

for child, child_col, parent, parent_col in relationships:

    valid_ids = set(data[parent][parent_col].dropna())

    invalid_count = (
        ~data[child][child_col].isin(valid_ids)
    ).sum()

    relationship_results.append({
        "relationship": f"{child}.{child_col} -> {parent}.{parent_col}",
        "invalid_records": int(invalid_count)
    })

# ==========================================
# 5. GENERATE DATA QUALITY REPORT
# ==========================================

report = []

for name, df in data.items():

    key = primary_keys.get(name)

    report.append({
        "dataset": name,
        "total_records": len(df),
        "total_columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_primary_keys": (
            int(df[key].duplicated().sum())
            if key else "Not applicable"
        )
    })

report_df = pd.DataFrame(report)

relationship_df = pd.DataFrame(
    relationship_results
)

# ==========================================
# 6. SAVE CLEANED DATASETS
# ==========================================

for name, df in data.items():

    filename = f"{name}_cleaned.csv"

    df.to_csv(
        PROCESSED / filename,
        index=False
    )

    print(
        f"Saved cleaned dataset: {filename}"
    )

# ==========================================
# 7. SAVE REPORTS
# ==========================================

report_df.to_csv(
    PROCESSED / "data_quality_report.csv",
    index=False
)

relationship_df.to_csv(
    PROCESSED / "relationship_validation.csv",
    index=False
)

# ==========================================
# 8. DISPLAY RESULTS
# ==========================================

print("\n========== DATA QUALITY REPORT ==========\n")

print(report_df.to_string(index=False))

print("\n========== RELATIONSHIP VALIDATION ==========\n")

print(relationship_df.to_string(index=False))

print("\n==========================================")
print("DATA CLEANING COMPLETED SUCCESSFULLY!")
print("==========================================")

print(f"\nCleaned files saved in: {PROCESSED}")
