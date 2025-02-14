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
import hashlib
from pathlib import Path
from danawa import ProductListManager
import pickle
# Logger 클래스: 터미널 출력과 동시에 파일에도 기록





def export_pickle_to_csv(pickle_file, output_dir):
    import pandas as pd
    """
    pickle_file에 저장된 데이터를 읽어 CSV 파일로 저장합니다.
    
    Args:
        pickle_file: 피클 파일 경로
        output_dir: 출력 디렉토리
        name_mappings: original_name 매핑 정보를 포함한 리스트
        [{
            "product_id": "",
            "index": "",
            "original_name": "",
            "name": ""
        }, ...]
    """
    # 피클 파일 로드
    try:
        with open(pickle_file, "rb") as f:
            data = pickle.load(f)
        rows=[]
        for i in range(len(data)):
            row=[ data[i].get("title"),data[i].get("view"),data[i].get("upload_date"),data[i].get("link"),data[i].get("explain")]
            rows.append(row)
        output=pd.DataFrame(rows,columns=["제목", "조회수","업로드일","링크","설명"])
        output.to_csv(output_dir, encoding="utf-8")
        return True
    except Exception as e:
        print(f"fail export pickle to csv Error :{e}")
        return False

class YouTubelistManager(ProductListManager):
    def __init__(self,
                backup_dir: str = 'backup_youtube',
                memory_threshold_mb: int = 500,
                max_items_before_dump: int = 1000,
                backup_interval_seconds: int = 300,
                max_total_size_gb: int = 20):
        self.product_lists = []
        self.backup_dir = backup_dir
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # Convert to bytes
        self.max_items = 20  # 기본값을 20으로 설정
        self.max_total_size = max_total_size_gb * 1024 * 1024 * 1024  # GB를 bytes로 변환
        self.backup_interval = backup_interval_seconds
        self.last_backup_time = time.time()
        self.backup_counter = 0
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        # Load any existing backups
        self._load_latest_backup()
    def __del__(self):
        """Ensure final backup on object destruction."""
        if self.product_lists:
            self._dump_to_pickle()
    
    def _dump_to_pickle_(self) -> None:
        """Dump current product lists to a pickle file and clear memory."""
        if not self.product_lists:
            return

        self.backup_counter += 1
        backup_filename = os.path.join(
            self.backup_dir, 
            f'youtube_metadata_backup_{self.backup_counter}.pkl'
        )
        
        # Save to pickle file
        with open(backup_filename, 'wb') as f:
            pickle.dump(self.product_lists, f)
        
        # Clear the current list to free memory
        self.product_lists = []
        self.last_backup_time = time.time()

    def merge_and_save_you(self, output_path: str, chunk_size_mb: int = 1000) -> bool:
        """
        모든 백업 데이터를 병합하여 지정된 경로에 저장합니다.
        
        Args:
            output_path: 저장할 파일 경로
            chunk_size_mb: 청크 단위 크기 (MB)
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 현재 메모리에 있는 데이터도 백업
            if self.product_lists:
                self._dump_to_pickle_()
            
            # 총 크기 확인
            total_size_gb = self.get_total_backup_size()
            if total_size_gb > self.max_total_size / (1024 * 1024 * 1024):
                print(f"경고: 총 크기({total_size_gb:.2f}GB)가 제한({self.max_total_size / (1024 * 1024 * 1024)}GB)을 초과합니다.")
                return False
                
            # 모든 데이터 수집
            all_data = []
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith('youtube_metadata_backup_') and f.endswith('.pkl')
            ])
            
            # 청크 단위로 읽고 쓰기
            chunk_size = chunk_size_mb * 1024 * 1024  # MB를 bytes로 변환
            current_chunk = []
            current_chunk_size = 0
            
            # 임시 파일들을 저장할 리스트
            temp_files = []
            
            for backup_file in backup_files:
                with open(os.path.join(self.backup_dir, backup_file), 'rb') as f:
                    data = pickle.load(f)
                    for item in data:
                        current_chunk.append(item)
                        # 대략적인 크기 추정
                        current_chunk_size += sys.getsizeof(str(item))
                        
                        if current_chunk_size >= chunk_size:
                            # 임시 파일에 청크 저장
                            temp_file = f"{output_path}.temp{len(temp_files)}"
                            with open(temp_file, 'wb') as tf:
                                pickle.dump(current_chunk, tf)
                            temp_files.append(temp_file)
                            current_chunk = []
                            current_chunk_size = 0
            
            # 마지막 청크 처리
            if current_chunk:
                temp_file = f"{output_path}.temp{len(temp_files)}"
                with open(temp_file, 'wb') as tf:
                    pickle.dump(current_chunk, tf)
                temp_files.append(temp_file)
            
            # 모든 임시 파일들을 하나로 병합
            all_data = []
            for temp_file in temp_files:
                with open(temp_file, 'rb') as f:
                    all_data.extend(pickle.load(f))
                os.remove(temp_file)  # 임시 파일 삭제
            
            # 최종 파일 저장
            with open(output_path, 'wb') as f:
                pickle.dump(all_data, f)
            try:
                for backup_file in backup_files:
                    os.remove(os.path.join(self.backup_dir, backup_file))
                print(f"✅ 백업된 {len(backup_files)}개 파일을 성공적으로 삭제했습니다.")
            except Exception as e:
                print(f"⚠️ 백업 파일 삭제 중 오류 발생: {str(e)}")
            return True  
        except Exception as e:
            print(f"병합 중 오류 발생: {str(e)}")
            # 임시 파일들 정리
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return False
        
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
    except:
        print("자막이 없습니다.")




def scroll_down(driver,n=10):
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(Keys.PAGE_DOWN)
    for _ in range(n):  # 10번 스크롤
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(1)  # 로딩될 시간 고려

def get_metadata(link):
    options1 = Options()
    #options1.add_argument('--headless')
    options1.add_argument('--disable-gpu')
    options1.add_argument('--no-sandbox')
    options1.add_argument("--disable-dev-shm-usage")
    options1.add_argument("--remote-debugging-port=9223")
    options1.add_argument("--incognito")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options1)
    driver.get(link)
    
    loop_extend=True
    loop_num=0
    loop_max=20
    while loop_extend:
        try:
            expand = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#expand")))
            if isinstance(expand,list):
                expand[0].click()
                break
            else:
                expand.click()
                break
        except:
            loop_num+=1
            time.sleep(1)
            if loop_num>loop_max:
                print("fail click expand")
                driver.quit()
                return "fail click expand"
    loop_elem=True
    loop_num_elem=0
    loop_max_elem=20
    while loop_elem:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "#description-inline-expander > yt-attributed-string > span > span")
            combined_text = " ".join([elem.text for elem in elements])
            return combined_text
        except:
            loop_num_elem+=1
            time.sleep(1)
            if loop_num_elem>loop_max_elem:
                print("fail get elements")
                return "fail get elements"
        finally:
            driver.quit()
                   
            
            



def automatic_retry(selector, driver, by=By.CSS_SELECTOR, attempts=10):
    num=0
    loop=True
    while loop:
        try:
            title_sl=driver.find_elements(by, selector)
            if isinstance(title_sl,list):
                out=title_sl[0].text
            else:
                out=title_sl.text
            return out
        except:
            num+=1
            time.sleep(1)
            if num>attempts:
                loop=False
                return False

def save_script(driver,search_query,save_path,flag_file_path,data):
    # ✅ 부모 요소 (`ytd-rich-item-renderer:nth-child(2)`) 찾기
    i=1
    scrol=0
    
    while True:
        try:

            loopdata={}
            css_selector = f"#contents > ytd-rich-item-renderer:nth-child({i})"
            parent_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
            title=automatic_retry("#video-title",parent_element)
            if title:
                loopdata['title']=title
            else:
                loopdata['title']="fail get title"
            view=automatic_retry("#metadata-line > span:nth-child(3)",parent_element)
            if view:
                loopdata['view']=view
            else:
                loopdata['view']="fail get view"
            upload=automatic_retry("#metadata-line > span:nth-child(4)",parent_element)
            if upload:
                loopdata['upload_date']=upload
            else:
                loopdata['upload_date']="fail get upload_date"
            # ✅ 부모 요소 내부의 `#video-title-link` 찾기 (직계 자식이 아니어도 찾을 수 있도록 수정)
            video_link_element = parent_element.find_element(By.CSS_SELECTOR, ":scope #video-title-link")
                # ✅ `href` 속성 가져오기
            video_url = video_link_element.get_attribute("href")
            loopdata["link"]=video_url
            loopdata["explain"]=get_metadata(video_url)
            print(f"✅ 추출한 링크: {video_url}")
            save_captions(video_url,search_query,i,save_path)
            i+=1
            scrol=0
            with open(flag_file_path, 'r') as f:
                flag = f.readline()
            if flag.strip() != "1":
                break
            data.append(loopdata)
        except:
            if loopdata and loopdata.keys() is not None and len(loopdata.keys())>0 and len(data)<i:
                data.append(loopdata)
            elif len(data)==i:
                data.append("fail get data")
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
    csv_path = Path(save_path+'/csv')
    csv_path.mkdir(parents=True, exist_ok=True)
    backup_dir=save_path+"/backup"
    pickle_path = Path(save_path+'/pickle')
    pickle_path.mkdir(parents=True, exist_ok=True)
    hashed_filename = hashlib.sha256(search_query.encode("utf-8")).hexdigest()
    data=YouTubelistManager(backup_dir=backup_dir+hashed_filename)
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
    save_path = os.path.join(base_dir, save_base, search_query)
    os.makedirs(save_path, exist_ok=True)
    log_file = os.path.join(save_path, f"{search_query}.txt")
    sys.stdout = Logger(log_file)
    save_script(driver,search_query,save_path,flag_file_path,data)
    driver.quit() 
    murged_pickle=str(pickle_path) + "/" + str(hashed_filename) + ".pickle"
    csv_file = str(csv_path) + "/" + str(hashed_filename) + ".csv"
    data.merge_and_save_you(murged_pickle)
    export_pickle_to_csv(murged_pickle, csv_file)


if __name__ == "__main__":
    run()
    print("정상 종료")











