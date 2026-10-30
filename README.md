# Sensitive Data Validator

## Project Overview

Sensitive Data Validator is a security-focused application that detects sensitive data, validates masking, enforces role-based access control, and decides whether data is safe for analytics publication.

---

## Project Structure

```
raale project/
├── backend/
│   ├── api.py                        ← FastAPI app + core validation logic
│   ├── pipeline.py                   ← Batch CSV pipeline runner
│   ├── schema_drift_handler.py       ← Schema drift detection module
│   ├── baseline.py / hybrid_detector.py / masking_validator.py
│   ├── value_detector.py / access_validator.py / metrics.py
├── data/
│   ├── validation_dataset.csv        ← 8-row original dataset
│   ├── failure_dataset.csv           ← 9-row failure scenarios
│   └── expanded_benchmark.csv        ← 69-row expanded benchmark
├── fronted/
│   ├── index.html / style.css / script.js
├── tests/
│   ├── test_detection.py / test_masking.py / test_access.py
│   ├── test_pipeline.py / test_schema_drift.py / test_api_integration.py
│   └── selenium/
│       ├── conftest.py               ← Chrome WebDriver fixture
│       ├── constants.py              ← Shared URL constants
│       ├── pages/
│       │   ├── dashboard_page.py     ← Page Object Model: index.html
│       │   └── validation_page.py   ← Page Object Model: validation form
│       ├── test_dashboard.py         ← 10 UI tests (A group)
│       ├── test_validation_form.py   ← 12 form tests (B group)
│       ├── test_security_scenarios.py← 12 security tests (C+D group)
│       ├── test_navigation.py        ← 7 navigation tests (F group)
│       └── reports/
│           ├── selenium_report.html  ← HTML test report
│           └── screenshots/          ← Auto-saved failure screenshots
├── .github/workflows/ci.yml          ← GitHub Actions CI/CD (4 jobs)
└── requirements.txt
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic, pandas |
| Frontend | HTML, CSS, JavaScript |
| API Testing | pytest, httpx, FastAPI TestClient |
| UI Automation | Selenium 4.52, Chrome WebDriver |
| Test Reports | pytest-html |
| CI/CD | GitHub Actions |

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
cd backend
python -m uvicorn api:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

### 3. Open the Frontend

Open `fronted/index.html` with Live Server in VS Code, or open directly in browser.

### 4. API Documentation (Swagger)

```
http://127.0.0.1:8000/docs
```

### 5. Dashboard

```
http://127.0.0.1:8000/dashboard
```

---

## Sensitive Data Detection

Detects: **Email, Phone, Card, Name, Normal**

Detection strategy:
- Field-name substring matching
- Value regex pattern matching
- Hybrid (both agree → use it; fallback to stronger signal)

---

## Masking Validation

| Type | Valid Mask Example |
|---|---|
| Email | `k***@gmail.com` |
| Phone | `******3210` |
| Card | `************5678` |
| Name | `K***` |
| Normal | Not required |

Results: **Protected / Not Protected / Not Required**

---

## Access Control

| Role | Sensitive Fields | Normal Fields |
|---|---|---|
| Admin | FULL ACCESS | FULL ACCESS |
| Manager | MASKED ACCESS | FULL ACCESS |
| Analyst | MASKED ACCESS | FULL ACCESS |
| (Invalid) | ACCESS DENIED | ACCESS DENIED |

---

## Publication Decision

- **ALLOW** — all checks pass
- **BLOCK** — type mismatch / masking failure / access denied

---

## Running Unit Tests (pytest)

```bash
# Run all unit and integration tests
python -m pytest tests/ -v --ignore=tests/selenium

# Run with coverage
python -m pytest tests/ -v --ignore=tests/selenium --cov=backend --cov-report=term-missing
```

**84+ tests** across 6 files: detection, masking, access, pipeline, schema drift, API integration.

---

## Selenium Automation Testing

### What is Selenium?

Selenium is a browser automation framework that controls real browsers (Chrome, Firefox, Edge) programmatically. It simulates user interactions — clicking, typing, scrolling — to test web applications end-to-end.

### Why Selenium in This Project?

- Validates that the HTML form fields are correctly rendered
- Tests that form submission triggers the FastAPI backend correctly
- Verifies security results (ALLOW/BLOCK) displayed in the browser
- Tests role-based access scenarios through the actual UI
- Catches frontend regressions that API-only tests would miss

### Selenium Architecture

```
Test File (test_dashboard.py etc.)
    ↓
Page Object (dashboard_page.py / validation_page.py)
    ↓
Selenium WebDriver (Chrome - Headless)
    ↓
Browser (renders fronted/index.html)
    ↓
JavaScript fetch() → FastAPI /validate
    ↓
Result displayed in #resultContent
    ↓
Assertion on DOM element text
```

**Pattern used:** Page Object Model (POM) — separates locators from test logic.

### Install Selenium

Already included in `requirements.txt`:

```
selenium>=4.15.0
pytest-html>=4.0.0
requests>=2.31.0
```

Selenium Manager (bundled since Selenium 4.6) automatically downloads the correct ChromeDriver — no manual setup needed.

### Run Selenium Tests

```bash
# Run all Selenium tests (C/D groups skip if backend is offline)
python -m pytest tests/selenium/ -v

# Run with HTML report
python -m pytest tests/selenium/ -v --html=tests/selenium/reports/selenium_report.html --self-contained-html

# Run with backend (all 41 tests active)
# Terminal 1:
cd backend && python -m uvicorn api:app --reload
# Terminal 2:
python -m pytest tests/selenium/ -v
```

### Selenium Test Cases

#### A — Dashboard Tests (10 tests) — `test_dashboard.py`

| Test | Description |
|---|---|
| A1 | Page title contains "Sensitive Data Validator" |
| A2 | Brand heading in topbar is correct |
| A3 | System Active status is displayed |
| A4 | Hero section heading is visible |
| A5 | Exactly 4 metric cards are present |
| A6 | Metric card values (87.5%, 100%, etc.) are non-empty |
| A7 | Validator section (form) is present |
| A8 | All 8 form fields are visible |
| A9 | Submit button is visible |
| A10 | Footer is present |

#### B — Form Validation Tests (12 tests) — `test_validation_form.py`

| Test | Description |
|---|---|
| B1a–B1h | All 8 form fields visible with correct placeholders and options |
| B2a | All fields fillable with test data |
| B2b | Form submission shows result (error or response) |
| B2c | Submit button text is correct |
| B2d | Start Validation button scrolls to form |

#### C — Security Scenarios (8 tests) — `test_security_scenarios.py`

| Test | Scenario | Expected |
|---|---|---|
| C1 | Valid masked email + Analyst | ALLOW |
| C2 | Valid masked phone + Manager | ALLOW |
| C3 | Valid masked card + Manager | ALLOW |
| C4 | Admin + Name, no masking | ALLOW |
| C5 | Unmasked phone + Manager | BLOCK |
| C6 | Wrong expected type | BLOCK |
| C7 | Normal field (amount) | ALLOW |
| C8 | Unmasked card + Analyst | BLOCK |

#### D — Role-Based Access Tests (4 tests) — `test_security_scenarios.py`

| Test | Scenario | Expected |
|---|---|---|
| D1 | Admin — email full access | ALLOW |
| D2 | Manager — masked phone | ALLOW |
| D3 | Analyst — masked card | ALLOW |
| D4 | Manager — unmasked email | BLOCK |

#### F — Navigation Tests (7 tests) — `test_navigation.py`

| Test | Description |
|---|---|
| F1 | Frontend page loads at file:// URL |
| F2 | Page title is correct |
| F3 | Backend GET / returns 200 |
| F4 | /docs Swagger page loads |
| F5 | /dashboard endpoint loads |
| F6 | Start Validation button scrolls to form |
| F7 | All page sections (hero, metrics, form, result, footer) present |

### Test Execution Output

```
collected 41 items

tests/selenium/test_dashboard.py::TestDashboardLoading::test_A1_page_title  PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A2_brand_heading PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A3_system_status_visible PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A4_hero_heading_visible PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A5_four_metric_cards PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A6_metric_card_values_not_empty PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A7_validator_section_present PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A8_all_form_fields_visible PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A9_submit_button_visible PASSED
tests/selenium/test_dashboard.py::TestDashboardLoading::test_A10_footer_present PASSED
...
================== 26 passed, 15 skipped in 94.46s ==================
```

### Test Report Location

```
tests/selenium/reports/selenium_report.html     ← HTML report
tests/selenium/reports/screenshots/             ← Failure screenshots
```

---

## CI/CD Pipeline (GitHub Actions)

4-job pipeline on every push to `main`:

```
Job 1: Lint (flake8)
    ↓
Job 2: Unit Tests (pytest, Python 3.10 + 3.11 matrix)
    ↓
Job 3: Benchmark (pipeline.py)
    ↓
Job 4: Selenium UI Tests (headless Chrome)
         → Uploads selenium_report.html as artifact
         → Uploads screenshots/ as artifact
```

---

## GitHub Repository

**URL:** https://github.com/kavya-17920/sensitive-data-validator

**Key Commits:**

| Commit | Description |
|---|---|
| `b267caf` | Expanded benchmark (69 rows), schema drift handler, 84+ tests, CI/CD |
| `598b564` | Fixed flake8 lint CI failure |
| `a74625d` | Added Selenium automation framework (26/41 tests pass locally) |

---

## Security Metrics (Original Dataset)

| Metric | Value |
|---|---|
| Baseline Accuracy | 87.5% |
| Hybrid Accuracy | 100% |
| Improvement | +12.5% |
| Protection Rate | 62.5% |

---

## Conclusion

Sensitive Data Validator provides an automated security validation pipeline combining:

- Hybrid PII detection (field-name + value pattern)
- Masking format validation
- Role-based access control
- Analytics publication decision (ALLOW / BLOCK)
- Schema drift handling for fintech partner integrations
- 84+ unit/integration tests + 41 Selenium UI tests
- 4-job GitHub Actions CI/CD pipeline

Unsafe or unauthorized data is blocked from publication.