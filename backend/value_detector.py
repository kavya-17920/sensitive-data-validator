import pandas as pd
import re

# Load dataset
df = pd.read_csv("../data/validation_dataset.csv")


# Detect sensitive type using actual value
def detect_by_value(value):

    value = str(value).strip()

    # Empty value
    if not value:
        return "Normal"

    # Email pattern
    if re.fullmatch(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        value
    ):
        return "Email"

    # Phone pattern
    elif re.fullmatch(r"\d{10}", value):
        return "Phone"

    # Card number pattern
    elif re.fullmatch(r"\d{16}", value):
        return "Card"

    # Name pattern
    elif re.fullmatch(r"[A-Za-z]+(?:[ .'-][A-Za-z]+)*", value):
        return "Name"

    # Otherwise normal field
    else:
        return "Normal"


# Apply value detection
df["Value_Detected_Type"] = df["Sample_Value"].apply(
    detect_by_value
)


# Compare with expected type
df["Value_Correct"] = (
    df["Value_Detected_Type"] == df["Expected_Type"]
)


# Display result
print("\n--- VALUE PATTERN RESULTS ---\n")

print(
    df[
        [
            "Field_Name",
            "Sample_Value",
            "Expected_Type",
            "Value_Detected_Type",
            "Value_Correct"
        ]
    ].to_string(index=False)
)


# Calculate accuracy
accuracy = df["Value_Correct"].mean() * 100

print(
    "\nValue Pattern Accuracy:",
    round(accuracy, 2),
    "%"
)