import random
import time

from lxml import html
from lxml.html import HtmlElement
import requests
from requests.models import Response
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager


class ParserMixin:
    COOKIE_KEYS = ["name", "value", "domain"]

    def __init__(self) -> None:
        """
        """
        self.session = None
        self.driver = None

    def start_driver(self, headless=False, chrome_driver_path: str = None) -> None:
        """
        """
        chrome_options = webdriver.chrome.options.Options()
        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        cache_manager = None
        if chrome_driver_path:
            cache_manager = DriverCacheManager(root_dir=chrome_driver_path)
        executable_path = ChromeDriverManager(cache_manager=cache_manager).install()
        service = webdriver.chrome.service.Service(executable_path=executable_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def quit_driver(self) -> None:
        """
        """
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                print(e)

    def wait_for_xpath(self, xpath: str, err_xpaths: list = []) -> None:
        """
        """
        for _ in range(10):
            try:
                self.driver.find_element("xpath", xpath)
                break
            except NoSuchElementException:
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                raise e
        else:
            raise Exception(f"Element with xpath {xpath} not found after multiple attempts")

    def get_cookies(self, cookie_names: list = []) -> None:
        """
        """
        all_c = [{k: c[k] for k in self.COOKIE_KEYS} for c in self.driver.get_cookies()]
        if cookie_names == []:
            return all_c
        return [c for c in all_c if c["name"] in cookie_names]

    def start_session(self,
                      headers: dict = {},
                      cookies: list = [],
                      proxies: dict = {}) -> None:
        """
        """
        session = requests.Session()
        if headers:
            session.headers.update(headers)
        for cookie in cookies:
            session.cookies.set(**cookie)
        if proxies:
            session.proxies.update(proxies)
        self.session = session

    def requests_from_session(self, url: str) -> Response:
        """
        """
        response = None
        for _ in range(3):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"err {e}")
            if response:
                if response.status_code == 404:
                    raise Exception("404_ERROR")
            time.sleep(random.uniform(0.5, 2))
        else:
            raise Exception(f"Could not be reached: {url}")

    def get_tree_from_session(self, url: str) -> HtmlElement:
        """
        """
        response = self.requests_from_session(url)
        return html.fromstring(response.text)
