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

# ✅ 4. Chrome .deb 파일 복사 및 설치
COPY google-chrome-stable_current_amd64.deb /tmp/
RUN dpkg -i /tmp/google-chrome-stable_current_amd64.deb || apt-get -fy install

# ✅ 6. Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 7. 크롤러 코드 복사
COPY crol.py .

# ✅ 8. 크롤러 실행
CMD ["python", "crol.py"]
