import pandas as pd
import os
import django
import re
import numpy as np

# --------------------------
# Setup Django environment
# --------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cotglobal_attendance.settings")
django.setup()

from attendance.models import Member

# --------------------------
# Step 1: Load Children Excel
# --------------------------
df = pd.read_excel("db/HERITAGE_DAN.xlsx", header=1)  # adjust header if needed

# Normalize column names: lowercase, strip spaces, replace spaces with _
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Detect columns
name_col = next((c for c in df.columns if "name" in c and "parent" not in c), None)
age_col = next((c for c in df.columns if "age" in c), None)
gender_col = next((c for c in df.columns if "gender" in c), None)
parent_name_col = next((c for c in df.columns if "parent" in c and "name" in c), None)
# Detect parent phone column (allow for phone columns even if 'parent' not in header)
parent_phone_col = next((c for c in df.columns if ("phone" in c or "number" in c)), None)

# print("Detected Columns:")
# print(f"Name: {name_col}")
# print(f"Age: {age_col}")
# print(f"Gender: {gender_col}")
# print(f"Parent Name: {parent_name_col}")
# print(f"Parent Phone: {parent_phone_col}")

# --------------------------
# Step 2: Clean and prepare dataframe
# --------------------------
df_clean = pd.DataFrame()
df_clean["name"] = df[name_col]

# Age cleaning
def clean_age(x):
    if pd.isna(x) or str(x).strip() == "":  # strip spaces too
        return None
    s = str(x).strip().upper()
    if s == "B":
        return 0
    if s.isdigit():
        return int(s)
    return None

# Age
df_clean["age"] = df[age_col].apply(clean_age)

df_clean["age"] = df_clean["age"].astype("Int64")  # nullable integer type

# Gender
df_clean["gender"] = df[gender_col].fillna("") if gender_col else ""

# Parent Name
df_clean["parent_name"] = df[parent_name_col].fillna("") if parent_name_col else ""

# Parent Phone Cleaning
def clean_parent_phone(x):
    if pd.isna(x):
        return ""
    s = str(x).replace(" ", "")
    if re.search(r"[a-zA-Z]", s):  # contains letters
        return ""
    digits_only = "".join(re.findall(r"\d+", s))
    return digits_only

df_clean["parent_phone_number"] = df[parent_phone_col].apply(clean_parent_phone) if parent_phone_col else ""

# Status complete: only True if age is not None, gender, parent name & parent phone exist
def check_status(row):
    required_fields = ["age", "gender", "parent_name", "parent_phone_number"]
    for f in required_fields:
        if pd.isna(row[f]) or row[f] == "":  # <- use pd.isna for NA/None
            return False
    return True

df_clean["status_complete"] = df_clean.apply(check_status, axis=1)
df_clean["service_category"] = "Child"

# --------------------------
# Step 3: Save cleaned file
# --------------------------
clean_file = "db/children_clean_ready.xlsx"
df_clean.to_excel(clean_file, index=False)
print(f"STEP 2 COMPLETE: Clean file saved as {clean_file}")
# empty_ages = df_clean[df_clean["age"].isna()]
# print(empty_ages)

# --------------------------
# Step 4: Import into Django
# --------------------------

members = []
for _, row in df_clean.iterrows():
    members.append(Member(
        name=row["name"],
        role="Child",
        phone_number="",
        gender=row["gender"],
        age=row["age"] if pd.notna(row["age"]) else None,
        parent_name=row["parent_name"],
        parent_phone_number=row["parent_phone_number"],
        status_complete=row["status_complete"]
    ))

Member.objects.bulk_create(members)
print(f"STEP 3 COMPLETE: {len(members)} child members loaded into the database.")
