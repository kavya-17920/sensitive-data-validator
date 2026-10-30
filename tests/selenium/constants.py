"""
constants.py — Shared URL constants for Sensitive Data Validator Selenium tests.
Imported by all test files and page objects.
"""
import os

# Frontend index.html path (opened as file:// URL — no server needed)
FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "fronted")
)
FRONTEND_URL = "file:///" + FRONTEND_DIR.replace("\\", "/") + "/index.html"

# FastAPI backend
BACKEND_URL = "http://127.0.0.1:8000"
DASHBOARD_URL = f"{BACKEND_URL}/dashboard"
API_DOCS_URL  = f"{BACKEND_URL}/docs"
