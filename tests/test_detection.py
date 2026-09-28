"""
test_detection.py
-----------------
Unit tests for the detect_field() function in api.py.

Covers three detection strategies:
  1. Field-name-based detection
  2. Value-pattern-based detection
  3. Hybrid (combined) detection
"""

import sys
import os

# Ensure backend/ is importable regardless of where pytest is launched from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from api import detect_field  # noqa: E402


# ============================================================
# TEST CLASS: Field-name-based detection
# ============================================================

class TestFieldNameDetection:
    """
    Tests where the field name alone is the dominant signal.
    A neutral sample value ('ABC') is supplied so that value-based
    detection does not interfere.
    """

    _neutral = "ABC"  # triggers value_result = "Name" or falls through

    def test_email_by_name_variants(self):
        """Field names containing 'email' or 'mail' → Email."""
        for field in ["email", "cust_mail", "EmailAddr", "usr_email_addr"]:
            result = detect_field(field, self._neutral)
            assert result == "Email", (
                f"Expected 'Email' for field='{field}', got '{result}'"
            )

    def test_phone_by_name_variants(self):
        """Field names containing 'phone' or 'mobile' → Phone."""
        for field in ["phone", "mobile_no", "contact_phone_num"]:
            result = detect_field(field, self._neutral)
            assert result == "Phone", (
                f"Expected 'Phone' for field='{field}', got '{result}'"
            )

    def test_card_by_name_variants(self):
        """Field names containing 'card' or 'cc' → Card."""
        for field in ["card_number", "cc_no", "cc"]:
            result = detect_field(field, self._neutral)
            assert result == "Card", (
                f"Expected 'Card' for field='{field}', got '{result}'"
            )

    def test_name_by_name_variants(self):
        """Field names containing 'name' or 'nm' → Name."""
        for field in ["cust_nm", "customer_name"]:
            result = detect_field(field, self._neutral)
            assert result == "Name", (
                f"Expected 'Name' for field='{field}', got '{result}'"
            )

    def test_normal_fields(self):
        """Generic field names with neutral values → Normal."""
        for field in ["amount", "transaction_id", "status"]:
            result = detect_field(field, "500")
            assert result == "Normal", (
                f"Expected 'Normal' for field='{field}', got '{result}'"
            )


# ============================================================
# TEST CLASS: Value-pattern-based detection
# ============================================================

class TestValueDetection:
    """
    Tests where the value pattern is the dominant signal.
    A neutral / unknown field name ('data_field') is used so that
    field-name-based detection returns 'Unknown'.
    """

    _unknown_field = "data_field"

    def test_email_value(self):
        """Valid e-mail addresses are detected as Email."""
        for value in ["kavya@gmail.com", "user@sub.domain.co.uk", "a@b.io"]:
            result = detect_field(self._unknown_field, value)
            assert result == "Email", (
                f"Expected 'Email' for value='{value}', got '{result}'"
            )

    def test_phone_value(self):
        """10-digit numeric strings are detected as Phone."""
        for value in ["9876543210", "0000000000", "1234567890"]:
            result = detect_field(self._unknown_field, value)
            assert result == "Phone", (
                f"Expected 'Phone' for value='{value}', got '{result}'"
            )

    def test_card_value(self):
        """16-digit numeric strings are detected as Card."""
        for value in ["4532123412345678", "0000000000000000"]:
            result = detect_field(self._unknown_field, value)
            assert result == "Card", (
                f"Expected 'Card' for value='{value}', got '{result}'"
            )

    def test_name_value(self):
        """Alphabetic strings (with allowed separators) → Name."""
        for value in ["Kavya", "John Doe", "Mary-Jane"]:
            result = detect_field(self._unknown_field, value)
            assert result == "Name", (
                f"Expected 'Name' for value='{value}', got '{result}'"
            )

    def test_normal_value(self):
        """Numeric-only short values / date-like strings → Normal."""
        for value in ["500", "2024-01-15", "TXN001"]:
            result = detect_field(self._unknown_field, value)
            assert result == "Normal", (
                f"Expected 'Normal' for value='{value}', got '{result}'"
            )

    def test_empty_value(self):
        """An empty string value with an unknown field name → Normal."""
        result = detect_field(self._unknown_field, "")
        assert result == "Normal", (
            f"Expected 'Normal' for empty value, got '{result}'"
        )


# ============================================================
# TEST CLASS: Hybrid detection (field + value signals)
# ============================================================

class TestHybridDetection:
    """
    Tests for the hybrid decision logic where field-name and value-pattern
    signals may agree, conflict, or be partially absent.
    """

    def test_both_agree_email(self):
        """Field says Email, value is a valid email → Email."""
        result = detect_field("email", "kavya@gmail.com")
        assert result == "Email"

    def test_both_agree_phone(self):
        """Field says Phone, value is 10-digit → Phone."""
        result = detect_field("phone", "9876543210")
        assert result == "Phone"

    def test_both_agree_card(self):
        """Field says Card, value is 16-digit → Card."""
        result = detect_field("card_number", "4532123412345678")
        assert result == "Card"

    def test_field_unknown_value_strong(self):
        """
        Field name='id' (Unknown), value='9876543210' (Phone pattern).
        Value wins: result should be Phone.
        """
        result = detect_field("id", "9876543210")
        assert result == "Phone", (
            f"Expected 'Phone' (value wins over unknown field), got '{result}'"
        )

    def test_field_email_value_unknown(self):
        """
        Field name='email' (Email), value='5000' (Unknown pattern).
        Field wins: result should be Email.
        """
        result = detect_field("email", "5000")
        assert result == "Email", (
            f"Expected 'Email' (field wins when value is unknown), got '{result}'"
        )

    def test_ambiguous_name_field_numeric_value(self):
        """
        Field name='reference' (Unknown), value='12345' (Unknown).
        Neither signal is decisive → Normal.
        """
        result = detect_field("reference", "12345")
        assert result == "Normal", (
            f"Expected 'Normal' for ambiguous reference/12345, got '{result}'"
        )
