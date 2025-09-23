import re
import os
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_normal_driver(headless=True, max_retries=3):
    for attempt in range(max_retries):
        driver = None
        try:
            options = webdriver.ChromeOptions()
            path = rf'{BASE_DIR}\chrome-dir'

            # Ensure chrome-dir exists
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"Created chrome directory: {path}")
                except OSError as e:
                    print(f"Failed to create chrome directory: {e}")
                    path = None

            if path:
                options.add_argument(f'--user-data-dir={path}')

            # Enhanced options for stability
            options.add_argument("--log-level=3")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-ipc-flooding-protection")

            if headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")
            else:
                options.add_argument("--start-maximized")

            # Experimental options for better stability
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

            # Allow the browser to fully initialize
            time.sleep(3)

            # Enhanced fingerprinting protection
            stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
            """
            driver.execute_script(stealth_js)

            # Test driver functionality
            driver.get("data:,")
            print(f"Chrome driver initialized successfully (attempt {attempt + 1})")
            return driver

        except Exception as e:
            print(f"Driver creation attempt {attempt + 1} failed: {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass

            if attempt < max_retries - 1:
                print(f"Retrying driver creation... Attempts left: {max_retries - attempt - 1}")
                time.sleep(3)
            else:
                print("Max retries exceeded. Could not create the driver.")
                return None

    return None


def check_element_visibility_and_return_property(driver, by_locator, property_name):
    try:
        element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(by_locator))
        if property_name == "text":
            return element.text.strip()
        elif property_name == "href":
            return element.get_attribute("href").strip()
        else:
            print(f"Unsupported property: {property_name}")
    except:
        print(f"Element not found or not visible: {by_locator}")
        return ''


def _to_int(text: str) -> int:
    m = re.search(r'\d+', text or '')
    return int(m.group()) if m else 0


def check_element_is_clickable(driver, by_locator):
    try:
        element = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(by_locator))
        return element
    except:
        print(f"Element not found or not clickable: {by_locator}")
        return None


def _read_done_set(path: str = 'done/done.txt') -> set[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def create_xpath_1(title):
    return f"//span[text()= '{title} :']/parent::span"


def create_xpath_2(title, tag):
    return f"//div[text()= '{title}']/parent::td/following-sibling::td/{tag}"


def clean_job_info(text):
    if not text:
        return ''
    text = text.split(':')[-1].strip()
    return text


def safe_get_job_detail(driver, by_locator, property_name, retries=2):
    for attempt in range(retries):
        try:
            value = check_element_visibility_and_return_property(driver, by_locator, property_name)
            return value if value else ''
        except Exception as e:
            print(f"Error getting {by_locator} ({property_name}): {e}, attempt {attempt + 1}")
            time.sleep(1)
    return ''


def wait_for_page_load(driver, timeout: int = 30) -> bool:
    """Wait for page to fully load with exception handling."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)  # Additional buffer
        return True
    except TimeoutException:
        print(f"Page load timeout after {timeout} seconds")
        return False
    except WebDriverException as e:
        print(f"Error waiting for page load: {e}")
        return False


def safe_navigate_to_url(driver, url: str, max_retries: int = 3) -> bool:
    """Navigate to URL with retry logic and exception handling."""
    for attempt in range(max_retries):
        try:
            driver.get(url)
            if wait_for_page_load(driver):
                # print(f"Successfully navigated to: {url}")
                return True
            else:
                print(f"Page load incomplete for: {url}")
        except WebDriverException as e:
            print(f"Navigation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue

    print(f"Failed to navigate to {url} after {max_retries} attempts")
    return False
