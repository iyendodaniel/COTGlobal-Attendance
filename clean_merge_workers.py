import pandas as pd
import os
import django
import re

# --------------------------
# Setup Django environment
# --------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cotglobal_attendance.settings")
django.setup()

from attendance.models import Member

# --------------------------
# Step 1: Load Workers Excel
# --------------------------
df = pd.read_excel("db/WORKERS_DAN.xlsx", header=0)  # adjust header if needed

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

# Detect department column
dept_col = None
for col in df.columns:
    if "department" in col:
        dept_col = col
        break

# --------------------------
# Step 2: Clean and prepare dataframe
# --------------------------
df_clean = pd.DataFrame()
df_clean["name"] = df[name_col]

# Robust phone number extraction
def first_number(x):
    if pd.isna(x):
        return ""
    # Keep only digits and join them together
    s = str(x)
    digits_only = "".join(re.findall(r'\d+', s))
    return digits_only

if phone_col:
    df_clean["phone"] = df[phone_col].apply(first_number)
else:
    df_clean["phone"] = ""

# Process department
def fix_department(dept):
    if pd.isna(dept):
        return ""

    d = str(dept).lower().strip()

    # Fix 121 hostess
    if "121 hostess" in d:
        return "CHAPEL 121 HOSTESS"

    # Fix all presbytery variations
    if "presb" in d:  
        return "PRESBYTERY"  

    return str(dept)


if dept_col:
    df_clean["department"] = df[dept_col].apply(fix_department)
else:
    df_clean["department"] = ""

# Add empty/default fields
df_clean["gender"] = ""
df_clean["age"] = None
df_clean["parent_name"] = ""
df_clean["parent_phone_number"] = ""
df_clean["service_category"] = "Worker"
df_clean["status_complete"] = False

# --------------------------
# Step 3: Save clean file
# --------------------------
clean_file = "db/workers_clean_ready.xlsx"
df_clean.to_excel(clean_file, index=False)
print(f"STEP 2 COMPLETE: Clean file saved as {clean_file}")

# --------------------------
# Step 4: Import into Django
# --------------------------
members = []
for i, row in df_clean.iterrows():
    members.append(Member(
        name=row["name"],
        role="Worker",
        phone_number=row["phone"],
        gender=row["gender"],
        age=row["age"] if pd.notna(row["age"]) else None,
        parent_name=row["parent_name"],
        parent_phone_number=row["parent_phone_number"],
        department=row["department"],
        status_complete=row["status_complete"]
    ))

Member.objects.bulk_create(members)
print(f"STEP 3 COMPLETE: {len(members)} worker members loaded into the database.")
