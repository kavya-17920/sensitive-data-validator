"""
test_schema_drift.py
--------------------
Unit tests for all public functions in schema_drift_handler.py:

  - flatten_nested_payload()
  - normalize_field_name()
  - extract_fields_from_semi_structured()
  - detect_schema_drift()
"""

import sys
import os
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from schema_drift_handler import (  # noqa: E402
    flatten_nested_payload,
    normalize_field_name,
    extract_fields_from_semi_structured,
    detect_schema_drift,
)


# ============================================================
# TEST CLASS: flatten_nested_payload()
# ============================================================

class TestFlattenNestedPayload:
    """Tests for flatten_nested_payload()."""

    def test_flat_dict_unchanged(self):
        """A dict with no nesting is returned as-is."""
        payload = {"email": "k***@gmail.com", "amount": "500"}
        result = flatten_nested_payload(payload)
        assert result == {"email": "k***@gmail.com", "amount": "500"}

    def test_single_level_nesting(self):
        """One level of nesting is flattened with dotted key."""
        payload = {"customer": {"email": "k***@gmail.com"}}
        result = flatten_nested_payload(payload)
        assert result == {"customer.email": "k***@gmail.com"}

    def test_two_level_nesting(self):
        """Two levels of nesting produce double-dotted keys."""
        payload = {"a": {"b": {"c": "value"}}}
        result = flatten_nested_payload(payload)
        assert result == {"a.b.c": "value"}

    def test_mixed_flat_and_nested(self):
        """Mix of flat and nested keys in the same dict."""
        payload = {
            "name": "Kavya",
            "contact": {"phone": "******3210", "email": "k***@gmail.com"},
        }
        result = flatten_nested_payload(payload)
        assert result == {
            "name": "Kavya",
            "contact.phone": "******3210",
            "contact.email": "k***@gmail.com",
        }

    def test_list_handling(self):
        """
        List values are preserved under their parent key (not recursed into).
        """
        payload = {"tags": ["pii", "sensitive"], "amount": "500"}
        result = flatten_nested_payload(payload)
        assert result["tags"] == ["pii", "sensitive"]
        assert result["amount"] == "500"

    def test_empty_dict(self):
        """Empty dict returns an empty dict."""
        assert flatten_nested_payload({}) == {}


# ============================================================
# TEST CLASS: normalize_field_name()
# ============================================================

class TestNormalizeFieldName:
    """Tests for normalize_field_name()."""

    # ---- Email aliases ----

    def test_email_aliases(self):
        """Common email aliases all map to 'email'."""
        for alias in ["emailAddress", "EMAIL", "usr_email", "cust_mail", "mail"]:
            result = normalize_field_name(alias)
            assert result == "email", (
                f"Expected 'email' for alias='{alias}', got '{result}'"
            )

    # ---- Phone aliases ----

    def test_phone_aliases(self):
        """Common phone aliases all map to 'phone'."""
        for alias in ["phoneNumber", "PHONE_NUM", "mobile_no", "contact_phone_num"]:
            result = normalize_field_name(alias)
            assert result == "phone", (
                f"Expected 'phone' for alias='{alias}', got '{result}'"
            )

    # ---- Card aliases ----

    def test_card_aliases(self):
        """Common card aliases all map to 'card_number'."""
        for alias in ["cardNumber", "cc_no", "payment_card", "cc"]:
            result = normalize_field_name(alias)
            assert result == "card_number", (
                f"Expected 'card_number' for alias='{alias}', got '{result}'"
            )

    # ---- Unknown / passthrough ----

    def test_unknown_key_lowercased(self):
        """
        An unknown field name is returned lowercased with no other
        transformation.
        """
        result = normalize_field_name("TransactionID")
        assert result == "transactionid"

    def test_known_exact_match(self):
        """Exact canonical key 'email' passes through."""
        assert normalize_field_name("email") == "email"

    def test_name_aliases(self):
        """Common name aliases all map to 'name'."""
        for alias in ["fullname", "customer_name", "cust_nm", "fname", "lname"]:
            result = normalize_field_name(alias)
            assert result == "name", (
                f"Expected 'name' for alias='{alias}', got '{result}'"
            )


# ============================================================
# TEST CLASS: extract_fields_from_semi_structured()
# ============================================================

class TestExtractFields:
    """Tests for extract_fields_from_semi_structured()."""

    def test_from_flat_dict(self):
        """A flat dict is extracted as-is."""
        data = {"email": "k***@gmail.com", "role": "Analyst"}
        result = extract_fields_from_semi_structured(data)
        assert result == {"email": "k***@gmail.com", "role": "Analyst"}

    def test_from_nested_dict(self):
        """A nested dict is flattened during extraction."""
        data = {"user": {"email": "k***@gmail.com"}, "amount": "500"}
        result = extract_fields_from_semi_structured(data)
        assert "user.email" in result
        assert result["amount"] == "500"

    def test_from_json_string(self):
        """A valid JSON string is parsed and extracted like a dict."""
        data = json.dumps({"phone": "******3210", "status": "active"})
        result = extract_fields_from_semi_structured(data)
        assert result == {"phone": "******3210", "status": "active"}

    def test_from_list_of_dicts(self):
        """The first element of a list-of-dicts is used."""
        data = [{"card_number": "************5678", "amount": "1000"}]
        result = extract_fields_from_semi_structured(data)
        assert "card_number" in result

    def test_invalid_json_string_raises(self):
        """An invalid JSON string raises a ValueError."""
        with pytest.raises(ValueError, match="Cannot parse string as JSON"):
            extract_fields_from_semi_structured("{not valid json}")

    def test_unsupported_type_raises(self):
        """An unsupported type (e.g. int) raises a ValueError."""
        with pytest.raises(ValueError, match="Unsupported data type"):
            extract_fields_from_semi_structured(12345)

    def test_empty_list_returns_empty(self):
        """An empty list returns an empty dict."""
        result = extract_fields_from_semi_structured([])
        assert result == {}


# ============================================================
# TEST CLASS: detect_schema_drift()
# ============================================================

class TestSchemaDrift:
    """Tests for detect_schema_drift()."""

    def test_no_drift_when_schema_matches(self):
        """Identical field sets → no drift."""
        baseline = {"email", "phone", "amount"}
        incoming = {"email", "phone", "amount"}
        report = detect_schema_drift(incoming, baseline)
        assert report["has_drift"] is False
        assert len(report["new_fields"]) == 0
        assert len(report["missing_fields"]) == 0

    def test_detects_new_fields(self):
        """
        Incoming has extra fields not in baseline → new_fields is populated
        and has_drift is True.
        """
        baseline = {"email", "phone"}
        incoming = {"email", "phone", "card_number"}
        report = detect_schema_drift(incoming, baseline)
        assert report["has_drift"] is True
        assert "card_number" in report["new_fields"]

    def test_detects_missing_fields(self):
        """
        Incoming is missing fields that are in baseline → missing_fields is
        populated and has_drift is True.
        """
        baseline = {"email", "phone", "card_number"}
        incoming = {"email", "phone"}
        report = detect_schema_drift(incoming, baseline)
        assert report["has_drift"] is True
        assert "card_number" in report["missing_fields"]

    def test_detects_renamed_candidates(self):
        """
        A field name that differs by ≤ 2 characters from a baseline field
        is flagged as a renamed candidate.
        """
        # 'phon' is edit-distance 1 from 'phone'
        baseline = {"email", "phone"}
        incoming = {"email", "phon"}  # likely a typo / rename of 'phone'
        report = detect_schema_drift(incoming, baseline)
        assert report["has_drift"] is True
        # At least one renamed candidate pairing should be detected
        renamed_pairs = [
            (r["incoming"], r["baseline"]) for r in report["renamed_candidates"]
        ]
        assert ("phon", "phone") in renamed_pairs

    def test_empty_baseline(self):
        """Any incoming field against an empty baseline → all are new."""
        incoming = {"email", "phone"}
        report = detect_schema_drift(incoming, set())
        assert report["has_drift"] is True
        assert incoming == report["new_fields"]

    def test_empty_incoming(self):
        """No incoming fields against a populated baseline → all are missing."""
        baseline = {"email", "phone"}
        report = detect_schema_drift(set(), baseline)
        assert report["has_drift"] is True
        assert baseline == report["missing_fields"]
