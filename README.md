# Sensitive Data Validator

## Project Overview

Sensitive Data Validator is a security-focused application designed to
detect sensitive data, validate masking, enforce role-based access control,
and decide whether data is safe for analytics publication.

The system helps prevent unauthorized exposure of sensitive information.

## Objectives

- Detect sensitive data fields
- Validate masking of sensitive information
- Enforce role-based access control
- Prevent unauthorized sensitive data exposure
- Allow or block analytics publication
- Generate security validation metrics

## Sensitive Data Detection

The system detects the following data types:

- Email
- Phone
- Card
- Name
- Normal

Detection is performed using:

- Field-name based detection
- Value-pattern based detection
- Hybrid detection

## Masking Validation

The system checks whether sensitive information is properly masked before
analytics publication.

Possible results:

- Protected
- Not Protected
- Not Required

## Access Control

The system supports three user roles:

| Role | Sensitive Data Access |
|------|------------------------|
| Admin | Full Access |
| Manager | Masked Access |
| Analyst | Masked Access |

Unrecognized roles are denied access.

## Publication Decision

The system produces one final decision:

- ALLOW
- BLOCK

Publication is blocked when:

- Sensitive data is not properly masked
- Access is denied
- Detected type does not match the expected type

## System Architecture

```text
User Input
    ↓
Sensitive Data Detection
    ↓
Masking Validation
    ↓
Access Control
    ↓
Security Decision
    ↓
ALLOW / BLOCK

raale project
│
├── README.md
│
├── backend
│   ├── api.py
│   ├── access_validator.py
│   ├── baseline.py
│   ├── hybrid_detector.py
│   ├── masking_validator.py
│   ├── metrics.py
│   └── pipeline.py
│
├── data
│   ├── failure_dataset.csv
│   └── validation_dataset.csv
│
├── fronted
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── models
│
└── repots
    └── Validation_Test_Report.md

How to Run
1. Start Backend

Open the terminal inside the backend folder:

python -m uvicorn api:app --reload

The backend will run at:

http://127.0.0.1:8000
2. Swagger API Documentation

Open the following URL in your browser:

http://127.0.0.1:8000/docs

Swagger can be used to test the validation API.

3. Dashboard

Open:

http://127.0.0.1:8000/dashboard

The dashboard displays detection performance and security metrics.

4. Start Frontend

Open the fronted folder in VS Code.

Right-click:

index.html

Select:

Open with Live Server

The frontend will open in the browser

API Testing

The /validate API was tested using Swagger UI.

ALLOW Test
Email
    ↓
Protected Masking
    ↓
Analyst
    ↓
MASKED ACCESS
    ↓
ALLOW
BLOCK Test
Phone
    ↓
Unmasked Value
    ↓
Masking Failure
    ↓
ACCESS DENIED
    ↓
BLOCK

Both API scenarios returned:

HTTP 200 OK
Security Metrics

The system calculates:

Total Fields
Sensitive Fields
Protected Fields
Masking Failures
Access Denied
Allowed Fields
Blocked Fields
Protection Rate
Detection Accuracy
Detection Performance

The validated detection performance is:

Baseline Accuracy        : 87.50%
Value Detector Accuracy  : 87.50%
Hybrid Accuracy          : 100.00%
Improvement               : +12.50%
Security Validation Metrics
Total Fields              : 9
Sensitive Fields          : 8
Protected Fields          : 5
Masking Failures          : 3
Access Denied             : 3
Allowed                   : 5
Blocked                   : 4
Protection Rate           : 62.50%
Final Result

The system successfully validates:

Sensitive data detection
Masking protection
Role-based access
Detection consistency
Analytics publication security

Unsafe or unauthorized data is blocked from publication.

Conclusion

Sensitive Data Validator provides an automated security validation
pipeline that combines sensitive data detection, masking validation,
role-based access control, and analytics publication control.

The system is designed to reduce the risk of exposing sensitive information during analytics and data processing.