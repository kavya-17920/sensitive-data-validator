"""
test_security_scenarios.py — Selenium tests for security validation scenarios (C & D groups).

These tests submit the validation form and verify the displayed result.

IMPORTANT: These tests require the FastAPI backend to be running at
http://127.0.0.1:8000. They are skipped automatically if the backend
is not available, to prevent false failures in offline environments.

Tests use only dummy test data — no real personal or financial information.

C — Sensitive Data Scenarios:
  C1  Valid masked email                   → ALLOW
  C2  Valid masked phone                   → ALLOW
  C3  Valid masked card                    → ALLOW
  C4  Valid masked name (Admin)            → ALLOW
  C5  Unmasked phone (Manager)             → BLOCK
  C6  Wrong expected type                  → BLOCK
  C7  Normal field, no masking             → ALLOW
  C8  Unmasked card (Analyst)              → BLOCK

D — Role-Based Access Scenarios:
  D1  Admin — full access to email         → ALLOW
  D2  Manager — masked access to phone     → ALLOW
  D3  Analyst — masked access to card      → ALLOW
  D4  Invalid role (Guest not in dropdown) → tested via API mismatch simulation
"""

import sys
import os
import time
import pytest
import requests

sys.path.insert(0, os.path.dirname(__file__))

from constants import FRONTEND_URL, BACKEND_URL
from pages.validation_page import ValidationPage


# ---------------------------------------------------------------------------
# Backend availability check — skip all live tests if backend is offline
# ---------------------------------------------------------------------------

def _backend_is_up() -> bool:
    try:
        r = requests.get(BACKEND_URL, timeout=3)
        return r.status_code == 200
    except Exception:
        return False


BACKEND_SKIP = pytest.mark.skipif(
    not _backend_is_up(),
    reason="FastAPI backend is not running at http://127.0.0.1:8000 — skipping live tests"
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def submit_and_get_decision(driver, **kwargs) -> str:
    """Fill the form, submit, wait for result and return ALLOW/BLOCK."""
    page = ValidationPage(driver)
    page.open(FRONTEND_URL)
    page.fill_and_submit(**kwargs)
    page.wait_for_result()
    return page.get_publication_decision()


# ---------------------------------------------------------------------------
# C — Sensitive Data Validation Scenarios
# ---------------------------------------------------------------------------

class TestSensitiveDataScenarios:
    """C — Sensitive data validation end-to-end scenarios."""

    @BACKEND_SKIP
    def test_C1_valid_masked_email_analyst_allow(self, driver):
        """C1: Valid masked email + Analyst → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="email", sample_value="test@example.com",
            expected_type="Email", expected_masking="t***@example.com",
            access_role="Analyst", actual_value="t***@example.com",
        )
        assert decision == "ALLOW", f"Expected ALLOW for masked email, got {decision}"

    @BACKEND_SKIP
    def test_C2_valid_masked_phone_manager_allow(self, driver):
        """C2: Valid masked phone + Manager → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="phone", sample_value="9876543210",
            expected_type="Phone", expected_masking="******3210",
            access_role="Manager", actual_value="******3210",
        )
        assert decision == "ALLOW", f"Expected ALLOW for masked phone, got {decision}"

    @BACKEND_SKIP
    def test_C3_valid_masked_card_manager_allow(self, driver):
        """C3: Valid masked card number + Manager → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="card_number", sample_value="4532123412345678",
            expected_type="Card", expected_masking="************5678",
            access_role="Manager", actual_value="************5678",
        )
        assert decision == "ALLOW", f"Expected ALLOW for masked card, got {decision}"

    @BACKEND_SKIP
    def test_C4_admin_name_no_masking_allow(self, driver):
        """C4: Admin accessing name field (no masking required) → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="customer_name", sample_value="Test User",
            expected_type="Name", expected_masking="none",
            access_role="Admin", actual_value="Test User",
        )
        assert decision == "ALLOW", f"Expected ALLOW for Admin name access, got {decision}"

    @BACKEND_SKIP
    def test_C5_unmasked_phone_manager_block(self, driver):
        """C5: Raw unmasked phone for Manager → BLOCK (masking failure)."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="phone", sample_value="9876543210",
            expected_type="Phone", expected_masking="9876543210",
            access_role="Manager", actual_value="9876543210",
        )
        assert decision == "BLOCK", f"Expected BLOCK for unmasked phone, got {decision}"

    @BACKEND_SKIP
    def test_C6_wrong_expected_type_block(self, driver):
        """C6: Expected type=Card but field is Phone → type mismatch → BLOCK."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="phone", sample_value="9876543210",
            expected_type="Card", expected_masking="none",
            access_role="Admin", actual_value="9876543210",
        )
        assert decision == "BLOCK", f"Expected BLOCK for type mismatch, got {decision}"

    @BACKEND_SKIP
    def test_C7_normal_field_allow(self, driver):
        """C7: Normal field (amount) with no masking, Analyst → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="amount", sample_value="5000",
            expected_type="Normal", expected_masking="none",
            access_role="Analyst", actual_value="5000",
        )
        assert decision == "ALLOW", f"Expected ALLOW for normal field, got {decision}"

    @BACKEND_SKIP
    def test_C8_unmasked_card_analyst_block(self, driver):
        """C8: Raw card number shown to Analyst → BLOCK (no masking applied)."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="card_number", sample_value="4532123412345678",
            expected_type="Card", expected_masking="4532123412345678",
            access_role="Analyst", actual_value="4532123412345678",
        )
        assert decision == "BLOCK", f"Expected BLOCK for unmasked card, got {decision}"


# ---------------------------------------------------------------------------
# D — Role-Based Access Scenarios
# ---------------------------------------------------------------------------

class TestRoleBasedAccess:
    """D — Role-based access control scenarios via the UI form."""

    @BACKEND_SKIP
    def test_D1_admin_email_full_access(self, driver):
        """D1: Admin accesses email with no masking required → ALLOW (FULL ACCESS)."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="email", sample_value="test@example.com",
            expected_type="Email", expected_masking="none",
            access_role="Admin", actual_value="test@example.com",
        )
        assert decision == "ALLOW", f"Expected ALLOW for Admin email, got {decision}"

    @BACKEND_SKIP
    def test_D2_manager_masked_phone_allow(self, driver):
        """D2: Manager receives properly masked phone → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="phone", sample_value="9876543210",
            expected_type="Phone", expected_masking="******3210",
            access_role="Manager", actual_value="******3210",
        )
        assert decision == "ALLOW", f"Expected ALLOW for Manager masked phone, got {decision}"

    @BACKEND_SKIP
    def test_D3_analyst_masked_card_allow(self, driver):
        """D3: Analyst receives properly masked card → ALLOW."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="card_number", sample_value="4532123412345678",
            expected_type="Card", expected_masking="************5678",
            access_role="Analyst", actual_value="************5678",
        )
        assert decision == "ALLOW", f"Expected ALLOW for Analyst masked card, got {decision}"

    @BACKEND_SKIP
    def test_D4_manager_unmasked_email_block(self, driver):
        """D4: Manager receives raw unmasked email → BLOCK (access denied)."""
        decision = submit_and_get_decision(
            driver,
            organisation="TestOrg", partner="PayX",
            field_name="email", sample_value="test@example.com",
            expected_type="Email", expected_masking="test@example.com",
            access_role="Manager", actual_value="test@example.com",
        )
        assert decision == "BLOCK", f"Expected BLOCK for unmasked email to Manager, got {decision}"
