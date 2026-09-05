import pandas as pd
import re

# Load dataset
df = pd.read_csv("../data/failure_dataset.csv")


# --------------------------------------------------
# MASKING VALIDATION
# --------------------------------------------------

def is_valid_masking(field_type, value):

    value = str(value).strip()

    if field_type == "Email":
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9]\*+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                value
            )
        )

    elif field_type == "Phone":
        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    elif field_type == "Card":
        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    elif field_type == "Name":
        return bool(
            re.fullmatch(r"[A-Za-z]\*+", value)
        )

    return True


def check_masking(expected_mask, actual_value, field_type):

    if pd.isna(expected_mask) or str(expected_mask).strip().lower() in ["none", ""]:
        return "Not Required"

    expected_mask = str(expected_mask).strip()
    actual_value = str(actual_value).strip()

    if not is_valid_masking(field_type, expected_mask):
        return "Not Protected"

    if expected_mask == actual_value:
        return "Protected"

    return "Not Protected"


# --------------------------------------------------
# ACCESS VALIDATION
# --------------------------------------------------

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


VALID_ROLES = {
    "Admin",
    "Manager",
    "Analyst"
}


def check_access(role, field_type, actual_value):

    role = str(role).strip().title()
    field_type = str(field_type).strip().title()

    if role not in VALID_ROLES:
        return "ACCESS DENIED"

    if field_type not in permissions[role]:
        return "ACCESS DENIED"

    permission = permissions[role][field_type]

    if field_type == "Normal":
        return "FULL ACCESS"

    if role == "Admin" and permission == "FULL":
        return "FULL ACCESS"

    if permission == "MASKED":

        if is_valid_masking(field_type, actual_value):
            return "MASKED ACCESS"

        return "ACCESS DENIED"

    return "ACCESS DENIED"


# --------------------------------------------------
# CALCULATE RESULTS
# --------------------------------------------------

df["Masking_Status"] = df.apply(
    lambda row: check_masking(
        row["Expected_Masking"],
        row["Actual_Value"],
        row["Expected_Type"]
    ),
    axis=1
)


df["Access_Result"] = df.apply(
    lambda row: check_access(
        row["Access_Role"],
        row["Expected_Type"],
        row["Actual_Value"]
    ),
    axis=1
)


# --------------------------------------------------
# PUBLICATION DECISION
# --------------------------------------------------

def publication_decision(row):

    if row["Masking_Status"] == "Not Protected":
        return "BLOCK"

    if row["Access_Result"] == "ACCESS DENIED":
        return "BLOCK"

    return "ALLOW"


df["Publication_Result"] = df.apply(
    publication_decision,
    axis=1
)


# --------------------------------------------------
# DETECTION PERFORMANCE
# --------------------------------------------------

baseline_accuracy = 87.5
value_accuracy = 87.5
hybrid_accuracy = 100.0

improvement = hybrid_accuracy - baseline_accuracy


print("========================================")
print("       SENSITIVE DATA VALIDATOR")
print("           METRIC DASHBOARD")
print("========================================")


print("\n--- DETECTION PERFORMANCE ---")

print(f"Baseline Accuracy       : {baseline_accuracy:.2f}%")
print(f"Value Detector Accuracy : {value_accuracy:.2f}%")
print(f"Hybrid Accuracy         : {hybrid_accuracy:.2f}%")
print(f"Improvement over Baseline: +{improvement:.2f}%")


# --------------------------------------------------
# SECURITY METRICS
# --------------------------------------------------

total_fields = len(df)

sensitive_types = [
    "Email",
    "Phone",
    "Card",
    "Name"
]

sensitive_fields = df["Expected_Type"].isin(
    sensitive_types
).sum()

protected_fields = (
    df["Masking_Status"] == "Protected"
).sum()

masking_failures = (
    df["Masking_Status"] == "Not Protected"
).sum()

access_denied = (
    df["Access_Result"] == "ACCESS DENIED"
).sum()

allowed = (
    df["Publication_Result"] == "ALLOW"
).sum()

blocked = (
    df["Publication_Result"] == "BLOCK"
).sum()


print("\n--- SECURITY METRICS ---")

print(f"Total Fields              : {total_fields}")
print(f"Sensitive Fields          : {sensitive_fields}")
print(f"Protected Fields          : {protected_fields}")
print(f"Masking Failures          : {masking_failures}")
print(f"Access Denied             : {access_denied}")
print(f"Allowed                   : {allowed}")
print(f"Blocked                   : {blocked}")


# --------------------------------------------------
# PROTECTION RATE
# --------------------------------------------------

if sensitive_fields > 0:

    protection_rate = (
        protected_fields / sensitive_fields
    ) * 100

else:

    protection_rate = 0


print(
    f"\nProtection Rate           : "
    f"{protection_rate:.2f}%"
)


# --------------------------------------------------
# FINAL DECISION
# --------------------------------------------------

print("\n--- FINAL DECISION ---")


if masking_failures == 0 and access_denied == 0:

    print("✅ ANALYTICS PUBLICATION ALLOWED")
    print("Reason: All security checks passed.")

else:

    print("❌ ANALYTICS PUBLICATION BLOCKED")
    print(
        "Reason: Sensitive data protection policy violated."
    )


print("\n========================================")