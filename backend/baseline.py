import pandas as pd

# Load dataset
df = pd.read_csv("../data/validation_dataset.csv")

# Simple baseline rules
def detect_sensitive_field(field_name):
    field = field_name.lower()

    if "email" in field or "mail" in field:
        return "Email"

    elif "phone" in field or "mobile" in field:
        return "Phone"

    elif "card" in field or "cc" in field:
        return "Card"

    elif "name" in field:
        return "Name"

    else:
        return "Normal"


# Apply detection
df["Detected_Type"] = df["Field_Name"].apply(detect_sensitive_field)

# Compare with expected type
df["Correct"] = df["Detected_Type"] == df["Expected_Type"]

# Display result
print("\n--- BASELINE RESULTS ---\n")

print(df[
    ["Organisation",
     "Partner",
     "Field_Name",
     "Expected_Type",
     "Detected_Type",
     "Correct"]
].to_string(index=False))

# Accuracy
accuracy = df["Correct"].mean() * 100

print("\nBaseline Accuracy:", round(accuracy, 2), "%")