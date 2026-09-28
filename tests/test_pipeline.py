"""
test_pipeline.py
----------------
Unit tests for final_decision() and end-to-end pipeline scenarios.

Tests cover:
  - Individual final_decision() logic (type match, masking, access)
  - Parametrized end-to-end scenarios exercising the full stack of
    detect_field → check_masking → check_access → final_decision
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from api import (  # noqa: E402
    detect_field,
    check_masking,
    check_access,
    final_decision,
)


# ============================================================
# TEST CLASS: final_decision()
# ============================================================

class TestFinalDecision:
    """Unit tests for the final_decision() function."""

    def test_allow_when_all_pass(self):
        """
        Types match + masking Protected + FULL ACCESS → ALLOW.
        """
        result = final_decision("Email", "Email", "Protected", "FULL ACCESS")
        assert result == "ALLOW"

    def test_allow_masked_access(self):
        """
        Types match + masking Protected + MASKED ACCESS → ALLOW.
        """
        result = final_decision("Phone", "Phone", "Protected", "MASKED ACCESS")
        assert result == "ALLOW"

    def test_allow_not_required_masking(self):
        """
        Types match + masking Not Required + FULL ACCESS → ALLOW.
        """
        result = final_decision("Normal", "Normal", "Not Required", "FULL ACCESS")
        assert result == "ALLOW"

    def test_block_on_type_mismatch(self):
        """
        detected_type != expected_type → BLOCK regardless of everything else.
        """
        result = final_decision("Phone", "Email", "Protected", "FULL ACCESS")
        assert result == "BLOCK"

    def test_block_on_masking_failure(self):
        """
        Type match but masking is 'Not Protected' → BLOCK.
        """
        result = final_decision("Card", "Card", "Not Protected", "FULL ACCESS")
        assert result == "BLOCK"

    def test_block_on_access_denied(self):
        """
        Type match + masking OK but ACCESS DENIED → BLOCK.
        """
        result = final_decision("Email", "Email", "Protected", "ACCESS DENIED")
        assert result == "BLOCK"

    def test_block_on_both_masking_and_access_failure(self):
        """
        Both masking failure and access denied → BLOCK (fails on masking first).
        """
        result = final_decision("Card", "Card", "Not Protected", "ACCESS DENIED")
        assert result == "BLOCK"

    def test_case_insensitive_type_comparison(self):
        """
        final_decision normalises types with .title() so 'email'/'Email' match.
        """
        result = final_decision("email", "Email", "Protected", "FULL ACCESS")
        assert result == "ALLOW"


# ============================================================
# TEST CLASS: End-to-End pipeline (parametrized)
# ============================================================

# Parametrize columns:
#   (description, field_name, sample_value, expected_type,
#    expected_masking, actual_value, role, expected_decision)

_E2E_SCENARIOS = [
    (
        "email_analyst_allow",
        "email", "kavya@gmail.com", "Email",
        "k***@gmail.com", "k***@gmail.com",
        "Analyst", "ALLOW",
    ),
    (
        "phone_manager_block_unmasked",
        "phone", "9876543210", "Phone",
        "9876543210", "9876543210",  # invalid mask format → Not Protected
        "Manager", "BLOCK",
    ),
    (
        "card_admin_allow",
        "card_number", "4532123412345678", "Card",
        # Admin sees raw value; but check_masking uses expected_masking.
        # None → Not Required, Admin still gets FULL ACCESS.
        None, "4532123412345678",
        "Admin", "ALLOW",
    ),
    (
        "name_admin_allow",
        "customer_name", "Kavya Sharma", "Name",
        None, "Kavya Sharma",
        "Admin", "ALLOW",
    ),
    (
        "normal_analyst_allow",
        "transaction_id", "TXN001", "Normal",
        None, "TXN001",
        "Analyst", "ALLOW",
    ),
]


class TestEndToEndPipeline:
    """
    Parametrized end-to-end tests that drive the full pipeline:
    detect_field → check_masking → check_access → final_decision.
    """

    @pytest.mark.parametrize(
        "description,field_name,sample_value,expected_type,"
        "expected_masking,actual_value,role,expected_decision",
        _E2E_SCENARIOS,
        ids=[s[0] for s in _E2E_SCENARIOS],
    )
    def test_pipeline_scenario(
        self,
        description,
        field_name,
        sample_value,
        expected_type,
        expected_masking,
        actual_value,
        role,
        expected_decision,
    ):
        """Run one end-to-end scenario through the full pipeline."""
        detected_type = detect_field(field_name, sample_value)
        masking_status = check_masking(expected_masking, actual_value, expected_type)
        access_result = check_access(role, detected_type, actual_value)
        decision = final_decision(
            detected_type, expected_type, masking_status, access_result
        )

        assert decision == expected_decision, (
            f"[{description}] Expected '{expected_decision}', got '{decision}'. "
            f"detected={detected_type}, masking={masking_status}, "
            f"access={access_result}"
        )
