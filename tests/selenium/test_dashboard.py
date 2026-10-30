"""
test_dashboard.py — Selenium tests for the frontend dashboard (index.html).

These tests open fronted/index.html directly as a file:// URL and verify
static UI elements that do not require a live backend.

Test cases:
  A1  Page title contains "Sensitive Data Validator"
  A2  Brand heading in the header is "Sensitive Data Validator"
  A3  System status text is displayed
  A4  Hero section heading is visible
  A5  Exactly 4 metric cards are present
  A6  Metric card values are non-empty
  A7  Validation form section is present on the page
  A8  All 8 form fields are visible
  A9  Submit button is visible
  A10 Footer is present
"""

import sys
import os
_SELENIUM_DIR = os.path.dirname(__file__)
if _SELENIUM_DIR not in sys.path:
    sys.path.insert(0, _SELENIUM_DIR)

import pytest
from constants import FRONTEND_URL
from pages.dashboard_page import DashboardPage


class TestDashboardLoading:
    """A — Dashboard Loading Tests"""

    def test_A1_page_title(self, driver):
        """A1: Page title must contain 'Sensitive Data Validator'."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert "Sensitive Data Validator" in page.get_title(), (
            f"Expected title to contain 'Sensitive Data Validator', got: '{page.get_title()}'"
        )

    def test_A2_brand_heading(self, driver):
        """A2: Brand heading in the topbar must read 'Sensitive Data Validator'."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        heading = page.get_brand_heading()
        assert "Sensitive Data Validator" in heading, (
            f"Expected brand heading to contain 'Sensitive Data Validator', got: '{heading}'"
        )

    def test_A3_system_status_visible(self, driver):
        """A3: System Active status must be displayed in the header."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        status = page.get_system_status()
        assert status != "", "System status text should not be empty"
        assert "System Active" in status or "Active" in status, (
            f"Expected system status to mention 'Active', got: '{status}'"
        )

    def test_A4_hero_heading_visible(self, driver):
        """A4: Hero section h2 heading is visible and non-empty."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        heading = page.get_hero_heading()
        assert heading != "", "Hero heading should not be empty"

    def test_A5_four_metric_cards(self, driver):
        """A5: Exactly 4 metric cards are displayed in the metrics section."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        cards = page.get_metric_cards()
        assert len(cards) == 4, (
            f"Expected 4 metric cards, found {len(cards)}"
        )

    def test_A6_metric_card_values_not_empty(self, driver):
        """A6: Each metric card contains visible text (e.g. '87.5%', '100%')."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        cards = page.get_metric_cards()
        for i, card in enumerate(cards):
            text = card.text.strip()
            assert text != "", f"Metric card {i + 1} should contain visible text, but it is empty"

    def test_A7_validator_section_present(self, driver):
        """A7: The 'Field Validation' section (id=validator) is present."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert page.is_validator_section_visible(), (
            "Validator section (section#validator) should be visible"
        )

    def test_A8_all_form_fields_visible(self, driver):
        """A8: All 8 form inputs are present and visible."""
        from pages.validation_page import ValidationPage
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        assert page.all_form_fields_visible(), (
            "All 8 form fields (organisation, partner, field_name, sample_value, "
            "expected_type, expected_masking, access_role, actual_value) must be visible"
        )

    def test_A9_submit_button_visible(self, driver):
        """A9: The 'Validate Field' submit button is visible."""
        from selenium.webdriver.common.by import By
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        btn = driver.find_element(By.CSS_SELECTOR, "button.validate-btn")
        assert btn.is_displayed(), "Submit button should be visible"

    def test_A10_footer_present(self, driver):
        """A10: Footer element is present on the page."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert page.is_footer_present(), "Footer should be present and visible"
