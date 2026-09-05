import pandas as pd
import re


# ==============================
# LOAD DATA
# ==============================

df = pd.read_csv("../data/failure_dataset.csv")


# ==============================
# 1. FIELD NAME DETECTION
# ==============================

def detect_by_field_name(field_name):

    field = str(field_name).strip().lower()

    if "email" in field or "mail" in field:
        return "Email"

    elif "phone" in field or "mobile" in field:
        return "Phone"

    elif "card" in field or "cc" in field:
        return "Card"

    elif "name" in field or "nm" in field:
        return "Name"

    return "Unknown"


# ==============================
# 2. VALUE PATTERN DETECTION
# ==============================

def detect_by_value(value):

    value = str(value).strip()

    if not value:
        return "Unknown"

    # Email
    if re.fullmatch(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        value
    ):
        return "Email"

    # Phone
    elif re.fullmatch(r"\d{10}", value):
        return "Phone"

    # Card
    elif re.fullmatch(r"\d{16}", value):
        return "Card"

    # Name
    elif re.fullmatch(
        r"[A-Za-z]+(?:[ .'-][A-Za-z]+)*",
        value
    ):
        return "Name"

    return "Unknown"


# ==============================
# 3. HYBRID DETECTION
# ==============================

def hybrid_detection(field_name, sample_value):

    field_result = detect_by_field_name(field_name)
    value_result = detect_by_value(sample_value)

    # Both agree and both provide useful evidence
    if field_result != "Unknown" and field_result == value_result:
        return field_result

    # Value gives strong evidence
    if value_result in ["Email", "Phone", "Card"]:
        return value_result

    # Field name gives evidence
    if field_result != "Unknown":
        return field_result

    # Value gives evidence
    if value_result != "Unknown":
        return value_result

    return "Normal"


# ==============================
# 4. MASKING VALIDATION
# ==============================

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

    if pd.isna(expected_mask) or str(expected_mask).strip().lower() in [
        "none",
        ""
    ]:
        return "Not Required"

    expected_mask = str(expected_mask).strip()
    actual_value = str(actual_value).strip()

    field_type = str(field_type).strip().title()

    # Expected masking format itself must be valid
    if not is_valid_masking(field_type, expected_mask):
        return "Not Protected"

    # Actual value must match expected protected value
    if expected_mask == actual_value:
        return "Protected"

    return "Not Protected"


# ==============================
# 5. ACCESS CONTROL
# ==============================

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


def check_access(role, field_type, actual_value):

    role = str(role).strip().title()
    field_type = str(field_type).strip().title()

    permission = permissions.get(role, {}).get(
        field_type,
        "DENIED"
    )

    if permission == "DENIED":
        return "ACCESS DENIED"

    # Normal data does not require masking
    if field_type == "Normal":
        return "FULL ACCESS"

    # Admin
    if permission == "FULL":
        return "FULL ACCESS"

    # Manager / Analyst
    if permission == "MASKED":

        if is_valid_masking(field_type, actual_value):
            return "MASKED ACCESS"

        return "ACCESS DENIED"

    return "ACCESS DENIED"


# ==============================
# 6. FINAL DECISION
# ==============================

def final_decision(
    detection_status,
    masking_status,
    access_status
):

    # Detection mismatch = security risk
    if detection_status == "MISMATCH":
        return "BLOCK"

    # Sensitive data is not protected
    if masking_status == "Not Protected":
        return "BLOCK"

    # User does not have required access
    if access_status == "ACCESS DENIED":
        return "BLOCK"

    return "ALLOW"


# ==============================
# 7. RUN COMPLETE PIPELINE
# ==============================


print("TEST FIELD:", detect_by_field_name("amount"))
print("TEST VALUE:", detect_by_value("5000"))
print("TEST HYBRID:", hybrid_detection("amount", "5000"))


df["Detected_Type"] = df.apply(
    lambda row: hybrid_detection(
        row["Field_Name"],
        row["Sample_Value"]
    ),
    axis=1
)


# Detection comparison
df["Detection_Status"] = df.apply(
    lambda row:
        "MATCH"
        if row["Detected_Type"] == row["Expected_Type"]
        else "MISMATCH",
    axis=1
)


# Masking
df["Masking_Status"] = df.apply(
    lambda row: check_masking(
        row["Expected_Masking"],
        row["Actual_Value"],
        row["Expected_Type"]
    ),
    axis=1
)


# Access
df["Access_Result"] = df.apply(
    lambda row: check_access(
        row["Access_Role"],
        row["Detected_Type"],
        row["Actual_Value"]
    ),
    axis=1
)


# Final decision
df["Final_Decision"] = df.apply(
    lambda row: final_decision(
        row["Detection_Status"],
        row["Masking_Status"],
        row["Access_Result"]
    ),
    axis=1
)


# ==============================
# 8. METRICS
# ==============================

total_fields = len(df)

detection_matches = (
    df["Detection_Status"] == "MATCH"
).sum()

detection_mismatches = (
    df["Detection_Status"] == "MISMATCH"
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
    df["Final_Decision"] == "ALLOW"
).sum()

blocked = (
    df["Final_Decision"] == "BLOCK"
).sum()


detection_accuracy = (
    detection_matches / total_fields * 100
)

protection_rate = (
    protected_fields /
    (protected_fields + masking_failures) * 100
    if (protected_fields + masking_failures) > 0
    else 100
)


# ==============================
# 9. DISPLAY RESULTS
# ==============================

print("\n========================================")
print("      SENSITIVE DATA VALIDATOR")
print("        COMPLETE PIPELINE")
print("========================================")

print("\n--- FIELD VALIDATION RESULTS ---\n")

print(
    df[
        [
            "Field_Name",
            "Expected_Type",
            "Detected_Type",
            "Detection_Status",
            "Masking_Status",
            "Access_Result",
            "Final_Decision"
        ]
    ].to_string(index=False)
)


print("\n========================================")
print("              METRICS")
print("========================================")

print(f"Total Fields          : {total_fields}")
print(f"Detection Accuracy    : {detection_accuracy:.2f}%")
print(f"Detection Mismatches  : {detection_mismatches}")
print(f"Protected Fields      : {protected_fields}")
print(f"Masking Failures      : {masking_failures}")
print(f"Access Denied         : {access_denied}")
print(f"Allowed               : {allowed}")
print(f"Blocked               : {blocked}")
print(f"Protection Rate       : {protection_rate:.2f}%")


print("\n========================================")
print("          FINAL PUBLICATION")
print("========================================")

if blocked > 0:

    print("PUBLICATION BLOCKED")
    print("Reason: Security policy violation detected.")

else:

    print("PUBLICATION ALLOWED")
    print("Reason: All validation checks passed.")