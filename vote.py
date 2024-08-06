import os
import pickle
import time
from typing import List, Dict

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

class Voter:
    SERVER_IDS_FILE = '.server_ids.txt'
    STEAM_COOKIES_FILE = 'steam_cookies.pkl'
    MAWG_COOKIES_FILE = 'mawg_cookies.pkl'
    CLAIM_IDS = [34652, 46586, 42078]
    TIMEOUT = 3

    def __init__(self):
        load_dotenv()
        self.credentials = self._get_credentials()
        self.server_ids = self._get_server_ids()
        self.driver = self._initialize_driver()

    def _get_credentials(self) -> Dict[str, str]:
        username = os.getenv("STEAM_USERNAME")
        password = os.getenv("STEAM_PASSWORD")
        if not username or not password:
            raise ValueError("Steam credentials not found in .env file")
        return {"username": username, "password": password}

    def _get_server_ids(self) -> List[str]:
        try:
            with open(self.SERVER_IDS_FILE, 'r') as f:
                server_ids = [line.strip() for line in f if line.strip()]
            if not server_ids:
                raise ValueError("Server IDs not found in .server_ids file")
            return server_ids
        except FileNotFoundError:
            raise FileNotFoundError(f"Server IDs file '{self.SERVER_IDS_FILE}' not found")

    def _initialize_driver(self) -> webdriver.Firefox:
        return webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    def cleanup(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def _save_cookies(self, url: str, cookie_file: str):
        self.driver.get(url)
        input(f"Press Enter after you have logged into {url.split('//')[1]}")
        print(f"Saving cookies for {url.split('//')[1]}...")
        with open(cookie_file, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def _load_cookies(self, url: str, cookie_file: str):
        self.driver.get(url)
        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
        except FileNotFoundError:
            print(f"Cookies file for {url.split('//')[1]} not found. Please login manually.")
            self._save_cookies(url, cookie_file)

    def run(self):
        try:
            self._load_cookies("https://steamcommunity.com", self.STEAM_COOKIES_FILE)
            self._load_cookies("https://menatworkgaming.com", self.MAWG_COOKIES_FILE)

            for server_id in self.server_ids:
                self._vote(server_id)

            for claim_id in self.CLAIM_IDS:
                self._claim(claim_id)

            print("All tasks completed successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.cleanup()

    def _vote(self, server_id: str):
        print(f"Voting for server {server_id}...")
        wait = WebDriverWait(self.driver, self.TIMEOUT)

        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])

        try:
            self.driver.get(f"https://ark-servers.net/server/{server_id}/vote/")
            self.driver.set_window_size(1057, 896)

            self._handle_consent(wait)
            self._accept_terms(wait)
            self._click_vote_button(wait)
            self._login_to_steam(wait)
        finally:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def _handle_consent(self, wait: WebDriverWait):
        try:
            consent_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".fc-cta-consent")))
            consent_button.click()
        except:
            pass  # Consent button not present, continue

    def _accept_terms(self, wait: WebDriverWait):
        agree_terms = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#accept")))
        agree_terms.click()

    def _click_vote_button(self, wait: WebDriverWait):
        vote_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#vote-form-block > form:nth-child(3) > input:nth-child(5)")))
        vote_button.click()

    def _login_to_steam(self, wait: WebDriverWait):
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "imageLogin")))
        login_button.click()

    def _claim(self, claim_id: int):
        print(f"Claiming rewards for server {claim_id}...")
        wait = WebDriverWait(self.driver, self.TIMEOUT)

        self.driver.get("https://menatworkgaming.com/")

        claim_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f".server-block-{claim_id} > div:nth-child(2) > div:nth-child(1) > button:nth-child(1)")))
        claim_button.click()

        claim_confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#voteServer{claim_id} > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > form:nth-child(2) > button:nth-child(2)")))
        claim_confirm_button.click()