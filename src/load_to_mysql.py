
import pandas as pd
from pathlib import Path
from getpass import getpass
from sqlalchemy import create_engine, URL, text

# ==========================================
# SALES SIGHT 360 - MYSQL DATA IMPORT
# ==========================================

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"

# ==========================================
# 1. MYSQL CONNECTION DETAILS
# ==========================================

print("\nSALES SIGHT 360 - MYSQL CONNECTION\n")

username = input("Enter MySQL username [root]: ").strip()
if not username:
    username = "root"

password = getpass("Enter your MySQL password: ")

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=username,
    password=password,
    host="localhost",
    port=3306,
    database="salessight360"
)

engine = create_engine(connection_url)

# ==========================================
# 2. TEST MYSQL CONNECTION
# ==========================================

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT DATABASE()")
        )

        print("\nConnected successfully!")
        print("Database:", result.scalar())

except Exception as error:
    print("\nMySQL connection failed!")
    print("Error:", error)
    raise SystemExit(1)

# ==========================================
# 3. DEFINE DATASET IMPORT ORDER
# ==========================================

files = [
    ("sales_reps", "sales_reps_cleaned.csv"),
    ("products", "products_cleaned.csv"),
    ("crm_leads", "crm_leads_cleaned.csv"),
    ("orders", "orders_cleaned.csv"),
    ("payments", "payments_cleaned.csv"),
    ("sales_targets", "sales_targets_cleaned.csv"),
    ("lead_stage_history", "lead_stage_history_cleaned.csv")
]

date_columns = {
    "crm_leads": ["lead_date"],
    "orders": ["order_date"],
    "payments": ["payment_date"],
    "sales_targets": ["month"],
    "lead_stage_history": ["stage_date"]
}

# ==========================================
# 4. IMPORT CSV DATA INTO MYSQL
# ==========================================

print("\nIMPORTING DATASETS...\n")

try:

    for table_name, filename in files:

        file_path = PROCESSED / filename

        df = pd.read_csv(
            file_path,
            parse_dates=date_columns.get(table_name, [])
        )

        df.to_sql(
            name=table_name,
            con=engine,
            if_exists="append",
            index=False,
            chunksize=500
        )

        print(
            f"Imported {len(df)} records "
            f"into {table_name}"
        )

except Exception as error:
    print("\nDATA IMPORT FAILED!")
    print("Error:", error)
    print(
        "Check the error before attempting another import."
    )
    raise SystemExit(1)

# ==========================================
# 5. VERIFY IMPORTED RECORD COUNTS
# ==========================================

print("\n========== MYSQL IMPORT VALIDATION ==========\n")

with engine.connect() as connection:

    for table_name, _ in files:

        count = connection.execute(
            text(f"SELECT COUNT(*) FROM `{table_name}`")
        ).scalar()

        print(
            f"{table_name}: {count} records"
        )

print("\n============================================")
print("ALL DATASETS IMPORTED SUCCESSFULLY!")
print("============================================")

engine.dispose()