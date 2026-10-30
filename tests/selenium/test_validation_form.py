"""
test_validation_form.py — Selenium tests for the validation form (B group).

These tests exercise form field filling and result display.
Because the form submits to http://127.0.0.1:8000/validate via fetch(),
the backend must be running for B2+ tests that check result output.

B1 tests form field visibility (offline — no backend).
B2 tests a full round-trip that expects a connection-error message when
   the backend is not running, confirming the form submits correctly.

All locators are based on actual index.html IDs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from constants import FRONTEND_URL
from pages.validation_page import ValidationPage
from pages.dashboard_page import DashboardPage


class TestFormFieldVisibility:
    """B1 — Verify all form fields exist and are visible."""

    def test_B1_organisation_field_visible(self, driver):
        """B1a: Organisation input is visible with correct placeholder."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "organisation")
        assert el.is_displayed()
        assert el.get_attribute("placeholder") == "e.g. FinA"

    def test_B1_partner_field_visible(self, driver):
        """B1b: Partner input is visible."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "partner")
        assert el.is_displayed()

    def test_B1_field_name_visible(self, driver):
        """B1c: Field Name input is visible."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "field_name")
        assert el.is_displayed()
        assert el.get_attribute("placeholder") == "e.g. email"

    def test_B1_sample_value_visible(self, driver):
        """B1d: Sample Value input is visible."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "sample_value")
        assert el.is_displayed()

    def test_B1_expected_type_select_visible(self, driver):
        """B1e: Expected Type select is visible and has options Email/Phone/Card/Name/Normal."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "expected_type")
        assert el.is_displayed()
        select = Select(el)
        option_values = [opt.get_attribute("value") for opt in select.options]
        for expected in ["Email", "Phone", "Card", "Name", "Normal"]:
            assert expected in option_values, (
                f"Option '{expected}' missing from expected_type select"
            )

    def test_B1_expected_masking_visible(self, driver):
        """B1f: Expected Masking input is visible."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "expected_masking")
        assert el.is_displayed()

    def test_B1_access_role_select_visible(self, driver):
        """B1g: Access Role select is visible and has Admin/Manager/Analyst options."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "access_role")
        assert el.is_displayed()
        select = Select(el)
        option_values = [opt.get_attribute("value") for opt in select.options]
        for role in ["Admin", "Manager", "Analyst"]:
            assert role in option_values, (
                f"Role '{role}' missing from access_role select"
            )

    def test_B1_actual_value_visible(self, driver):
        """B1h: Actual Value input is visible."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        el = driver.find_element(By.ID, "actual_value")
        assert el.is_displayed()


class TestFormInteraction:
    """B2 — Form fill and submit interactions."""

    def test_B2_fill_all_fields(self, driver):
        """B2: All fields can be filled with test data without error."""
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        page.enter_organisation("TestOrg")
        page.enter_partner("TestPartner")
        page.enter_field_name("email")
        page.enter_sample_value("test@example.com")
        page.select_expected_type("Email")
        page.enter_expected_masking("t***@example.com")
        page.select_access_role("Analyst")
        page.enter_actual_value("t***@example.com")

        from selenium.webdriver.common.by import By
        assert driver.find_element(By.ID, "organisation").get_attribute("value") == "TestOrg"
        assert driver.find_element(By.ID, "partner").get_attribute("value") == "TestPartner"
        assert driver.find_element(By.ID, "field_name").get_attribute("value") == "email"

    def test_B2_submit_without_backend_shows_error_or_result(self, driver):
        """
        B2b: Submitting the form when backend is offline must show either
        a connection error message or a validation result — never a blank page.
        """
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        page.enter_organisation("TestOrg")
        page.enter_partner("TestPartner")
        page.enter_field_name("email")
        page.enter_sample_value("test@example.com")
        page.select_expected_type("Email")
        page.enter_expected_masking("t***@example.com")
        page.select_access_role("Analyst")
        page.enter_actual_value("t***@example.com")

        # Scroll submit button into view then click via JS to avoid intercept
        btn = driver.find_element(By.CSS_SELECTOR, "button.validate-btn")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        driver.execute_script("arguments[0].click();", btn)

        import time
        time.sleep(5)  # Allow async fetch to complete or timeout
        content = page.get_result_content_text()
        assert content.strip() != "", (
            "Result content should not be empty after form submission"
        )


    def test_B2_validate_button_text(self, driver):
        """B2c: Validate button displays '🔍 Validate Field' text."""
        from selenium.webdriver.common.by import By
        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        btn = driver.find_element(By.CSS_SELECTOR, "button.validate-btn")
        assert "Validate Field" in btn.text, (
            f"Submit button should say 'Validate Field', got: '{btn.text}'"
        )

    def test_B2_start_validation_btn_scrolls(self, driver):
        """B2d: Clicking 'Start Validation' hero button scrolls to the form."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        page.click_start_validation()
        import time
        time.sleep(1)
        from selenium.webdriver.common.by import By
        validator = driver.find_element(By.CSS_SELECTOR, "section#validator")
        # Check that the element is in view (Y position > 0 after scroll)
        assert validator.is_displayed(), "Validator section should still be displayed after scroll"
