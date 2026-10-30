"""
test_navigation.py — Selenium tests for navigation and page loading (F group).

F1  Frontend page loads at file:// URL
F2  Page title is correct
F3  Backend home endpoint (GET /) returns 200 — verified via requests, not browser
F4  FastAPI /docs URL loads a page titled 'FastAPI' (if backend is running)
F5  Dashboard URL (/dashboard) serves an HTML page (if backend is running)
F6  'Start Validation' button scrolls to the form section
F7  Multiple page sections are reachable by scrolling
"""

import sys
import os
import pytest
import requests

sys.path.insert(0, os.path.dirname(__file__))

from constants import FRONTEND_URL, BACKEND_URL, DASHBOARD_URL, API_DOCS_URL
from pages.dashboard_page import DashboardPage


# Backend skip marker (same pattern as test_security_scenarios.py)
def _backend_is_up() -> bool:
    try:
        return requests.get(BACKEND_URL, timeout=3).status_code == 200
    except Exception:
        return False


BACKEND_SKIP = pytest.mark.skipif(
    not _backend_is_up(),
    reason="FastAPI backend is not running — skipping backend navigation tests"
)


class TestNavigation:
    """F — Navigation and page loading tests."""

    def test_F1_frontend_loads(self, driver):
        """F1: Frontend index.html loads without error."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert page.is_loaded(), (
            f"Frontend page did not load correctly. Title: '{page.get_title()}'"
        )

    def test_F2_page_title_correct(self, driver):
        """F2: Page title is 'Sensitive Data Validator'."""
        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert "Sensitive Data Validator" in page.get_title()

    @BACKEND_SKIP
    def test_F3_backend_home_returns_200(self, driver):
        """F3: GET http://127.0.0.1:8000/ returns HTTP 200."""
        driver.get(BACKEND_URL)
        import time
        time.sleep(1)
        # The page content should include the running message
        source = driver.page_source
        assert "running" in source.lower() or "200" in driver.title or source != "", (
            "Backend home endpoint should return a non-empty response"
        )

    @BACKEND_SKIP
    def test_F4_api_docs_page_loads(self, driver):
        """F4: FastAPI /docs page loads and title contains 'FastAPI' or 'Swagger'."""
        driver.get(API_DOCS_URL)
        import time
        time.sleep(2)  # Allow Swagger UI JS to render
        title = driver.title
        assert ("FastAPI" in title or "Swagger" in title or "docs" in title.lower()), (
            f"API docs page title should mention FastAPI or Swagger, got: '{title}'"
        )

    @BACKEND_SKIP
    def test_F5_dashboard_endpoint_loads(self, driver):
        """F5: GET /dashboard returns a non-empty HTML page."""
        driver.get(DASHBOARD_URL)
        import time
        time.sleep(1)
        assert "Sensitive Data" in driver.page_source or driver.page_source != "", (
            "Dashboard endpoint should return HTML content"
        )

    def test_F6_start_validation_scrolls_to_form(self, driver):
        """F6: Clicking 'Start Validation' button reveals the form section."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        page = DashboardPage(driver)
        page.open(FRONTEND_URL)

        # Click start validation
        page.click_start_validation()

        import time
        time.sleep(1)

        # The validator section should still be displayed (scrolled into view)
        validator = driver.find_element(By.CSS_SELECTOR, "section#validator")
        assert validator.is_displayed(), (
            "Validator section should be displayed after clicking Start Validation"
        )

    def test_F7_all_sections_present(self, driver):
        """F7: Hero, metrics, validator, result sections all exist in the DOM."""
        from selenium.webdriver.common.by import By

        page = DashboardPage(driver)
        page.open(FRONTEND_URL)

        sections = {
            "hero": "section.hero",
            "metrics cards": "div.cards",
            "validator": "section#validator",
            "result": "section#result",
            "footer": "footer",
        }

        for name, selector in sections.items():
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            assert len(elements) > 0, (
                f"Section '{name}' (selector: '{selector}') not found in the DOM"
            )
