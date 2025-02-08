# ✅ 1. Python 공식 이미지 사용
FROM python:3.12-slim

# ✅ 2. 작업 디렉토리 설정
WORKDIR /app

# ✅ 3. 필요한 패키지 설치 (Chrome & Selenium)
RUN apt update && apt install -y \
    curl unzip wget gnupg ca-certificates libayatana-indicator3-7 \
    xvfb libxi6 libayatana-appindicator3-1 \
    libnss3 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm-dev libgbm1 \
    xdg-utils jq

# ✅ 4. Chrome 설치 (headless 모드, 최신 방식)
RUN mkdir -p /etc/apt/keyrings \
    && wget -q -O /etc/apt/keyrings/google-chrome.asc https://dl.google.com/linux/linux_signing_key.pub \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.asc] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

# ✅ 5. Chrome WebDriver 최신 버전 다운로드 (오류 해결 버전)
RUN apt-get install -y curl \
    && CHROME_VERSION=$(google-chrome --version | awk '{print $NF}' | cut -d'.' -f1) \
    && DRIVER_VERSION=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r ".channels.Stable.version") \
    && wget -q -O chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver.zip -d /usr/local/bin/ \
    && rm chromedriver.zip


# ✅ 6. Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 7. 크롤러 코드 복사
COPY crol.py .

# ✅ 8. 크롤러 실행
CMD ["python", "crol.py"]
