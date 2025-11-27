import pandas as pd
import os
import django

# --------------------------
# Setup Django environment
# --------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cotglobal_attendance.settings")
django.setup()

from attendance.models import Member

# --------------------------
# Step 2: Load teens excel
# --------------------------
df = pd.read_excel(
    "db/TEENS_EXOUSIA_AS_AT_16-10-24(1)(1).xlsx",
    header=1
)

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# Detect name column
name_col = None
for col in df.columns:
    if "name" in col:
        name_col = col
        break

# Detect phone column
phone_col = None
for col in df.columns:
    if "phone" in col or "number" in col:
        phone_col = col
        break

# Extract name + phone
df_clean = pd.DataFrame()
df_clean["name"] = df[name_col]

if phone_col:
    df_clean["phone"] = df[phone_col].fillna("").astype(str)
else:
    df_clean["phone"] = ""

# Add empty fields
df_clean["gender"] = ""
df_clean["age"] = None
df_clean["parent_name"] = ""
df_clean["parent_phone_number"] = ""
df_clean["service_category"] = "Teen"
df_clean["status_complete"] = False

# Save cleaned file
df_clean.to_excel("db/teens_clean_ready.xlsx", index=False)
print("STEP 2 COMPLETE: Clean file saved as db/teens_clean_ready.xlsx")


# --------------------------
# Step 3: Import CLEAN FILE into Django
# --------------------------
members = []
for i, row in df_clean.iterrows():  
    members.append(Member(
        name=row["name"],
        role="Teen",
        phone_number=row["phone"],
        gender=row["gender"],
        age=row["age"] if pd.notna(row["age"]) else None,
        parent_name=row["parent_name"],
        parent_phone_number=row["parent_phone_number"],
        status_complete=row["status_complete"]
    ))

Member.objects.bulk_create(members)
print(f"STEP 3 COMPLETE: {len(members)} teen members loaded into the database.")
