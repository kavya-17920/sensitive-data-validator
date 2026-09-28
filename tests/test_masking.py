"""
test_masking.py
---------------
Unit tests for is_valid_masking() and check_masking() from api.py.

Tests cover:
  - Email, Phone, Card, Name masking validation rules
  - Normal fields (no masking required)
  - check_masking() with None, valid, and invalid expected_masking inputs
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from api import is_valid_masking, check_masking  # noqa: E402


# ============================================================
# TEST CLASS: is_valid_masking()
# ============================================================

class TestMaskingValidation:
    """Tests for the is_valid_masking() function."""

    # ---- Email ----

    def test_email_valid_mask(self):
        """A leading char followed by stars then @domain is valid."""
        assert is_valid_masking("Email", "k***@gmail.com") is True

    def test_email_valid_mask_longer_local(self):
        """Longer masked local part is also valid."""
        assert is_valid_masking("Email", "u****@company.org") is True

    def test_email_invalid_mask_full(self):
        """A fully unmasked email is NOT a valid mask."""
        assert is_valid_masking("Email", "kavya@gmail.com") is False

    def test_email_invalid_mask_all_stars(self):
        """All stars without @ and domain is NOT valid for Email."""
        assert is_valid_masking("Email", "****") is False

    # ---- Phone ----

    def test_phone_valid_mask_last4(self):
        """Stars followed by 4 trailing digits → valid Phone mask."""
        assert is_valid_masking("Phone", "******3210") is True

    def test_phone_valid_mask_all_stars(self):
        """All stars → valid Phone mask."""
        assert is_valid_masking("Phone", "**********") is True

    def test_phone_invalid_mask(self):
        """A raw 10-digit number is NOT a valid Phone mask."""
        assert is_valid_masking("Phone", "9876543210") is False

    def test_phone_valid_mask_four_digit_suffix(self):
        """Any star prefix + exactly 4 digit suffix → valid."""
        assert is_valid_masking("Phone", "******1234") is True

    # ---- Card ----

    def test_card_valid_mask(self):
        """Stars followed by last 4 digits → valid Card mask."""
        assert is_valid_masking("Card", "************5678") is True

    def test_card_valid_mask_all_stars(self):
        """All stars → valid Card mask."""
        assert is_valid_masking("Card", "****************") is True

    def test_card_invalid_mask(self):
        """A raw 16-digit card number is NOT a valid Card mask."""
        assert is_valid_masking("Card", "4532123412345678") is False

    # ---- Name ----

    def test_name_valid_mask(self):
        """Single letter followed by stars → valid Name mask."""
        assert is_valid_masking("Name", "K***") is True

    def test_name_invalid_mask(self):
        """A plain full name is NOT a valid Name mask."""
        assert is_valid_masking("Name", "Kavya") is False

    def test_name_invalid_mask_all_stars(self):
        """Stars without a leading letter are NOT valid for Name."""
        assert is_valid_masking("Name", "****") is False

    # ---- Normal ----

    def test_normal_field_no_mask_required(self):
        """Normal field type always returns True regardless of value."""
        assert is_valid_masking("Normal", "any_value") is True
        assert is_valid_masking("Normal", "") is True
        assert is_valid_masking("Normal", "500") is True


# ============================================================
# TEST CLASS: check_masking()
# ============================================================

class TestCheckMasking:
    """Tests for the check_masking() function."""

    def test_none_masking_not_required(self):
        """
        When expected_masking is Python None the field does not
        require masking → 'Not Required'.
        """
        result = check_masking(None, "kavya@gmail.com", "Email")
        assert result == "Not Required"

    def test_string_none_masking_not_required(self):
        """
        When expected_masking is the string 'none' (case-insensitive)
        the field does not require masking → 'Not Required'.
        """
        result = check_masking("none", "9876543210", "Phone")
        assert result == "Not Required"

    def test_empty_string_masking_not_required(self):
        """Empty string expected_masking → 'Not Required'."""
        result = check_masking("", "Kavya", "Name")
        assert result == "Not Required"

    def test_protected_when_match(self):
        """
        When expected_masking is a valid mask AND actual_value == expected_masking
        → 'Protected'.
        """
        result = check_masking("k***@gmail.com", "k***@gmail.com", "Email")
        assert result == "Protected"

    def test_protected_phone_when_match(self):
        """Phone: valid mask matches actual_value → 'Protected'."""
        result = check_masking("******3210", "******3210", "Phone")
        assert result == "Protected"

    def test_not_protected_when_mismatch(self):
        """
        Expected masking is a valid format but the actual_value is different
        (e.g., a different masked token) → 'Not Protected'.
        """
        result = check_masking("k***@gmail.com", "x***@gmail.com", "Email")
        assert result == "Not Protected"

    def test_invalid_mask_format_not_protected(self):
        """
        If expected_masking does not conform to the valid mask pattern for
        that field type → 'Not Protected' (format check fails first).
        """
        # A raw email is not a valid mask format → Not Protected
        result = check_masking("kavya@gmail.com", "kavya@gmail.com", "Email")
        assert result == "Not Protected"

    def test_card_protected_when_match(self):
        """Card: valid mask matches actual_value → 'Protected'."""
        result = check_masking("************5678", "************5678", "Card")
        assert result == "Protected"

    def test_name_protected_when_match(self):
        """Name: valid mask matches actual_value → 'Protected'."""
        result = check_masking("K***", "K***", "Name")
        assert result == "Protected"
