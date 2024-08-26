import os
import pickle
import time
import imaplib
import email
import re

from typing import List, Dict

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

class Voter:
    def __init__(self, server_ids_file: str, steam_cookies_file: str="steam_cookies.pkl", email_provider="gmail.com", mawg_cookies_file: str = "mawg_cookies.pkl", claim_ids: List[int] = [34652, 46586, 42078], timeout: int = 5):
        load_dotenv()
        self.SERVER_IDS_FILE = server_ids_file
        self.STEAM_COOKIES_FILE = steam_cookies_file
        self.MAWG_COOKIES_FILE = mawg_cookies_file
        self.CLAIM_IDS = [34652, 46586, 42078]
        self.TIMEOUT = timeout
        self.credentials = self._get_credentials()
        self.server_ids = self._get_server_ids()
        self.driver = self._initialize_driver()
        self.email_provider = email_provider

    def _get_credentials(self) -> Dict[str, str]:
        username = os.getenv("STEAM_USERNAME")
        password = os.getenv("STEAM_PASSWORD")
        email_user = os.getenv("EMAIL_USERNAME")
        email_pass = os.getenv("EMAIL_PASSWORD")
        if not username or not password or not email_user or not email_pass:
            raise ValueError("Credentials not found in .env file")
        return {"username": username, "password": password, "email_user": email_user, "email_pass": email_pass}

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
        with open(cookie_file, "wb") as f:
            pickle.dump(self.driver.get_cookies(), f)

    def _load_cookies(self, url: str, cookie_file: str):
        self.driver.get(url)
        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                if 'expiry' in cookie and cookie['expiry'] < time.time():
                    print(f"Cookie {cookie['name']} is expired.")
                    continue
                self.driver.add_cookie(cookie)
            self.driver.refresh()

            if not self.driver.get_cookie("steamLoginSecure"):
                print("Session expired, logging in again.")
                raise Exception("Session expired.")
        except (FileNotFoundError, Exception) as e:
            print(e)
            self._login_to_steam(url + "/login/home/?goto=")

    def _login_to_steam(self, url: str):
        print("Logging into Steam...")

        wait = WebDriverWait(self.driver, self.TIMEOUT)

        self.driver.get(url)
        username = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._3BkiHun-mminuTO-Y-zXke:nth-child(1) > input:nth-child(3)")))
        username.send_keys(self.credentials["username"])

        password = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._3BkiHun-mminuTO-Y-zXke:nth-child(2) > input:nth-child(3)")))
        password.send_keys(self.credentials["password"])

        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".DjSvCZoKKfoNSmarsEcTS")))
        login_button.click()


        # Get the verification code from email
        verification_code = self._get_verification_code()
        print(f"Verification code retrieved: {verification_code}")

        if verification_code:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "._1gzkmmy_XA39rp9MtxJfZJ")))
            # self.driver.switch_to.active_element.send_keys(verification_code)
            for char in verification_code:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(char)
            print("Logging in...")
            time.sleep(5)
            WebDriverWait(self.driver, self.TIMEOUT).until(lambda d: d.get_cookie("steamLoginSecure"))

            self._save_cookies(url, self.STEAM_COOKIES_FILE)
        else:
            raise Exception("Failed to retrieve verification code.")

    def _get_verification_code(self) -> str:
        """Fetch the Steam verification code from the email."""
        try:
            mail = imaplib.IMAP4_SSL(f"imap.{self.email_provider}")
            mail.login(self.credentials["email_user"], self.credentials["email_pass"])
            mail.select("inbox")
            _, messages = mail.search(None, '(FROM "noreply@steampowered.com")')
            mail_ids = messages[0].split()


            latest_email_id = mail_ids[-1]
            _, data = mail.fetch(latest_email_id, "(RFC822)")
            raw_email = data[0][1]

            msg = email.message_from_bytes(raw_email)
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        email_body = part.get_payload(decode=True).decode()
                        break
            else:
                email_body = msg.get_payload(decode=True).decode()
            code_match = re.search(r"\b[A-Z0-9]{5}\b", email_body)
            if code_match:
                return code_match.group(0)
            else:
                return None

        except Exception as e:
            print(f"Failed to retrieve verification code: {e}")
            return None


    def vote_and_claim(self):
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


    def vote_only(self):
        try:
            self._load_cookies("https://steamcommunity.com", self.STEAM_COOKIES_FILE)

            for server_id in self.server_ids:
                self._vote(server_id)

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
            self._click_steam_button(wait)
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
        if not agree_terms.is_selected():
            agree_terms.click()

    def _click_vote_button(self, wait: WebDriverWait):
        vote_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#vote-form-block > form:nth-child(3) > input:nth-child(5)")))
        vote_button.click()

    def _click_steam_button(self, wait: WebDriverWait):
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



# Example usage:
if __name__ == "__main__":
    voter = Voter(server_ids_file=".arklegends_servers.txt", steam_cookies_file="steam_cookies.pkl")
    voter.vote_and_claim()
