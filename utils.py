import re
import os
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_normal_driver(headless=False, max_retries=3):
    try:
        options = webdriver.ChromeOptions()
        path = rf'{BASE_DIR}\chrome-dir'
        options.add_argument(f'--user-data-dir={path}')
        options.add_argument("--log-level=3")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if not headless:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")

        # Initialize normal Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        time.sleep(2)  # Allow the browser to fully initialize

        # Additional fingerprinting tweaks (remove WebDriver flag)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return driver

    except Exception as e:
        print(f"Error: {e}")
        if max_retries > 0:
            print(f"Retrying... Attempts left: {max_retries}")
            time.sleep(2)
            return get_normal_driver(headless=headless, max_retries=max_retries - 1)
        else:
            print("Max retries exceeded. Could not create the driver.")
            return None

def check_element_visibility_and_return_property(driver, by_locator, property_name):
    try:
        element = WebDriverWait(driver, 1).until(EC.visibility_of_element_located(by_locator))
        if property_name == "text":
            return element.text.strip()
        elif property_name == "href":
            return element.get_attribute("href").strip()
        else: print(f"Unsupported property: {property_name}")
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
            print(f"Error getting {by_locator} ({property_name}): {e}, attempt {attempt+1}")
            time.sleep(1)
    return ''
