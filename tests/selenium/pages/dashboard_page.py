"""
dashboard_page.py — Page Object for the Sensitive Data Validator frontend.

Maps exactly to the HTML structure in fronted/index.html:

  - <header class="topbar">  →  header / brand / status
  - <section class="hero">   →  hero heading, "Start Validation" button
  - <div class="cards">      →  four .metric-card elements
  - <section id="validator"> →  validation form
  - <section id="result">    →  result area
  - <footer>                 →  footer text

Element locators are derived from the actual IDs and classes in index.html
so they will never break as long as the HTML structure is unchanged.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class DashboardPage:
    """
    Page Object representing the main frontend page (fronted/index.html).

    Usage::

        page = DashboardPage(driver)
        page.open(FRONTEND_URL)
        assert page.is_loaded()
    """

    # --- Locators (matched to actual index.html) ---
    TITLE_CONTAINS = "Sensitive Data Validator"

    # Header
    LOC_HEADER = (By.CSS_SELECTOR, "header.topbar")
    LOC_BRAND_HEADING = (By.CSS_SELECTOR, "header.topbar h1")
    LOC_SYSTEM_STATUS = (By.CSS_SELECTOR, ".system-status")

    # Hero section
    LOC_HERO = (By.CSS_SELECTOR, "section.hero")
    LOC_HERO_H2 = (By.CSS_SELECTOR, "section.hero h2")
    LOC_START_BTN = (By.CSS_SELECTOR, "button.primary-btn")

    # Metric cards  (div.cards > div.metric-card)
    LOC_METRIC_CARDS = (By.CSS_SELECTOR, "div.cards div.metric-card")

    # Validator section
    LOC_VALIDATOR_SECTION = (By.CSS_SELECTOR, "section#validator")
    LOC_FORM = (By.CSS_SELECTOR, "form#validationForm")

    # Form fields (IDs from index.html)
    LOC_ORGANISATION = (By.ID, "organisation")
    LOC_PARTNER = (By.ID, "partner")
    LOC_FIELD_NAME = (By.ID, "field_name")
    LOC_SAMPLE_VALUE = (By.ID, "sample_value")
    LOC_EXPECTED_TYPE = (By.ID, "expected_type")
    LOC_EXPECTED_MASKING = (By.ID, "expected_masking")
    LOC_ACCESS_ROLE = (By.ID, "access_role")
    LOC_ACTUAL_VALUE = (By.ID, "actual_value")
    LOC_SUBMIT_BTN = (By.CSS_SELECTOR, "button.validate-btn")

    # Result area
    LOC_RESULT_SECTION = (By.CSS_SELECTOR, "section#result")
    LOC_RESULT_CONTENT = (By.ID, "resultContent")

    # Footer
    LOC_FOOTER = (By.CSS_SELECTOR, "footer")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open(self, url: str) -> "DashboardPage":
        """Navigate to the frontend URL."""
        self.driver.get(url)
        return self

    # ------------------------------------------------------------------
    # State checks
    # ------------------------------------------------------------------

    def is_loaded(self) -> bool:
        """Return True when the page title and header are present."""
        return (
            self.TITLE_CONTAINS in self.driver.title
            and self.get_brand_heading() != ""
        )

    def get_title(self) -> str:
        return self.driver.title

    def get_brand_heading(self) -> str:
        try:
            el = self.wait.until(EC.presence_of_element_located(self.LOC_BRAND_HEADING))
            return el.text
        except Exception:
            return ""

    def get_system_status(self) -> str:
        try:
            return self.driver.find_element(*self.LOC_SYSTEM_STATUS).text
        except Exception:
            return ""

    def get_hero_heading(self) -> str:
        try:
            return self.driver.find_element(*self.LOC_HERO_H2).text
        except Exception:
            return ""

    def get_metric_cards(self):
        """Return all metric card WebElements."""
        return self.driver.find_elements(*self.LOC_METRIC_CARDS)

    def is_form_visible(self) -> bool:
        try:
            return self.driver.find_element(*self.LOC_FORM).is_displayed()
        except Exception:
            return False

    def is_validator_section_visible(self) -> bool:
        try:
            return self.driver.find_element(*self.LOC_VALIDATOR_SECTION).is_displayed()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Interactions
    # ------------------------------------------------------------------

    def click_start_validation(self) -> None:
        """Click the 'Start Validation' hero button (scrolls to form)."""
        btn = self.wait.until(EC.element_to_be_clickable(self.LOC_START_BTN))
        btn.click()

    def is_footer_present(self) -> bool:
        try:
            return self.driver.find_element(*self.LOC_FOOTER).is_displayed()
        except Exception:
            return False
