import pandas as pd
import re

# Load dataset
df = pd.read_csv("../data/failure_dataset.csv")


# ============================================================
# MASKING PATTERN VALIDATION
# ============================================================

def is_valid_masking(field_type, masked_value):

    value = str(masked_value).strip()

    # Email example: k***@gmail.com
    if field_type == "Email":
        return bool(
            re.fullmatch(
                r"[A-Za-z0-9]\*+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                value
            )
        )

    # Phone example: ******3210 OR **********
    elif field_type == "Phone":
        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    # Card example: ************5678 OR ****************
    elif field_type == "Card":
        return bool(
            re.fullmatch(r"\*+", value)
            or re.fullmatch(r"\*+\d{4}", value)
        )

    # Name example: K***
    elif field_type == "Name":
        return bool(
            re.fullmatch(r"[A-Za-z]\*+", value)
        )

    # Normal fields do not need masking
    return True


# ============================================================
# MASKING CONTENT VALIDATION
# ============================================================

def validate_mask_against_actual(field_type, actual_value, masked_value):

    actual = str(actual_value).strip()
    masked = str(masked_value).strip()

    # ---------------- EMAIL ----------------
    if field_type == "Email":

        actual_match = re.fullmatch(
            r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})",
            actual
        )

        masked_match = re.fullmatch(
            r"([A-Za-z0-9])\*+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})",
            masked
        )

        if not actual_match or not masked_match:
            return False

        actual_username = actual_match.group(1)
        actual_domain = actual_match.group(2)

        masked_first_character = masked_match.group(1)
        masked_domain = masked_match.group(2)

        return (
            actual_username[0].lower()
            == masked_first_character.lower()
            and actual_domain.lower()
            == masked_domain.lower()
            and "*" in masked
        )

    # ---------------- PHONE ----------------
    elif field_type == "Phone":

        if not re.fullmatch(r"\d{10}", actual):
            return False

        if re.fullmatch(r"\*+", masked):
            return len(masked) == len(actual)

        if re.fullmatch(r"\*+\d{4}", masked):

            visible_digits = masked[-4:]
            actual_last_four = actual[-4:]

            return visible_digits == actual_last_four

        return False

    # ---------------- CARD ----------------
    elif field_type == "Card":

        if not re.fullmatch(r"\d{16}", actual):
            return False

        if re.fullmatch(r"\*+", masked):
            return len(masked) == len(actual)

        if re.fullmatch(r"\*+\d{4}", masked):

            visible_digits = masked[-4:]
            actual_last_four = actual[-4:]

            return visible_digits == actual_last_four

        return False

    # ---------------- NAME ----------------
    elif field_type == "Name":

        if not re.fullmatch(
            r"[A-Za-z]+(?:[ .'-][A-Za-z]+)*",
            actual
        ):
            return False

        # First character should be preserved
        # and remaining characters should be masked
        if re.fullmatch(r"[A-Za-z]\*+", masked):

            return (
                masked[0].lower()
                == actual[0].lower()
                and len(masked) == len(actual)
            )

        return False

    # Normal fields
    return True


# ============================================================
# MAIN MASKING CHECK
# ============================================================
def check_masking(expected_mask, actual_value, field_type):

    # Normal fields do not require masking
    if (
        pd.isna(expected_mask)
        or str(expected_mask).strip().lower() in ["none", ""]
    ):
        return "Not Required"

    expected_mask = str(expected_mask).strip()
    actual_value = str(actual_value).strip()
    field_type = str(field_type).strip().title()

    # Check whether expected masking pattern is valid
    if not is_valid_masking(field_type, expected_mask):
        return "Not Protected"

    # Expected masked value and actual masked value must match
    if expected_mask == actual_value:
        return "Protected"

    return "Not Protected"

# ============================================================
# APPLY MASKING VALIDATION
# ============================================================

df["Masking_Status"] = df.apply(
    lambda row: check_masking(
        row["Expected_Masking"],
        row["Actual_Value"],
        row["Expected_Type"]
    ),
    axis=1
)


# ============================================================
# PUBLICATION DECISION
# ============================================================

def publication_decision(status):

    if status == "Not Protected":
        return "BLOCK"

    return "ALLOW"


df["Publication_Result"] = df["Masking_Status"].apply(
    publication_decision
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n========================================")
print("        MASKING VALIDATOR")
print("========================================")

print("\n--- MASKING VALIDATION RESULTS ---\n")

print(
    df[
        [
            "Field_Name",
            "Expected_Type",
            "Expected_Masking",
            "Actual_Value",
            "Masking_Status",
            "Publication_Result"
        ]
    ].to_string(index=False)
)


# ============================================================
# METRICS
# ============================================================

protected = (
    df["Masking_Status"] == "Protected"
).sum()

not_protected = (
    df["Masking_Status"] == "Not Protected"
).sum()

not_required = (
    df["Masking_Status"] == "Not Required"
).sum()


total_sensitive = protected + not_protected

protection_rate = (
    protected / total_sensitive * 100
    if total_sensitive > 0
    else 100
)


print("\n========================================")
print("              METRICS")
print("========================================")

print(f"Protected Fields     : {protected}")
print(f"Not Protected Fields : {not_protected}")
print(f"Not Required Fields  : {not_required}")
print(f"Protection Rate      : {protection_rate:.2f}%")


# ============================================================
# FINAL PUBLICATION DECISION
# ============================================================

print("\n========================================")
print("        FINAL PUBLICATION")
print("========================================")

if not_protected > 0:

    print("❌ PUBLICATION BLOCKED")
    print(
        "Reason: One or more sensitive fields "
        "are not properly masked."
    )

else:

    print("✅ PUBLICATION APPROVED")
    print(
        "All sensitive fields are properly protected."
    )