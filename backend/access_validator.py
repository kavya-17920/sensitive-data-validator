import pandas as pd
import re

# Load dataset
df = pd.read_csv("../data/failure_dataset.csv")


# ============================================================
# VALID ROLES
# ============================================================

VALID_ROLES = {
    "Admin",
    "Manager",
    "Analyst"
}


# ============================================================
# ROLE PERMISSIONS
# ============================================================

permissions = {

    "Admin": {
        "Email": "FULL",
        "Phone": "FULL",
        "Card": "FULL",
        "Name": "FULL",
        "Normal": "FULL"
    },

    "Manager": {
        "Email": "MASKED",
        "Phone": "MASKED",
        "Card": "MASKED",
        "Name": "MASKED",
        "Normal": "FULL"
    },

    "Analyst": {
        "Email": "MASKED",
        "Phone": "MASKED",
        "Card": "MASKED",
        "Name": "MASKED",
        "Normal": "FULL"
    }
}


# ============================================================
# MASKING VALIDATION
# ============================================================

def is_properly_masked(field_type, actual_value):

    value = str(actual_value).strip()

    # Email
    if field_type == "Email":

        return bool(
            re.fullmatch(
                r"[A-Za-z0-9]\*+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                value
            )
        )

    # Phone
    elif field_type == "Phone":

        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    # Card
    elif field_type == "Card":

        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    # Name
    elif field_type == "Name":

        return bool(
            re.fullmatch(r"[A-Za-z]\*+", value)
        )

    # Normal data does not require masking
    elif field_type == "Normal":
        return True

    return False


# ============================================================
# ACCESS CHECK
# ============================================================

def check_access(role, field_type, actual_value):

    # Normalize input
    role = str(role).strip().title()
    field_type = str(field_type).strip().title()

    # --------------------------------------------------------
    # 1. Validate role
    # --------------------------------------------------------

    if role not in VALID_ROLES:
        return "ACCESS DENIED"

    # --------------------------------------------------------
    # 2. Validate field type
    # --------------------------------------------------------

    if field_type not in permissions[role]:
        return "ACCESS DENIED"

    # Get permission
    permission = permissions[role][field_type]

    # --------------------------------------------------------
    # 3. Normal fields
    # --------------------------------------------------------

    if field_type == "Normal":
        return "FULL ACCESS"

    # --------------------------------------------------------
    # 4. Admin
    # --------------------------------------------------------

    if role == "Admin" and permission == "FULL":
        return "FULL ACCESS"

    # --------------------------------------------------------
    # 5. Manager / Analyst
    # --------------------------------------------------------

    if permission == "MASKED":

        if is_properly_masked(field_type, actual_value):
            return "MASKED ACCESS"

        return "ACCESS DENIED"

    return "ACCESS DENIED"


# ============================================================
# APPLY ACCESS VALIDATION
# ============================================================

df["Access_Result"] = df.apply(
    lambda row: check_access(
        row["Access_Role"],
        row["Expected_Type"],
        row["Actual_Value"]
    ),
    axis=1
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n========================================")
print("         ACCESS VALIDATOR")
print("========================================")

print("\n--- ACCESS ROLE VALIDATION ---\n")

print(
    df[
        [
            "Organisation",
            "Partner",
            "Field_Name",
            "Expected_Type",
            "Access_Role",
            "Actual_Value",
            "Access_Result"
        ]
    ].to_string(index=False)
)


# ============================================================
# METRICS
# ============================================================

denied = (
    df["Access_Result"] == "ACCESS DENIED"
).sum()

allowed = (
    df["Access_Result"] != "ACCESS DENIED"
).sum()

masked_access = (
    df["Access_Result"] == "MASKED ACCESS"
).sum()

full_access = (
    df["Access_Result"] == "FULL ACCESS"
).sum()

total_fields = len(df)

access_rate = (
    allowed / total_fields * 100
    if total_fields > 0
    else 0
)


# ============================================================
# DISPLAY METRICS
# ============================================================

print("\n========================================")
print("              METRICS")
print("========================================")

print(f"Total Fields      : {total_fields}")
print(f"Full Access       : {full_access}")
print(f"Masked Access     : {masked_access}")
print(f"Access Denied     : {denied}")
print(f"Access Allowed    : {allowed}")
print(f"Access Rate       : {access_rate:.2f}%")


# ============================================================
# FINAL ACCESS DECISION
# ============================================================

print("\n========================================")
print("        FINAL ACCESS DECISION")
print("========================================")

if denied > 0:

    print("❌ ACCESS VALIDATION FAILED")
    print(
        "Reason: One or more fields have "
        "insufficient access permissions."
    )

else:

    print("✅ ACCESS VALIDATION PASSED")
    print(
        "All fields satisfy the configured "
        "role-based access policy."
    )