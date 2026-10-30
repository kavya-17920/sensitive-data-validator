"""
conftest.py — Shared Selenium fixtures for Sensitive Data Validator tests.

Provides:
  - A Chrome WebDriver (headless or normal) via the ``driver`` fixture.
  - Automatic screenshot capture on test failure.
  - Constants for base URLs (frontend served via Live Server / file, backend API).

The driver uses Selenium Manager (bundled since Selenium 4.6+) so no
manual ChromeDriver download is needed.
"""

import os
import datetime
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Import shared URL constants
import sys
sys.path.insert(0, os.path.dirname(__file__))
from constants import FRONTEND_URL, BACKEND_URL, DASHBOARD_URL, API_DOCS_URL  # noqa: F401

# Directory to save failure screenshots
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "reports", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _build_options(headless: bool = True) -> Options:
    """Build Chrome options. Always runs headless in CI; optional locally."""
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--log-level=3")
    return opts


@pytest.fixture(scope="session")
def headless() -> bool:
    """Control headless mode via --headless CLI flag (default: True)."""
    # Pass --no-headless on the pytest command line to watch the browser live.
    return True


@pytest.fixture(scope="function")
def driver(headless, request):
    """
    Yield a fresh Chrome WebDriver for each test function.
    Captures a screenshot to reports/screenshots/ if the test fails.
    """
    opts = _build_options(headless=headless)
    # Selenium Manager resolves the ChromeDriver automatically (Selenium >= 4.6)
    drv = webdriver.Chrome(options=opts)
    drv.set_page_load_timeout(30)
    drv.implicitly_wait(5)

    yield drv

    # ----- Teardown -----
    # Capture screenshot on failure
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = request.node.name.replace("/", "_").replace(":", "_")
        path = os.path.join(SCREENSHOTS_DIR, f"{safe_name}_{timestamp}.png")
        try:
            drv.save_screenshot(path)
            print(f"\n[SCREENSHOT] Saved to {path}")
        except Exception:  # noqa: BLE001
            pass

    drv.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach test outcome to the request node so the driver fixture can read it."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
