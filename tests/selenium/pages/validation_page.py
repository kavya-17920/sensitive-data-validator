"""
validation_page.py — Page Object for the Validation Form on the frontend.

Wraps the <form id="validationForm"> and <section id="result"> in index.html.
All locators come directly from the actual HTML IDs and CSS classes.

Form fields (IDs from index.html):
  organisation, partner, field_name, sample_value,
  expected_type (select), expected_masking, access_role (select), actual_value

Result area:
  #resultContent  — injected HTML by script.js after API response
  .validation-status  — present after submission
  .final-decision     — contains the ALLOW / BLOCK text
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class ValidationPage:
    """
    Page Object for the validation form and result display.

    Usage::

        page = ValidationPage(driver)
        page.open(FRONTEND_URL)
        page.fill_and_submit(
            organisation="TestOrg", partner="PayX",
            field_name="email", sample_value="k@x.com",
            expected_type="Email", expected_masking="k***@x.com",
            access_role="Analyst", actual_value="k***@x.com"
        )
        assert page.get_publication_decision() == "ALLOW"
    """

    # Form field locators — all IDs from index.html
    LOC_ORGANISATION = (By.ID, "organisation")
    LOC_PARTNER = (By.ID, "partner")
    LOC_FIELD_NAME = (By.ID, "field_name")
    LOC_SAMPLE_VALUE = (By.ID, "sample_value")
    LOC_EXPECTED_TYPE = (By.ID, "expected_type")
    LOC_EXPECTED_MASKING = (By.ID, "expected_masking")
    LOC_ACCESS_ROLE = (By.ID, "access_role")
    LOC_ACTUAL_VALUE = (By.ID, "actual_value")
    LOC_SUBMIT = (By.CSS_SELECTOR, "button.validate-btn")

    # Result area locators — injected by script.js
    LOC_RESULT_CONTENT = (By.ID, "resultContent")
    LOC_VALIDATION_STATUS = (By.CSS_SELECTOR, "#resultContent .validation-status")
    LOC_FINAL_DECISION = (By.CSS_SELECTOR, "#resultContent .final-decision strong")
    LOC_RESULT_GRID_ITEMS = (By.CSS_SELECTOR, "#resultContent .result-item")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

    def open(self, url: str) -> "ValidationPage":
        self.driver.get(url)
        return self

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def _clear_and_type(self, locator, text: str) -> None:
        el = self.wait.until(EC.element_to_be_clickable(locator))
        el.clear()
        el.send_keys(str(text))

    def _select_option(self, locator, visible_text: str) -> None:
        el = self.wait.until(EC.presence_of_element_located(locator))
        Select(el).select_by_visible_text(visible_text)

    def enter_organisation(self, value: str) -> None:
        self._clear_and_type(self.LOC_ORGANISATION, value)

    def enter_partner(self, value: str) -> None:
        self._clear_and_type(self.LOC_PARTNER, value)

    def enter_field_name(self, value: str) -> None:
        self._clear_and_type(self.LOC_FIELD_NAME, value)

    def enter_sample_value(self, value: str) -> None:
        self._clear_and_type(self.LOC_SAMPLE_VALUE, value)

    def select_expected_type(self, value: str) -> None:
        self._select_option(self.LOC_EXPECTED_TYPE, value)

    def enter_expected_masking(self, value: str) -> None:
        self._clear_and_type(self.LOC_EXPECTED_MASKING, value)

    def select_access_role(self, value: str) -> None:
        self._select_option(self.LOC_ACCESS_ROLE, value)

    def enter_actual_value(self, value: str) -> None:
        self._clear_and_type(self.LOC_ACTUAL_VALUE, value)

    def click_submit(self) -> None:
        btn = self.wait.until(EC.element_to_be_clickable(self.LOC_SUBMIT))
        btn.click()

    def fill_and_submit(
        self,
        organisation: str,
        partner: str,
        field_name: str,
        sample_value: str,
        expected_type: str,
        expected_masking: str,
        access_role: str,
        actual_value: str,
    ) -> None:
        """Fill every form field and click the validate button."""
        self.enter_organisation(organisation)
        self.enter_partner(partner)
        self.enter_field_name(field_name)
        self.enter_sample_value(sample_value)
        self.select_expected_type(expected_type)
        self.enter_expected_masking(expected_masking)
        self.select_access_role(access_role)
        self.enter_actual_value(actual_value)
        self.click_submit()

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    def wait_for_result(self) -> bool:
        """Wait until the result content changes from the loading state."""
        try:
            self.wait.until(
                EC.presence_of_element_located(self.LOC_VALIDATION_STATUS)
            )
            return True
        except Exception:
            return False

    def get_publication_decision(self) -> str:
        """Return 'ALLOW' or 'BLOCK' from the final-decision element."""
        try:
            el = self.wait.until(
                EC.presence_of_element_located(self.LOC_FINAL_DECISION)
            )
            return el.text.strip()
        except Exception:
            return ""

    def get_result_content_text(self) -> str:
        """Return the full text of the result content area."""
        try:
            el = self.driver.find_element(*self.LOC_RESULT_CONTENT)
            return el.text
        except Exception:
            return ""

    def is_allow_result(self) -> bool:
        return self.get_publication_decision() == "ALLOW"

    def is_block_result(self) -> bool:
        return self.get_publication_decision() == "BLOCK"

    def get_result_items(self) -> list:
        """Return all result-grid items as WebElements."""
        try:
            return self.driver.find_elements(*self.LOC_RESULT_GRID_ITEMS)
        except Exception:
            return []

    def is_connection_error_shown(self) -> bool:
        """Return True if the 'Backend Connection Failed' error is displayed."""
        return "Backend Connection Failed" in self.get_result_content_text()

    # ------------------------------------------------------------------
    # Field visibility checks
    # ------------------------------------------------------------------

    def all_form_fields_visible(self) -> bool:
        """Verify that all 8 form fields are visible on the page."""
        locators = [
            self.LOC_ORGANISATION, self.LOC_PARTNER, self.LOC_FIELD_NAME,
            self.LOC_SAMPLE_VALUE, self.LOC_EXPECTED_TYPE, self.LOC_EXPECTED_MASKING,
            self.LOC_ACCESS_ROLE, self.LOC_ACTUAL_VALUE,
        ]
        for loc in locators:
            try:
                if not self.driver.find_element(*loc).is_displayed():
                    return False
            except Exception:
                return False
        return True
