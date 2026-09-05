import pandas as pd
import re

# Load dataset
df = pd.read_csv("../data/validation_dataset.csv")


# Field name detection
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

    else:
        return "Unknown"


# Value pattern detection
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


# Hybrid detection
def hybrid_detection(field_name, sample_value):

    field_result = detect_by_field_name(field_name)
    value_result = detect_by_value(sample_value)

    # Both agree, but they must contain useful evidence
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

    # No evidence = Normal
    return "Normal"


# Apply hybrid detection
df["Hybrid_Detected_Type"] = df.apply(
    lambda row: hybrid_detection(
        row["Field_Name"],
        row["Sample_Value"]
    ),
    axis=1
)


# Check correctness
df["Hybrid_Correct"] = (
    df["Hybrid_Detected_Type"]
    == df["Expected_Type"]
)


# Display results
print("\n--- HYBRID DETECTION RESULTS ---\n")

print(
    df[
        [
            "Field_Name",
            "Sample_Value",
            "Expected_Type",
            "Hybrid_Detected_Type",
            "Hybrid_Correct"
        ]
    ].to_string(index=False)
)


# Accuracy
accuracy = (
    df["Hybrid_Correct"].mean() * 100
)

print(
    "\nHybrid Accuracy:",
    round(accuracy, 2),
    "%"
)