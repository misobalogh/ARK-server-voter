from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import os
import pickle
import time

SERVER_IDS_FILE = '.server_ids.txt'
STEAM_COOKIES_FILE = 'steam_cookies.pkl'
MAWG_COOKIES_FILE = 'mawg_cookies.pkl'
CLAIM_IDS = [34652, 46586, 42078]

class Voter():
    def __init__(self):
        load_dotenv()
        self.credentials = self.get_credentials()
        self.server_ids = self.get_server_ids(SERVER_IDS_FILE)
        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    def get_credentials(self):
        credentials = {
            "username": os.getenv("STEAM_USERNAME"),
            "password": os.getenv("STEAM_PASSWORD")
        }
        if not credentials["username"] or not credentials["password"]:
            raise Exception("Steam credentials not found in .env file")
        return credentials

    def get_server_ids(self, file):
        with open(file, 'r') as f:
            server_ids = [line.strip() for line in f if line.strip()]
        if not server_ids:
            raise Exception("Server IDs not found in .server_ids file")
        return server_ids

    def cleanup(self):
        if self.driver:
            self.driver.quit()

    def save_cookies(self, url, cookie_file):
        driver = self.driver
        driver.get(url)
        input(f"Press Enter after you have logged into {url.split('//')[1]}")
        print("Saving Cookies...")
        with open(cookie_file, "wb") as f:
            pickle.dump(driver.get_cookies(), f)

    def load_cookies(self, url, cookie_file):
        driver = self.driver
        driver.get(url)
        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
        except FileNotFoundError:
            print(f"Cookies file for {url.split('//')[1]} not found. Please login manually the first time.")
            self.save_cookies(url, cookie_file)

    def run(self):
        try:
            self.load_cookies("https://steamcommunity.com", STEAM_COOKIES_FILE)
            self.load_cookies("https://menatworkgaming.com", MAWG_COOKIES_FILE)
        except Exception as e:
            print(f"An error occurred: {e}")
            self.save_cookies("https://steamcommunity.com", STEAM_COOKIES_FILE)
            self.save_cookies("https://menatworkgaming.com", MAWG_COOKIES_FILE)

        for server_id in self.server_ids:
            self.vote(server_id)

        claim_ids = CLAIM_IDS

        for id in claim_ids:
            self.claim(id)

        print("Everything ran successfully, exiting...")
        self.cleanup()

    def steam_login(self, driver):
        wait = WebDriverWait(driver, 10)
        username_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._3BkiHun-mminuTO-Y-zXke:nth-child(1) > input:nth-child(3)")))
        username_input.send_keys(self.credentials["username"])

        password_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div._3BkiHun-mminuTO-Y-zXke:nth-child(2) > input:nth-child(3)")))
        password_input.send_keys(self.credentials["password"])

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".DjSvCZoKKfoNSmarsEcTS")))
        submit_button.click()

    def MAWG_login(self, driver):
        wait = WebDriverWait(driver, 10)
        driver.get("https://menatworkgaming.com/")

        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-default")))
        login_button.click()

        steam_login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn:nth-child(2)")))
        steam_login_button.click()

        input("Press Enter after you login to MAWG.")
        self.steam_login(driver)

    def vote(self, server_id):
        print(f"Voting for server {server_id}...")

        driver = self.driver
        wait = WebDriverWait(driver, 5)

        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])

        driver.get(f"https://ark-servers.net/server/{server_id}/vote/")
        driver.set_window_size(1057, 896)

        try:
            consent_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".fc-cta-consent")))
            consent_button.click()
        except:
            pass

        agree_terms = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#accept")))
        agree_terms.click()

        vote_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#vote-form-block > form:nth-child(3) > input:nth-child(5)")))
        vote_button.click()

        driver.close()
        driver.switch_to.window(driver.window_handles[0])


    def claim(self, id):
        print(f"Claiming rewards for server {id}...")

        driver = self.driver
        wait = WebDriverWait(driver, 5)

        driver.get("https://menatworkgaming.com/")

        claim_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f".server-block-{id} > div:nth-child(2) > div:nth-child(1) > button:nth-child(1)")))
        claim_button.click()

        claim_confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"#voteServer{id} > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > form:nth-child(2) > button:nth-child(2)")))
        claim_confirm_button.click()
