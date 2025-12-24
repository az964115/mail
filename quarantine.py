from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

LOGIN_URL = "https://192.168.8.25:800/login.php"
USERNAME = "admin"
PASSWORD = "boxadmin"

class Quarantine:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        # chrome_options.add_argument("--headless")  # 先不要用 headless
        self.driver = webdriver.Chrome(options=chrome_options)
        self.login()

    def login(self):
        self.driver.get(LOGIN_URL)
        wait = WebDriverWait(self.driver, 10)

        # 輸入帳號密碼
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "ID")))
        username_input.send_keys(USERNAME)

        password_input = self.driver.find_element(By.NAME, "PASSWORD")
        password_input.send_keys(PASSWORD)

        # 點登入按鈕
        login_btn = self.driver.find_element(By.XPATH, '//a[@class="BUTTON" and text()="登入"]')
        login_btn.click()

        # 等待跳轉到搜尋頁
        time.sleep(2)
        self.driver.get("https://192.168.8.25:800/?page=ST&op=search&mod=search&selecttab=0")
        print("[LOGIN] 登入完成並進入搜尋頁")

    def search_quarantine(self, subject, time_period="3"):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        # 切換到搜尋 iframe
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)
        print("[INFO] 已切換到 iframe")

        # 選擇隔離郵件
        driver.find_element(By.CSS_SELECTOR, 'label[for="search_range_quarantine"]').click()

        # 選擇時間區間
        driver.find_element(By.CSS_SELECTOR, f'label[for="search_timeperiod{time_period}"]').click()

        # 輸入主旨
        search_input = driver.find_element(By.NAME, "subject")
        search_input.clear()
        search_input.send_keys(subject)

        # 點擊查詢（使用 JS 確保能點擊）
        search_btn = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, '//a[contains(@class,"CENTER") and contains(normalize-space(.),"查詢")]')
            )
        )
        driver.execute_script("arguments[0].click();", search_btn)
        print("[INFO] 已點擊查詢")

        # 等待結果表格
        time.sleep(3)
        results = []
        try:
            table = driver.find_element(By.ID, "resultTable")
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if cols:
                    results.append({
                        "date": cols[0].text,
                        "from": cols[1].text,
                        "subject": cols[2].text
                    })
        except:
            pass

        return results
