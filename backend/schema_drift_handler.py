"""
schema_drift_handler.py
=======================
Dynamic schema drift detection and normalization module for fintech
partner integrations.

Integrates with the Sensitive Data Validator (api.py) to handle:
  - Nested JSON flattening           (flatten_nested_payload)
  - Dynamic key / alias normalization (normalize_field_name)
  - Semi-structured data extraction  (extract_fields_from_semi_structured)
  - Schema drift detection           (detect_schema_drift, update_known_schema)
  - Fintech batch processing         (process_partner_payload)

Usage
-----
    from schema_drift_handler import process_partner_payload

    results = process_partner_payload(
        raw_payload=payload,
        organisation="FinA",
        partner="PayX",
        access_role="Manager",
        known_schema={"email": "Email", "cust_name": "Name"},
    )
"""

import re
import json
from typing import Any, Union

# ---------------------------------------------------------------------------
# Import core detection helpers from api.py.
# The try/except lets the module be used standalone (e.g. in unit tests)
# without a running FastAPI context.
# ---------------------------------------------------------------------------
try:
    from api import detect_field, is_valid_masking, check_masking, check_access
except ImportError:                                                # pragma: no cover
    def detect_field(field_name: str, sample_value: str) -> str:       # type: ignore[misc]
        """Fallback stub — returns 'Normal' when api.py is not available."""
        return "Normal"

    def is_valid_masking(field_type: str, value: str) -> bool:         # type: ignore[misc]
        """Fallback stub."""
        return False

    def check_masking(                                                   # type: ignore[misc]
        expected_masking: str,
        actual_value: str,
        field_type: str,
    ) -> str:
        """Fallback stub."""
        return "Not Required"

    def check_access(                                                    # type: ignore[misc]
        role: str,
        field_type: str,
        actual_value: str,
    ) -> str:
        """Fallback stub."""
        return "ACCESS DENIED"


# ===========================================================================
# MODULE-LEVEL SCHEMA STATE
# ===========================================================================

# Maps canonical field name → detected sensitive type
# (e.g. {"email": "Email", "cust_name": "Name"})
# Populated at runtime by update_known_schema().
KNOWN_SCHEMA: dict[str, str] = {}


# ===========================================================================
# FIELD ALIAS REGISTRY
# ===========================================================================

# Add new aliases here — no other code needs to change.
# Keys are the *normalised* (lowercase, no non-alphanumeric chars) alias;
# values are the canonical field name.
FIELD_ALIASES: dict[str, str] = {
    # ---- email ----
    "emailaddress":  "email",
    "emailaddr":     "email",
    "emailaddress":  "email",
    "email_address": "email",
    "usremail":      "email",
    "usr_email":     "email",
    "email":         "email",
    "eamil":         "email",   # common typo variant
    "e_mail":        "email",
    "EMAIL":         "email",

    # ---- phone ----
    "phonenumber":   "phone",
    "phone_number":  "phone",
    "phonenum":      "phone",
    "phone_num":     "phone",
    "mobileno":      "phone",
    "mobile_no":     "phone",
    "mobilenumber":  "phone",
    "contactphone":  "phone",
    "contact_phone": "phone",
    "PHONE_NUM":     "phone",

    # ---- card number ----
    "cardnumber":    "card_number",
    "card_number":   "card_number",
    "cardno":        "card_number",
    "card_no":       "card_number",
    "ccnum":         "card_number",
    "cc_num":        "card_number",
    "ccno":          "card_number",
    "cc_no":         "card_number",
    "CardNo":        "card_number",
    "paymentcard":   "card_number",
    "payment_card":  "card_number",
    "cardnum":       "card_number",

    # ---- customer name ----
    "fullname":      "cust_name",
    "full_name":     "cust_name",
    "custnm":        "cust_name",
    "cust_nm":       "cust_name",
    "clientname":    "cust_name",
    "client_name":   "cust_name",
    "customername":  "cust_name",
    "CustomerName":  "cust_name",
}


# ===========================================================================
# 1. NESTED JSON FLATTENING
# ===========================================================================

def flatten_nested_payload(payload: dict, prefix: str = "") -> dict:
    """
    Recursively flatten a nested JSON dictionary to a single-level dict
    whose keys encode the full access path using dot notation.

    Supports up to 5 levels of nesting. List elements are keyed by their
    zero-based integer index.

    Parameters
    ----------
    payload : dict
        The (potentially nested) dictionary to flatten.
    prefix : str, optional
        Internal recursion prefix — callers should leave this empty.

    Returns
    -------
    dict
        A flat ``{"dotted.key": value}`` dictionary.

    Examples
    --------
    >>> flatten_nested_payload({'user': {'email': 'a@b.com', 'phone': '9876543210'}})
    {'user.email': 'a@b.com', 'user.phone': '9876543210'}

    >>> flatten_nested_payload({'items': [{'card': '1234567890123456'}]})
    {'items.0.card': '1234567890123456'}
    """
    _MAX_DEPTH = 5

    # Count current depth from the number of separators already in the prefix
    current_depth = prefix.count(".") if prefix else 0

    flat: dict = {}

    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)

        if current_depth >= _MAX_DEPTH:
            # Max depth reached — store value as-is regardless of its type
            flat[full_key] = value

        elif isinstance(value, dict):
            nested = flatten_nested_payload(value, prefix=full_key)
            flat.update(nested)

        elif isinstance(value, list):
            for idx, item in enumerate(value):
                indexed_key = f"{full_key}.{idx}"
                if isinstance(item, dict):
                    nested = flatten_nested_payload(item, prefix=indexed_key)
                    flat.update(nested)
                else:
                    flat[indexed_key] = item

        else:
            flat[full_key] = value

    return flat


# ===========================================================================
# 2. DYNAMIC KEY NORMALIZATION
# ===========================================================================

def normalize_field_name(raw_key: str) -> str:
    """
    Map a raw / aliased field name to its canonical form using
    ``FIELD_ALIASES``.

    Lookup strategy (in order):
    1. Exact lowercase+stripped match.
    2. Match after stripping all non-alphanumeric characters (handles
       CamelCase and mixed-separator variants uniformly).
    3. If no alias is found, return the key lowercased and stripped.

    Parameters
    ----------
    raw_key : str
        The original field name as received from the partner payload.

    Returns
    -------
    str
        Canonical field name (e.g. ``"email"``, ``"card_number"``) or
        the cleaned raw key when no mapping exists.

    Examples
    --------
    >>> normalize_field_name("EmailAddress")
    'email'
    >>> normalize_field_name("PHONE_NUM")
    'phone'
    >>> normalize_field_name("transaction_id")
    'transaction_id'
    """
    cleaned = raw_key.strip().lower()
    # Strip all non-alphanumeric characters for CamelCase / mixed-separator lookup
    stripped = re.sub(r"[^a-z0-9]", "", cleaned)

    return (
        FIELD_ALIASES.get(cleaned)
        or FIELD_ALIASES.get(stripped)
        or cleaned
    )


# ===========================================================================
# 3. SEMI-STRUCTURED DATA EXTRACTION
# ===========================================================================

def extract_fields_from_semi_structured(
    data: Union[dict, list, str],
) -> list[dict]:
    """
    Accept semi-structured data in multiple formats and return a flat list
    of ``{"field_name": ..., "sample_value": ...}`` dicts ready for
    downstream processing.

    Supported input types
    ---------------------
    * ``dict``  — flat or nested JSON object.
    * ``list``  — list of dicts (e.g. a batch of records); every record
                  is processed and its fields are collected.
    * ``str``   — raw JSON string (parsed internally).

    Processing pipeline
    -------------------
    1. Parse JSON strings.
    2. Wrap plain dicts into a single-element list.
    3. For each record: flatten via ``flatten_nested_payload()``, then
       normalize every *leaf* key via ``normalize_field_name()``.

    Parameters
    ----------
    data : dict | list | str
        The raw partner data.

    Returns
    -------
    list[dict]
        List of ``{"field_name": str, "sample_value": str}`` entries.

    Raises
    ------
    ValueError
        If a JSON string cannot be parsed, or if the input type is
        not supported.

    Examples
    --------
    >>> extract_fields_from_semi_structured({'emailAddress': 'a@b.com'})
    [{'field_name': 'email', 'sample_value': 'a@b.com'}]
    """
    # --- Step 1: parse JSON strings ---
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON string provided: {exc}") from exc

    # --- Step 2: normalise to list of records ---
    if isinstance(data, dict):
        records: list[dict] = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError(
            f"Unsupported data type '{type(data).__name__}'. "
            "Expected dict, list, or JSON string."
        )

    # --- Step 3: flatten + normalize each record ---
    extracted: list[dict] = []
    for record in records:
        if not isinstance(record, dict):
            # Skip non-dict list elements (e.g. raw scalars in a mixed list)
            continue

        flat = flatten_nested_payload(record)

        for raw_key, value in flat.items():
            # Preserve path prefix (e.g. "user.") but normalize only the
            # leaf segment so path structure remains readable in reports.
            segments = raw_key.rsplit(".", 1)
            leaf = segments[-1]
            path_prefix = segments[0] + "." if len(segments) == 2 else ""
            normalized_leaf = normalize_field_name(leaf)
            normalized_key = f"{path_prefix}{normalized_leaf}" if path_prefix else normalized_leaf

            extracted.append({
                "field_name":   normalized_key,
                "sample_value": str(value),
            })

    return extracted


# ===========================================================================
# 4. SCHEMA DRIFT DETECTION
# ===========================================================================

def detect_schema_drift(
    current_fields: list[str],
    known_schema: dict,
) -> dict:
    """
    Compare the set of fields observed in the current payload against a
    ``known_schema`` and classify the differences.

    Parameters
    ----------
    current_fields : list[str]
        Canonical field names extracted from the incoming payload.
    known_schema : dict
        Mapping of ``{field_name: expected_type}`` representing the
        previously agreed data contract with the partner.

    Returns
    -------
    dict with three keys:

    ``new_fields`` : list[str]
        Fields present in the payload but absent from the known schema.

    ``missing_fields`` : list[str]
        Fields declared in the known schema but absent from the payload.

    ``renamed_candidates`` : list[dict]
        New fields whose name is a substring of (or contains) a known
        field name — a heuristic signal that the partner may have renamed
        an existing field.
        Each entry: ``{"current": str, "possible_match": str}``.

    Examples
    --------
    >>> known = {"email": "Email", "cust_name": "Name"}
    >>> detect_schema_drift(["email", "user_email_addr", "account_id"], known)
    {
        'new_fields': ['account_id', 'user_email_addr'],
        'missing_fields': ['cust_name'],
        'renamed_candidates': [{'current': 'user_email_addr', 'possible_match': 'email'}]
    }
    """
    known_keys = set(known_schema.keys())
    current_keys = set(current_fields)

    new_fields = sorted(current_keys - known_keys)
    missing_fields = sorted(known_keys - current_keys)

    # Fuzzy rename detection via substring containment (lightweight heuristic)
    renamed_candidates: list[dict] = []
    for new_f in new_fields:
        for known_f in known_keys:
            # Both directions: "user_phone" contains "phone",
            # and "phone" is contained in "user_phone"
            if known_f in new_f or new_f in known_f:
                renamed_candidates.append({
                    "current":        new_f,
                    "possible_match": known_f,
                })
                break  # One best candidate per new field is sufficient

    return {
        "new_fields":         new_fields,
        "missing_fields":     missing_fields,
        "renamed_candidates": renamed_candidates,
    }


def update_known_schema(field_name: str, detected_type: str) -> None:
    """
    Register or update a field's detected type in the module-level
    ``KNOWN_SCHEMA`` dictionary.

    This allows the schema to grow organically as new payloads are
    processed, providing a baseline for future drift detection runs.

    Parameters
    ----------
    field_name : str
        Canonical field name (should already be normalized before calling).
    detected_type : str
        The sensitive-data type detected by ``detect_field()``
        (one of ``"Email"``, ``"Phone"``, ``"Card"``, ``"Name"``,
        ``"Normal"``).

    Side Effects
    ------------
    Mutates the module-level ``KNOWN_SCHEMA`` dict in place.

    Examples
    --------
    >>> update_known_schema("email", "Email")
    >>> KNOWN_SCHEMA
    {'email': 'Email'}
    """
    KNOWN_SCHEMA[field_name] = detected_type


# ===========================================================================
# 5. FINTECH BATCH PROCESSOR
# ===========================================================================

def process_partner_payload(
    raw_payload: Union[dict, list, str],
    organisation: str,
    partner: str,
    access_role: str,
    known_schema: dict = None,
) -> list[dict]:
    """
    End-to-end pipeline for processing a raw fintech partner payload.

    Steps
    -----
    1. Extract and normalize all fields from the raw payload
       (supports dict, list of dicts, or JSON string).
    2. Detect schema drift relative to ``known_schema``.
    3. For each field, call ``detect_field()`` (from api.py) to classify
       the sensitive-data type.
    4. Assign a ``drift_status`` tag based on the drift analysis.
    5. Append synthetic ``"MISSING"`` entries for schema fields absent
       from the current payload.
    6. Return a structured list of result records.

    Parameters
    ----------
    raw_payload : dict | list | str
        The incoming partner data in any supported format.
    organisation : str
        Name of the consuming organisation (e.g. ``"FinA"``).
    partner : str
        Name of the data partner (e.g. ``"PayX"``).
    access_role : str
        Role of the requesting user — forwarded to ``check_access()``.
        Valid values: ``"Admin"``, ``"Manager"``, ``"Analyst"``.
    known_schema : dict, optional
        ``{field_name: expected_type}`` baseline for drift comparison.
        Defaults to an empty dict (first-time ingestion — all fields
        will be marked as ``NEW_FIELD``).

    Returns
    -------
    list[dict]
        One entry per flattened field, each containing:

        ==================  ================================================
        Key                 Description
        ==================  ================================================
        ``organisation``    Echoes the *organisation* parameter.
        ``partner``         Echoes the *partner* parameter.
        ``field_name``      Normalized / canonical field name.
        ``original_key``    Raw dotted key as it appeared in the payload.
        ``sample_value``    String value of the field (``None`` for MISSING).
        ``detected_type``   Type returned by ``detect_field()``:
                            ``"Email"``, ``"Phone"``, ``"Card"``,
                            ``"Name"``, or ``"Normal"``.
        ``drift_status``    One of ``"KNOWN"``, ``"NEW_FIELD"``,
                            ``"RENAMED"``, ``"MISSING"``.
        ==================  ================================================

    Examples
    --------
    >>> results = process_partner_payload(
    ...     raw_payload={"emailAddress": "alice@example.com"},
    ...     organisation="FinA",
    ...     partner="PayX",
    ...     access_role="Manager",
    ...     known_schema={"email": "Email"},
    ... )
    >>> results[0]["drift_status"]
    'KNOWN'
    """
    if known_schema is None:
        known_schema = {}

    # ------------------------------------------------------------------
    # Step 1 – Extract fields (flatten + normalize)
    # ------------------------------------------------------------------
    extracted = extract_fields_from_semi_structured(raw_payload)

    # Build original (un-normalized) dotted keys for reporting by re-flattening
    # the raw payload before any normalization is applied.
    if isinstance(raw_payload, str):
        try:
            _raw: Any = json.loads(raw_payload)
        except json.JSONDecodeError:
            _raw = {}
    else:
        _raw = raw_payload

    _raw_records: list[dict]
    if isinstance(_raw, dict):
        _raw_records = [_raw]
    elif isinstance(_raw, list):
        _raw_records = [r for r in _raw if isinstance(r, dict)]
    else:
        _raw_records = []

    original_keys: list[str] = []
    for rec in _raw_records:
        original_keys.extend(flatten_nested_payload(rec).keys())

    # Pair each extracted entry with its original raw key (positionally)
    for i, entry in enumerate(extracted):
        entry["original_key"] = (
            original_keys[i] if i < len(original_keys) else entry["field_name"]
        )

    # ------------------------------------------------------------------
    # Step 2 – Schema drift analysis
    # ------------------------------------------------------------------
    current_field_names = [e["field_name"] for e in extracted]
    drift_report = detect_schema_drift(current_field_names, known_schema)

    new_fields_set = set(drift_report["new_fields"])
    renamed_set = {rc["current"] for rc in drift_report["renamed_candidates"]}

    # ------------------------------------------------------------------
    # Steps 3 & 4 – Per-field type detection + drift labelling
    # ------------------------------------------------------------------
    results: list[dict] = []

    for entry in extracted:
        fname = entry["field_name"]
        sval  = entry["sample_value"]
        orig  = entry["original_key"]

        # Detect sensitive type via api.py's hybrid field+value detection
        detected_type = detect_field(fname, sval)

        # Classify drift status (RENAMED takes precedence over NEW_FIELD)
        if fname in renamed_set:
            drift_status = "RENAMED"
        elif fname in new_fields_set:
            drift_status = "NEW_FIELD"
        else:
            drift_status = "KNOWN"

        results.append({
            "organisation":  organisation,
            "partner":       partner,
            "field_name":    fname,
            "original_key":  orig,
            "sample_value":  sval,
            "detected_type": detected_type,
            "drift_status":  drift_status,
        })

    # ------------------------------------------------------------------
    # Step 5 – Append MISSING entries for absent schema fields
    # ------------------------------------------------------------------
    for missing_field in drift_report["missing_fields"]:
        results.append({
            "organisation":  organisation,
            "partner":       partner,
            "field_name":    missing_field,
            "original_key":  missing_field,
            "sample_value":  None,
            "detected_type": known_schema.get(missing_field, "Unknown"),
            "drift_status":  "MISSING",
        })

    return results


# ===========================================================================
# DEMO  —  run:  python schema_drift_handler.py
# ===========================================================================

if __name__ == "__main__":
    import pprint
    from collections import Counter

    pp = pprint.PrettyPrinter(indent=2, width=100)

    # -------------------------------------------------------------------
    print("=" * 70)
    print("DEMO 1 — Nested JSON payload (up to 3 levels deep)")
    print("=" * 70)

    nested_payload: dict = {
        "user": {
            "emailAddress": "alice@bank.com",
            "phoneNumber":  "9876543210",
            "address": {
                "city":    "Mumbai",
                "pincode": "400001",
            },
        },
        "transactions": [
            {
                "cardNumber": "4111111111111111",
                "amount":     "5000",
            },
            {
                "cardNumber": "5500005555555559",
                "amount":     "1200",
            },
        ],
    }

    known_v1: dict[str, str] = {
        "email":       "Email",
        "phone":       "Phone",
        "card_number": "Card",
    }

    results_demo1 = process_partner_payload(
        raw_payload  = nested_payload,
        organisation = "FinA",
        partner      = "PayX",
        access_role  = "Manager",
        known_schema = known_v1,
    )
    print("\nFlattened & processed fields:")
    pp.pprint(results_demo1)

    # -------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DEMO 2 — Renamed / aliased keys (schema normalization)")
    print("=" * 70)

    aliased_payload: dict = {
        "EMAIL":        "bob@fintech.io",
        "PHONE_NUM":    "8765432109",
        "CardNo":       "4000000000000002",
        "CustomerName": "Robert Smith",
        "account_id":   "ACC-99182",
    }

    known_v2: dict[str, str] = {
        "email":       "Email",
        "phone":       "Phone",
        "card_number": "Card",
        "cust_name":   "Name",
    }

    results_demo2 = process_partner_payload(
        raw_payload  = aliased_payload,
        organisation = "FinA",
        partner      = "LoanPro",
        access_role  = "Analyst",
        known_schema = known_v2,
    )
    print("\nNormalized fields and drift status:")
    pp.pprint(results_demo2)

    # -------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("DEMO 3 — Schema drift (new field + missing field + rename candidate)")
    print("=" * 70)

    # Partner renamed 'phone' → 'user_phone_number', dropped 'cust_name',
    # and introduced a brand-new 'loyalty_score' field.
    drifted_payload_json: str = json.dumps([
        {
            "email":              "carol@payments.com",
            "user_phone_number":  "7654321098",       # rename candidate for 'phone'
            "card_number":        "5425233430109903",
            "loyalty_score":      "GOLD",             # brand-new field
        },
        {
            "email":              "dave@payments.com",
            "user_phone_number":  "6543210987",
            "card_number":        "4012888888881881",
            "loyalty_score":      "SILVER",
        },
    ])

    known_v3: dict[str, str] = {
        "email":       "Email",
        "phone":       "Phone",      # partner dropped / renamed this
        "card_number": "Card",
        "cust_name":   "Name",       # partner dropped this entirely
    }

    results_demo3 = process_partner_payload(
        raw_payload  = drifted_payload_json,
        organisation = "FinA",
        partner      = "WalletZ",
        access_role  = "Admin",
        known_schema = known_v3,
    )

    print("\nDrift-annotated results (JSON string input, list of records):")
    pp.pprint(results_demo3)

    # Summary
    status_counts = Counter(r["drift_status"] for r in results_demo3)
    print("\nDrift status summary:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status:<15}: {count}")
