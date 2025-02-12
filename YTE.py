import sys
from pytubefix import YouTube
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import argparse
from pathlib import Path
# Logger 클래스: 터미널 출력과 동시에 파일에도 기록
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout  # 원래 stdout 저장
        self.log = open(filename, "a", encoding="utf-8")  # 로그 파일 오픈
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()

def save_captions(link,search_query,i,save_path):
        # ✅ 현재 작업 디렉토리 가져오기
    base_dir = os.getcwd()
    
    # ✅ 디렉토리 확인 및 생성
    os.makedirs(save_path, exist_ok=True)
    #link = input("자막을 다운로드할 영상 링크를 입력하세요: ")
    yt = YouTube(link)
    filename = f"{i}.mp3"
    download_path = yt.streams.filter(only_audio=True).first().download(output_path=save_path, filename=filename)
    # 사용 가능한 자막 목록 출력

    # 원하는 자막 언어 코드 입력 (예: 'en' 또는 'ko')
    #language_code = input("다운로드할 자막의 언어 코드를 입력하세요 (예: en, ko): ")
    try:
        language_code = "a.ko"
        # 해당 언어의 자막 객체 가져오기
        caption = yt.captions.get(language_code)
        if caption:
            # SRT 형식으로 자막 생성
            srt_captions = caption.generate_srt_captions()
            # 파일로 저장 (파일 이름은 영상 제목과 언어 코드 사용)
            filename = os.path.join(save_path, f"{i}.srt")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(srt_captions)
            print(f"자막이 '{filename}' 파일로 저장되었습니다.")
        else:
            print("입력한 언어 코드에 해당하는 자막이 존재하지 않습니다.")

        lines = srt_captions.splitlines()
        text_lines = []
        for line in lines:
            # 순수 숫자(번호)만 있는 줄은 건너뜁니다.
            if re.match(r'^\d+$', line):
                continue
            # 타임스탬프 형식 (예: 00:00:01,000 --> 00:00:04,000)인 줄은 건너뜁니다.
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            # 빈 줄도 건너뜁니다.
            if line.strip() == "":
                continue
            # 나머지 자막 텍스트 라인만 추가
            text_lines.append(line)
            txt_captions = "\n".join(text_lines)
            filename_txt = os.path.join(save_path, f"{i}.txt")
            with open(filename_txt, "w", encoding="utf-8") as f:
                f.write(txt_captions)    
        else:
            print("입력한 언어 코드에 해당하는 자막이 존재하지 않습니다.")
    except:
        print("자막이 없습니다.")




def scroll_down(driver,n=10):
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(Keys.PAGE_DOWN)
    for _ in range(n):  # 10번 스크롤
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)  # 로딩될 시간 고려




def save_script(driver,search_query,save_path,flag_file_path):
    # ✅ 부모 요소 (`ytd-rich-item-renderer:nth-child(2)`) 찾기
    i=1
    scrol=0
    while True:
        try:
            css_selector = f"#contents > ytd-rich-item-renderer:nth-child({i})"
            parent_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )

            # ✅ 부모 요소 내부의 `#video-title-link` 찾기 (직계 자식이 아니어도 찾을 수 있도록 수정)
            video_link_element = parent_element.find_element(By.CSS_SELECTOR, ":scope #video-title-link")
                # ✅ `href` 속성 가져오기
            video_url = video_link_element.get_attribute("href")
            print(f"✅ 추출한 링크: {video_url}")
            save_captions(video_url,search_query,i,save_path)
            i+=1
            scrol=0
            with open(flag_file_path, 'r') as f:
                flag = f.readline()
            if flag.strip() != "1":
                break
        except:
            scroll_down(driver,n=10)
            scrol+=1
            if scrol>3:
                break
       
def run(search_query="잇섭",save_base="output/youtube",folder_path="잇섭"):
    base_dir = os.getcwd()
    save_path = os.path.join(base_dir, save_base, folder_path)
    os.makedirs(save_path, exist_ok=True)
    log_file = os.path.join(save_path, f"{search_query}.txt")
    flag_file_path = Path(save_path+'/flag.txt')
    flag_file_path.touch()
    with open(flag_file_path, 'w') as f:
        f.write("1")
    sys.stdout = Logger(log_file)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--incognito")
    service = Service()  
    driver = webdriver.Chrome(service=service, options=options)
    print("테스트 로그: 이 메시지가 파일에도 기록되어야 합니다.")
    driver.get("https://www.youtube.com")
    time.sleep(3)  # 페이지 로딩 대기


    search_box = driver.find_element(By.NAME, "search_query")



    search_box.send_keys(search_query)


    search_box.send_keys(Keys.ENTER)

    time.sleep(5)

    move_channel = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#main-link")))

    driver.execute_script("arguments[0].click();", move_channel[0])


    move_tap = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#tabsContent > yt-tab-group-shape > div.yt-tab-group-shape-wiz__tabs > yt-tab-shape:nth-child(2)"))
    )

    move_tap.click()
    # **로그 저장 설정**  
    # save_path 폴더를 생성하고, 그 안에 search_query와 동일한 이름의 텍스트 파일을 만듭니다.
    base_dir = os.getcwd()
    save_path = os.path.join(base_dir, args.save_base, search_query)
    os.makedirs(save_path, exist_ok=True)
    log_file = os.path.join(save_path, f"{search_query}.txt")
    sys.stdout = Logger(log_file)
    
    save_script(driver,search_query,save_path,flag_file_path)

    driver.quit()











if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YOUTUBE script download')
    parser.add_argument('--search_query', type=str, default="잇섭", help='검색어 입력') 
    parser.add_argument('--save_base', type=str, default="output/youtube", help='저장 베이스 경로')
    args=parser.parse_args()
    search_query = args.search_query
    parser.add_argument('--folder_path', type=str, default=search_query, help='저장할 폴더 이름')
    args=parser.parse_args()
    base_dir = os.getcwd()
    save_path = os.path.join(base_dir, args.save_base, args.folder_path)
    os.makedirs(save_path, exist_ok=True)
    log_file = os.path.join(save_path, f"{search_query}.txt")
    flag_file_path = Path(save_path+'/flag.txt')
    flag_file_path.touch()
    with open(flag_file_path, 'w') as f:
        f.write("1")
    sys.stdout = Logger(log_file)
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--incognito")
    service = Service()  
    driver = webdriver.Chrome(service=service, options=options)
    print("테스트 로그: 이 메시지가 파일에도 기록되어야 합니다.")
    driver.get("https://www.youtube.com")
    time.sleep(3)  # 페이지 로딩 대기


    search_box = driver.find_element(By.NAME, "search_query")



    search_box.send_keys(search_query)


    search_box.send_keys(Keys.ENTER)

    time.sleep(5)

    move_channel = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#main-link")))

    driver.execute_script("arguments[0].click();", move_channel[0])


    move_tap = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#tabsContent > yt-tab-group-shape > div.yt-tab-group-shape-wiz__tabs > yt-tab-shape:nth-child(2)"))
    )

    move_tap.click()
    # **로그 저장 설정**  
    # save_path 폴더를 생성하고, 그 안에 search_query와 동일한 이름의 텍스트 파일을 만듭니다.
    base_dir = os.getcwd()
    save_path = os.path.join(base_dir, args.save_base, search_query)
    os.makedirs(save_path, exist_ok=True)
    log_file = os.path.join(save_path, f"{search_query}.txt")
    sys.stdout = Logger(log_file)
    
    save_script(driver,search_query,save_path,flag_file_path)

    driver.quit()














