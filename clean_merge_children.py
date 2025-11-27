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
# Step 2: Load teens_clean_names.xlsx
# --------------------------
df = pd.read_excel("db/teens_clean_names.xlsx")

# Add empty fields
df["phone"] = ""
df["gender"] = ""
df["age"] = None
df["parent_name"] = ""
df["service_category"] = "Teen"
df["parent_phone_number"] = ""  # new field for children
df["status_complete"] = False

# Save to master file (optional)
master_file = "db/teens_master.xlsx"
df.to_excel(master_file, index=False)
print(f"STEP 2 COMPLETE: Created {master_file} with empty fields.")

# --------------------------
# Step 3: Import into Django DB
# --------------------------
members = []
for i, row in df.iterrows():
    members.append(Member(
        name=row["NAME"],
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
