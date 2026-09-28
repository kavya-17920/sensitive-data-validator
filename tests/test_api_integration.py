"""
test_api_integration.py
-----------------------
Integration tests for the FastAPI application in api.py.

Uses FastAPI's built-in TestClient (backed by httpx) to exercise the
full HTTP request/response cycle without spinning up a real server.

Tests cover:
  - POST /validate  → happy-path ALLOWs and various BLOCK conditions
  - GET /           → home endpoint liveness check
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient  # noqa: E402
from api import app  # noqa: E402

# Shared test client (one ASGI app instance for all tests)
client = TestClient(app)


# ============================================================
# HELPER
# ============================================================

def _validate(
    field_name: str,
    sample_value: str,
    expected_type: str,
    expected_masking: str,
    access_role: str,
    actual_value: str,
    organisation: str = "TestOrg",
    partner: str = "TestPartner",
) -> dict:
    """POST /validate and return the parsed JSON response body."""
    payload = {
        "organisation": organisation,
        "partner": partner,
        "field_name": field_name,
        "sample_value": sample_value,
        "expected_type": expected_type,
        "expected_masking": expected_masking,
        "access_role": access_role,
        "actual_value": actual_value,
    }
    response = client.post("/validate", json=payload)
    assert response.status_code == 200, (
        f"Expected HTTP 200 but got {response.status_code}: {response.text}"
    )
    return response.json()


# ============================================================
# TEST CLASS: POST /validate
# ============================================================

class TestValidateEndpoint:
    """Integration tests for the POST /validate endpoint."""

    def test_email_analyst_allow(self):
        """
        Valid masked email presented by an Analyst → publication ALLOW.
        """
        body = _validate(
            field_name="email",
            sample_value="kavya@gmail.com",
            expected_type="Email",
            expected_masking="k***@gmail.com",
            access_role="Analyst",
            actual_value="k***@gmail.com",
        )
        assert body["detected_type"] == "Email"
        assert body["masking_status"] == "Protected"
        assert body["access_result"] == "MASKED ACCESS"
        assert body["publication"] == "ALLOW"

    def test_phone_manager_block_unmasked(self):
        """
        Unmasked phone number presented by a Manager → publication BLOCK.
        (Raw 10-digit value is not a valid mask format.)
        """
        body = _validate(
            field_name="phone",
            sample_value="9876543210",
            expected_type="Phone",
            expected_masking="9876543210",   # not a valid mask
            access_role="Manager",
            actual_value="9876543210",
        )
        assert body["detected_type"] == "Phone"
        assert body["masking_status"] == "Not Protected"
        assert body["publication"] == "BLOCK"

    def test_card_admin_allow(self):
        """
        Admin accesses a raw card number; masking is 'none' (not required).
        Types match → ALLOW.
        """
        body = _validate(
            field_name="card_number",
            sample_value="4532123412345678",
            expected_type="Card",
            expected_masking="none",   # no masking required
            access_role="Admin",
            actual_value="4532123412345678",
        )
        assert body["detected_type"] == "Card"
        assert body["masking_status"] == "Not Required"
        assert body["access_result"] == "FULL ACCESS"
        assert body["publication"] == "ALLOW"

    def test_invalid_role_block(self):
        """
        An unrecognised role ('Guest') → ACCESS DENIED → BLOCK.
        """
        body = _validate(
            field_name="email",
            sample_value="kavya@gmail.com",
            expected_type="Email",
            expected_masking="k***@gmail.com",
            access_role="Guest",
            actual_value="k***@gmail.com",
        )
        assert body["access_result"] == "ACCESS DENIED"
        assert body["publication"] == "BLOCK"

    def test_type_mismatch_block(self):
        """
        expected_type='Card' but the field+value clearly indicate Phone
        → type mismatch → BLOCK.
        """
        body = _validate(
            field_name="phone",
            sample_value="9876543210",
            expected_type="Card",       # deliberate mismatch
            expected_masking="none",
            access_role="Admin",
            actual_value="9876543210",
        )
        assert body["detected_type"] == "Phone"
        assert body["publication"] == "BLOCK"

    def test_name_admin_allow(self):
        """Admin accessing a name field with no masking required → ALLOW."""
        body = _validate(
            field_name="customer_name",
            sample_value="Kavya Sharma",
            expected_type="Name",
            expected_masking="none",
            access_role="Admin",
            actual_value="Kavya Sharma",
        )
        assert body["detected_type"] == "Name"
        assert body["publication"] == "ALLOW"

    def test_normal_field_analyst_allow(self):
        """Normal field (amount) for any valid role → ALLOW."""
        body = _validate(
            field_name="amount",
            sample_value="500",
            expected_type="Normal",
            expected_masking="none",
            access_role="Analyst",
            actual_value="500",
        )
        assert body["detected_type"] == "Normal"
        assert body["publication"] == "ALLOW"

    def test_response_contains_org_partner(self):
        """Response body echoes the organisation and partner fields."""
        body = _validate(
            field_name="amount",
            sample_value="100",
            expected_type="Normal",
            expected_masking="none",
            access_role="Admin",
            actual_value="100",
            organisation="FinCorp",
            partner="DataPartnerX",
        )
        assert body["organisation"] == "FinCorp"
        assert body["partner"] == "DataPartnerX"


# ============================================================
# TEST CLASS: GET /
# ============================================================

class TestHomeEndpoint:
    """Tests for the GET / (home) endpoint."""

    def test_home_returns_200(self):
        """Home endpoint should return HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_message(self):
        """Home endpoint should return a JSON message body."""
        response = client.get("/")
        body = response.json()
        assert "message" in body
        assert "running" in body["message"].lower()
