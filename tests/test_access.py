"""
test_access.py
--------------
Unit tests for check_access() from api.py.

Covers:
  - Admin full-access to all field types
  - Manager and Analyst masked access with valid masks
  - Denial when unmasked sensitive data is presented to non-Admin roles
  - Invalid roles → ACCESS DENIED
  - Normal field → FULL ACCESS for any valid role
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from api import check_access  # noqa: E402


# ============================================================
# TEST CLASS: check_access()
# ============================================================

class TestAccessControl:
    """Tests for the check_access() function."""

    # ---- Admin ----

    def test_admin_full_access_all_types(self):
        """Admin role receives FULL ACCESS for every field type."""
        field_types = {
            "Email": "kavya@gmail.com",
            "Phone": "9876543210",
            "Card": "4532123412345678",
            "Name": "Kavya Sharma",
            "Normal": "500",
        }
        for ftype, value in field_types.items():
            result = check_access("Admin", ftype, value)
            assert result == "FULL ACCESS", (
                f"Admin should get FULL ACCESS for {ftype}, got '{result}'"
            )

    # ---- Manager ----

    def test_manager_masked_access_with_valid_mask(self):
        """Manager + Email + valid mask → MASKED ACCESS."""
        result = check_access("Manager", "Email", "k***@gmail.com")
        assert result == "MASKED ACCESS"

    def test_manager_masked_access_phone(self):
        """Manager + Phone + valid mask → MASKED ACCESS."""
        result = check_access("Manager", "Phone", "******3210")
        assert result == "MASKED ACCESS"

    def test_manager_access_denied_unmasked(self):
        """Manager + Card + raw (unmasked) value → ACCESS DENIED."""
        result = check_access("Manager", "Card", "4532123412345678")
        assert result == "ACCESS DENIED"

    def test_manager_access_denied_unmasked_email(self):
        """Manager + Email + raw email → ACCESS DENIED."""
        result = check_access("Manager", "Email", "kavya@gmail.com")
        assert result == "ACCESS DENIED"

    # ---- Analyst ----

    def test_analyst_masked_access_with_valid_mask(self):
        """Analyst + Phone + valid mask → MASKED ACCESS."""
        result = check_access("Analyst", "Phone", "******3210")
        assert result == "MASKED ACCESS"

    def test_analyst_masked_access_card(self):
        """Analyst + Card + valid mask → MASKED ACCESS."""
        result = check_access("Analyst", "Card", "************5678")
        assert result == "MASKED ACCESS"

    def test_analyst_access_denied_unmasked_name(self):
        """Analyst + Name + raw name → ACCESS DENIED."""
        result = check_access("Analyst", "Name", "Kavya Sharma")
        assert result == "ACCESS DENIED"

    # ---- Normal fields ----

    def test_normal_field_full_access_manager(self):
        """Normal field → FULL ACCESS regardless of role (Manager)."""
        result = check_access("Manager", "Normal", "500")
        assert result == "FULL ACCESS"

    def test_normal_field_full_access_analyst(self):
        """Normal field → FULL ACCESS regardless of role (Analyst)."""
        result = check_access("Analyst", "Normal", "TXN001")
        assert result == "FULL ACCESS"

    # ---- Invalid roles ----

    def test_invalid_role_denied(self):
        """An unrecognised role ('Guest') always gets ACCESS DENIED."""
        result = check_access("Guest", "Email", "k***@gmail.com")
        assert result == "ACCESS DENIED"

    def test_empty_role_denied(self):
        """An empty role string → ACCESS DENIED."""
        result = check_access("", "Phone", "******3210")
        assert result == "ACCESS DENIED"

    def test_lowercase_role_normalised(self):
        """
        check_access normalises the role with .title(), so 'admin'
        should be treated as 'Admin' and return FULL ACCESS.
        """
        result = check_access("admin", "Email", "kavya@gmail.com")
        assert result == "FULL ACCESS"
