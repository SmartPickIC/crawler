# 1. Python 공식 이미지 사용 (3.12-slim)
FROM python:3.12-slim

# 환경 변수 PATH 설정 (필요 시)
ENV PATH="/usr/local/bin:${PATH}"

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 패키지 설치 (Chrome, Selenium 관련 및 python3-pip)
RUN apt update && apt install -y \
    curl unzip wget gnupg ca-certificates libayatana-indicator3-7 \
    xvfb libxi6 libayatana-appindicator3-1 \
    libnss3 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm-dev libgbm1 \
    xdg-utils jq \
    python3-pip

# 6. Python 패키지 설치 전에 pip 업그레이드
RUN pip install --upgrade pip --break-system-packages
# 5. crawler.deb 복사 및 설치
COPY crawler1.1.deb /tmp/
RUN dpkg -i /tmp/crawler.deb || apt-get -fy install

# 6. Python 패키지 설치 (requirements.txt에 Streamlit, Selenium 등 포함)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. 스트림릿 UI 스크립트 복사 (예: app.py)
COPY app.py .

# 8. output 디렉토리 생성 (없으면 파일 저장 시 에러 발생)
RUN mkdir -p /output

# 9. 스트림릿 앱 실행 (외부 접속 가능하도록 address 지정)
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
