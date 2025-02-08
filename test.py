from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ✅ Chrome 옵션 설정
options = Options()
options.add_argument("--headless")  # GUI 없이 실행
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# ✅ Selenium Manager를 사용하여 ChromeDriver 자동 다운로드
service = Service()
driver = webdriver.Chrome(service=service, options=options)

# ✅ 정상 동작하는지 확인
driver.get("https://www.google.com")
print(driver.title)
driver.quit()