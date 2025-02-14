import os
import re
from pathlib import Path
import tqdm
import pandas as pd
from pathlib import Path
import ast
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tqdm
import pandas as pd
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from pathlib import Path
import pickle
import os
from pathlib import Path
from difflib import SequenceMatcher
import requests
import csv
import argparse
import hashlib
import threading
from time import sleep
import time
from typing import List, Any
import psutil
import sys
class ProductListManager:
    def __init__(self, 
                 backup_dir: str = 'backup',
                 memory_threshold_mb: int = 500,
                 max_items_before_dump: int = 1000,
                 backup_interval_seconds: int = 300,
                 max_total_size_gb: int = 20):
        """
        Initialize the ProductListManager.
        
        Args:
            backup_dir: Directory to store pickle backups
            memory_threshold_mb: Memory threshold in MB before forcing a dump
            max_items_before_dump: Maximum items to hold before forcing a dump
            backup_interval_seconds: Minimum time between backups in seconds
            max_total_size_gb: Maximum total size of all backups in GB
        """
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

    def append(self, item: Any) -> None:
        """Add an item to the product list and handle automatic backup if needed."""
        self.product_lists.append(item)
        
        # Check if we need to dump based on various conditions
        if self._should_dump():
            self._dump_to_pickle()

    def _should_dump(self) -> bool:
        """Check if we should dump based on memory usage, item count, and time."""
        current_time = time.time()
        time_since_last_backup = current_time - self.last_backup_time
        
        # Get current memory usage
        process = psutil.Process(os.getpid())
        current_memory = process.memory_info().rss
        
        return (
            current_memory >= self.memory_threshold or
            len(self.product_lists) >= self.max_items or
            time_since_last_backup >= self.backup_interval
        )

    def _dump_to_pickle(self) -> None:
        """Dump current product lists to a pickle file and clear memory."""
        if not self.product_lists:
            return

        self.backup_counter += 1
        backup_filename = os.path.join(
            self.backup_dir, 
            f'product_lists_backup_{self.backup_counter}.pkl'
        )
        
        # Save to pickle file
        with open(backup_filename, 'wb') as f:
            pickle.dump(self.product_lists, f)
        
        # Clear the current list to free memory
        self.product_lists = []
        self.last_backup_time = time.time()

    def _load_latest_backup(self) -> None:
        """Load the most recent backup if it exists."""
        backup_files = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('product_lists_backup_') and f.endswith('.pkl')
        ])
        
        if backup_files:
            latest_backup = backup_files[-1]
            self.backup_counter = int(latest_backup.split('_')[-1].split('.')[0])
            
            with open(os.path.join(self.backup_dir, latest_backup), 'rb') as f:
                self.product_lists = pickle.load(f)

    def get_all_data(self) -> List[Any]:
        """
        Combine all data from backups and current list.
        Warning: This may use a lot of memory if there are many backups.
        """
        all_data = []
        
        # Load data from all backup files
        backup_files = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('product_lists_backup_') and f.endswith('.pkl')
        ])
        
        for backup_file in backup_files:
            with open(os.path.join(self.backup_dir, backup_file), 'rb') as f:
                all_data.extend(pickle.load(f))
        
        # Add current data
        all_data.extend(self.product_lists)
        
        return all_data

    def get_backup_info(self) -> List[dict]:
        """백업 파일들의 정보를 반환합니다."""
        backup_files = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('product_lists_backup_') and f.endswith('.pkl')
        ])
        
        info_list = []
        for backup_file in backup_files:
            file_path = os.path.join(self.backup_dir, backup_file)
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                info_list.append({
                    'filename': backup_file,
                    'size_mb': file_size / (1024 * 1024),
                    'items_count': len(data)
                })
        return info_list

    def load_specific_backup(self, backup_number: int) -> List[Any]:
        """특정 백업 파일만 로드합니다."""
        filename = f'product_lists_backup_{backup_number}.pkl'
        file_path = os.path.join(self.backup_dir, filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError(f"Backup {backup_number} not found")

    def load_range(self, start_backup: int, end_backup: int) -> List[Any]:
        """특정 범위의 백업 파일들을 로드합니다."""
        all_data = []
        for backup_num in range(start_backup, end_backup + 1):
            try:
                data = self.load_specific_backup(backup_num)
                all_data.extend(data)
            except FileNotFoundError:
                continue
        return all_data

    def __len__(self) -> int:
        """Return the total number of items across all backups and current list."""
        total_items = len(self.product_lists)
        
        for backup_file in os.listdir(self.backup_dir):
            if backup_file.startswith('product_lists_backup_') and backup_file.endswith('.pkl'):
                with open(os.path.join(self.backup_dir, backup_file), 'rb') as f:
                    total_items += len(pickle.load(f))
        
        return total_items

    def __getitem__(self, index):
        """일반 리스트처럼 인덱싱을 지원합니다."""
        if isinstance(index, slice):
            # 슬라이싱의 경우
            return self.get_all_data()[index]
        
        # 단일 인덱스의 경우
        if index < 0:  # 음수 인덱스 처리
            index = len(self) + index
            
        # 현재 메모리의 리스트 확인
        if index < len(self.product_lists):
            return self.product_lists[index]
            
        # 백업 파일들을 순회하며 해당 인덱스 찾기
        current_pos = len(self.product_lists)
        backup_files = sorted([
            f for f in os.listdir(self.backup_dir)
            if f.startswith('product_lists_backup_') and f.endswith('.pkl')
        ])
        
        for backup_file in backup_files:
            with open(os.path.join(self.backup_dir, backup_file), 'rb') as f:
                backup_data = pickle.load(f)
                backup_len = len(backup_data)
                if current_pos + backup_len > index:
                    # 이 백업 파일에 해당 인덱스가 있음
                    return backup_data[index - current_pos]
                current_pos += backup_len
                
        raise IndexError("list index out of range")

    def __del__(self):
        """Ensure final backup on object destruction."""
        if self.product_lists:
            self._dump_to_pickle()
            
    def get_total_backup_size(self) -> float:
        """모든 백업 파일의 총 크기를 GB 단위로 반환합니다."""
        total_size = 0
        for backup_file in os.listdir(self.backup_dir):
            if backup_file.startswith('product_lists_backup_') and backup_file.endswith('.pkl'):
                file_path = os.path.join(self.backup_dir, backup_file)
                total_size += os.path.getsize(file_path)
        return total_size / (1024 * 1024 * 1024)  # Convert to GB


    def merge_and_save(self, output_path: str, chunk_size_mb: int = 1000) -> bool:
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
                self._dump_to_pickle()
            
            # 총 크기 확인
            total_size_gb = self.get_total_backup_size()
            if total_size_gb > self.max_total_size / (1024 * 1024 * 1024):
                print(f"경고: 총 크기({total_size_gb:.2f}GB)가 제한({self.max_total_size / (1024 * 1024 * 1024)}GB)을 초과합니다.")
                return False
                
            # 모든 데이터 수집
            all_data = []
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith('product_lists_backup_') and f.endswith('.pkl')
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



class SplitTuple(tuple):
    def split(self, sep=None):
        # 튜플의 모든 요소를 문자열로 변환하고 연결
        joined = ''.join(str(x) for x in self)
        # 문자열을 split하고 결과를 다시 SplitTuple로 변환
        return SplitTuple(joined.split(sep))
    
    
def extract_set_from_string(raw_string, keyword_set):
    """
    슬라이딩 윈도우 방식으로 `raw_string`에서 `keyword_set`에 포함된 모든 단어를 빠짐없이 탐색하여 리스트로 반환.

    :param raw_string: 공백 없는 입력 문자열
    :param keyword_set: 찾고자 하는 키워드 집합 (set)
    :return: 매칭된 단어 리스트 (모든 키워드를 빠짐없이 탐색)
    """
    matches = []
    length = len(raw_string)
    
    while raw_string:  # ✅ 문자열이 남아있는 동안 반복
        match_found = False
        for size in range(length, 0, -1):  # ✅ 긴 키워드부터 탐색
            substring = raw_string[:size]  # ✅ 문자열의 처음부터 `size`만큼 가져오기
            if substring in keyword_set:
                matches.append(substring)
                raw_string = raw_string[size:]  # ✅ 매칭된 부분 제거 후 다시 처음부터 탐색
                match_found = True
                break  # ✅ 가장 긴 매칭을 우선 사용하고, 다시 처음부터 탐색
        if not match_found:
            raw_string = raw_string[1:]  # ✅ 매칭이 없으면 한 글자씩 이동
    
    return matches

def extract_patterns_from_string(raw_string, patterns):
    """
    슬라이딩 윈도우 방식으로 특정 정규식 패턴과 일치하는 모든 단어를 추출.

    :param raw_string: 띄어쓰기 없는 입력 문자열
    :param patterns: 찾고자 하는 정규식 패턴 리스트
    :return: 패턴과 일치하는 단어 리스트
    """
    matches = []
    index = 0
    length = len(raw_string)
    
    matches = []
    index = 0
    length = len(raw_string)

    while index < length:
        for size in range(length - index, 0, -1):  # 긴 키워드부터 탐색
            substring = raw_string[index:index+size]
            if any(re.search(pattern, substring) for pattern in patterns):  # ✅ 단어 단위 비교
                matches.append(substring)
                index += size - 1  # ✅ 키워드 길이만큼 이동
                break
        index += 1  # 다음 문자로 이동

    return matches  # ✅ 찾은 키워드를 공백으로 결합하여 반환

    #while index < length:
    #    for pattern in patterns:
    #        for size in range(length - index, 0, -1):  # 긴 패턴부터 검사
    #            substring = raw_string[index:index+size]
    #            if re.match(pattern, substring):  # ✅ 정규식과 일치하는 경우
    #                matches.append(substring)
    #                index += size - 1  # ✅ 패턴 길이만큼 이동
    #                break
    #    index += 1  # 다음 문자로 이동
    #
    #return matches  # ✅ 정규식과 일치하는 모든 단어 리스트 반환


def extract_year_from_string(raw_string):
    """한 글자씩 이동하면서 출시 연도를 감지"""
    index = 0
    length = len(raw_string)
    detected_years = []

    while index < length - 3:  # 최소 4자리 연도 검사 가능하도록 설정
        substring = raw_string[index:index+4]
        if re.match(r"^20[2-3][0-9]$", substring):  # ✅ 2020~2029 범위 연도 감지
            detected_years.append(substring)
            index += 3  # ✅ 연도는 4자리이므로, 다음 탐색 인덱스 조정
        index += 1
#any(re.match(pattern, substring) for pattern in patterns)
    return list(dict.fromkeys(detected_years))  # ✅ 중복 제거 후 반환





def normalize_product_name(product_name):
    """띄어쓰기 없이 입력된 문자열에서 키워드를 찾아 정리"""
    product_name = convert_none_to_str(product_name)
    
    # ✅ 쉼표 및 `+` 제거
    product_name = product_name.replace(",", " ").replace("+", " ")
    
    # ✅ 공백 제거 후 분석 (띄어쓰기 없이 붙어 있는 경우 대비)
    product_name = re.sub(r"\s+", "", product_name)
    
    
    return product_name



def match_score(candidate, reference):
    """두 문자열의 유사도를 측정하는 함수 (0~1 범위)"""
    return SequenceMatcher(None, candidate, reference).ratio()

def extract_keywords_from_string(raw_string, keywords):
    """
    띄어쓰기 없이 입력된 문자열에서 키워드를 찾아 정리.
    - 키워드 집합을 단어 단위로 변환하여 탐색.
    """
    # ✅ 키워드를 단어 단위로 분리하여 `set`에 저장
    keyword_set = set()
    for key in keywords:
        keyword_set.update(key.split())  # ✅ 공백 기준으로 키를 나누어 `set`에 저장

    matches = []
    index = 0
    length = len(raw_string)

    while index < length:
        for size in range(length - index, 0, -1):  # 긴 키워드부터 탐색
            substring = raw_string[index:index+size]
            if substring in keyword_set:  # ✅ 단어 단위 비교
                matches.append(substring)
                index += size - 1  # ✅ 키워드 길이만큼 이동
                break
        index += 1  # 다음 문자로 이동

    return " ".join(matches)  # ✅ 찾은 키워드를 공백으로 결합하여 반환

class hashableSlitter(tuple):
    def split(self, sep=None):
        # 튜플의 모든 요소를 문자열로 변환하고 연결
        joined = ''.join(str(x) for x in self)
        # 문자열을 split하고 결과를 다시 SplitTuple로 변환
        return hashableSlitter(joined.split(sep))

def convert_none_to_str(item):
    """None이면 'None' 문자열로 변환, 아니면 그대로 반환"""
    return "None" if item is None else item
class ProductDatabasePickleFixed:
    def __init__(self, pickle_filename="product_database.pkl", csv_filename="product_database.csv"):
        self._save_lock = threading.Lock()
        self.pickle_filename = pickle_filename  # ✅ Pickle 저장 파일
        self.csv_filename = csv_filename  # ✅ 배포용 CSV 저장 파일
        self.current_id = 1  # ID 초기값
        self.products = {}  # ✅ 제품명 -> ID 매핑
        self.blacklist = set()  # ✅ 블랙리스트
        self.product_keywords = set()  # ✅ 제품 리스트
        self.company_tags = None
        self.load_company_tags()
        self.crawl_index = 1  # ✅ 크롤링 인덱스 초기값
        self.raw_data = {}  # ✅ ID -> 원본 이름 데이터 매핑
        self.regex_release_year = None
        self.regex_model_number = None
        self.regex_patterns = None
        self.load_regex_patterns()
        # ✅ Pickle 파일 로드 (없으면 기본값으로 생성)
        self.load_or_create_pickle()
         
        
    
    def load_regex_patterns(self, file_path="regex_patterns.txt", default_patterns=None):
        """
        txt 파일에서 정규식 패턴을 로드합니다.
        각 줄은 "키:패턴" 형식이어야 합니다.
        파일이 없으면 default_patterns(없으면 내부 기본값)을 사용하여 파일을 생성합니다.
        로드한 패턴은 re.compile 후 self.regex_patterns에 저장하고,
        'release_year'와 'model_number'는 각각 self.regex_release_year, self.regex_model_number에 할당합니다.
        """
        if default_patterns is None:
            default_patterns = {
                "release_year": r"^20[2-3][0-9]$",
                "model_number": r"^(S\d{1,2}|M\d{1,2}|\d+세대|\d{2,4}GB|\d{1,3}(?:\.\d+)?GHz|\d{1,2}A|폴드\d{1}|아이폰\d{1,2}|\d{1}TB)$"
            }
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                for key, pattern in default_patterns.items():
                    f.write(f"{key}:{pattern}\n")
            patterns = default_patterns
        else:
            patterns = {}
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and ":" in line:
                        key, pattern = line.split(":", 1)
                        patterns[key.strip()] = pattern.strip()
        self.regex_patterns = {}
        for key, pattern in patterns.items():
            try:
                self.regex_patterns[key] = re.compile(pattern)
            except re.error as e:
                print(f"Error compiling regex for '{key}': {pattern}. Error: {e}")
        # 특정 패턴을 별도 변수로 할당
        self.regex_release_year = self.regex_patterns.get("release_year", re.compile(r"^20[2-3][0-9]$"))
        self.regex_model_number = self.regex_patterns.get("model_number", re.compile(
            r"^(S\d{1,2}|M\d{1,2}|\d+세대|\d{2,4}GB|\d{1,3}(?:\.\d+)?GHz|\d{1,2}A|폴드\d{1}|아이폰\d{1,2}|\d{1}TB|패드\d{1,2}|\d{1,2}\.\d{1})$"
        ))

    def load_company_tags(self, file_path="company_tags.txt", default_tags=None):
        """
        txt 파일에서 회사 태그를 로드합니다.
        각 줄은 "키:값" 형식이어야 합니다.
        파일이 없으면 default_tags(없으면 내부 기본값)를 파일로 저장 후 사용합니다.
        로드한 태그는 self.company_tags에 할당합니다.
        """
        if default_tags is None:
            default_tags = {
                "삼성": "삼성",
                "애플": "APPLE",
                "엘지": "LG",
                "LG": "LG",
                "APPLE": "APPLE",
                "Samsung": "삼성"
            }
        with self._save_lock:
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    for key, value in default_tags.items():
                        f.write(f"{key}:{value}\n")
                tags = default_tags
            else:
                tags = {}
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and ":" in line:
                            key, value = line.split(":", 1)
                            tags[key.strip()] = value.strip()
        self.company_tags = tags
    
        
        
    def export_raw_data_to_csv(self, file_path):
        """경로(file_path)를 입력받아 self.raw_data를 CSV 파일로 저장하는 메서드.
        
        self.raw_data는 {product_id: [ { "index":..., "original_name":..., "name":... }, ... ], ... } 형태입니다.
        각 행에는 product_id, index, original_name, name 항목이 포함됩니다.
        """
        import csv
        with self._save_lock:
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["product_id", "index", "original_name", "name"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product_id, records in self.raw_data.items():
                    for record in records:
                        # 각 record는 딕셔너리입니다. 여기에 product_id를 추가하여 한 행(row)로 만듭니다.
                        row = {
                            "product_id": product_id,
                            "index": record.get("index", ""),
                            "original_name": record.get("original_name", ""),
                            "name": record.get("name", "")
                        }
                        writer.writerow(row)
        print(f"✅ CSV 파일 `{file_path}` 저장 완료!")
    def load_or_create_pickle(self):
        hardcoded_blacklist = {
            "Cellular", "해외구매", "중고", "C타입", "5G", "LTE", "키보드", "북커버", "케이스",
            "매직키보드", "폴리오케이스", "애플펜슬", "폴리오키보드", "폴리오케이스","폴리오키보드","자급제"
        }
            # ✅ 제품 리스트 기본값
        hardcoded_product_keywords = {
        "iPad", "갤럭시탭", "갤럭시Z","Surface", "G패드", "Yoga", "Xperia", "MatePad","갤럭시","울트라","플립","폴드"
        "냉장고", "세탁기", "TV", "오븐", "전자레인지", "에어컨", "공기청정기", "iPhone","아이폰","맥북","맥미니","맥북에어","맥북프로",
        "청소기", "스피커", "모니터", "M1", "M2", "M3", "M4", "M5", "mini", "Air","플러스","요가","레노버","Pad","AI","샤오미","미","패드","프로"
        }
        hardcoded_product = {
            "APPLE 2021 iPad Pro 11 3세대": 1,
            "APPLE 2021 iPad Pro 12.9 5세대": 2,
            "APPLE 2022 iPad Air 5세대": 3,
            "APPLE 2022 iPad Pro 11 4세대": 4,
            "APPLE 2022 iPad Pro 12.9 6세대": 5,
            "APPLE 2024 iPad Air 13 M2": 6,
            "APPLE 2024 iPad Air 13 M2 프로": 7,
            "APPLE 2024 iPad mini A17 Pro 7세대": 8,
            "APPLE 2024 iPad Pro 11 M4": 9,
            "APPLE 2024 iPad Pro 11 M4 프로": 10,
            "APPLE 2024 iPad Pro 13 M4": 11,
            "APPLE 2024 iPad Pro 13 M4 프로": 12,
            "레노버 요가 Pad Pro AI": 13,
            "삼성전자 갤럭시탭 S10 울트라": 14,
            "삼성전자 갤럭시탭 S10 플러스": 15,
            "삼성전자 갤럭시탭 S8": 16,
            "삼성전자 갤럭시탭 S8 울트라": 17,
            "삼성전자 갤럭시탭 S8 플러스": 18,
            "삼성전자 갤럭시탭 S9": 19,
            "삼성전자 갤럭시탭 S9 울트라": 20,
            "삼성전자 갤럭시탭 S9 플러스": 21,
            "샤오미 미 패드7": 22,
            "샤오미 미 패드7 프로": 23
                }

        """Pickle 파일에서 기존 데이터를 불러오거나, 없으면 기본값 생성"""

        if not os.path.exists(self.pickle_filename):
            self.blacklist = hardcoded_blacklist  # ✅ 블랙리스트에 하드코딩 값 추가
            print(f"⚠️ Pickle 파일 `{self.pickle_filename}`이 존재하지 않습니다. 새로 생성합니다.")
            self.product_keywords = hardcoded_product_keywords
            self.products = hardcoded_product
            self.current_id = 24 
            self.save_to_pickle()  # ✅ 기본값으로 파일 생성
        else:
            with open(self.pickle_filename, "rb") as f:
                data = pickle.load(f)
                self.products = data.get("products", {})
                self.blacklist = data.get("blacklist", set())
                self.product_keywords = data.get("product_keywords", set())
                if isinstance(self.products, set):
                    print("❌ 오류: products가 `set`으로 저장됨! 딕셔너리로 변환합니다.")
                    self.products = hardcoded_product  # ✅ 빈 딕셔너리로 초기화
                    self.current_id = 23
                self.current_id = max(self.products.values(), default=1) + 1  # ✅ ID 자동 증가

    def save_to_pickle(self):
        """현재 데이터를 Pickle 파일에 저장"""
        with self._save_lock:
            with open(self.pickle_filename, "wb") as f:
                pickle.dump({
                    "products": self.products,
                    "blacklist": self.blacklist,
                    "product_keywords": self.product_keywords
                }, f)
        print(f"✅ Pickle 파일 `{self.pickle_filename}` 저장 완료!")

    def detect_company(self, product_name):
        """제품명에서 회사 태그를 감지하여 자동 분류"""
        for tag, company in self.company_tags.items():
            if tag in product_name:
                return company
        return "기타"

    def export_original_name(self):
        out=[]
        for product_id, records in self.raw_data.items():
            for record in records:
                # 각 record는 딕셔너리입니다. 여기에 product_id를 추가하여 한 행(row)로 만듭니다.
                row = {
                    "product_id": product_id,
                    "index": record.get("index", ""),
                    "original_name": record.get("original_name", ""),
                    "name": record.get("name", "")
                }
                out.append(row)
        return out
    def filter_and_standardize(self, product_name):
        """불필요한 요소 제거 후, 가장 적합한 단어 순서로 정리하여 모델명을 생성"""
        original_name = convert_none_to_str(product_name)  # ✅ 원본 제품명 저장
        product_name = normalize_product_name(original_name)  # ✅ 공백 제거 후 정리
        for word in self.blacklist:
            product_name = product_name.replace(word, " ")
            product_name = re.sub(r"\s+", " ", product_name).strip()
        extracted_name = extract_keywords_from_string(product_name, self.products.keys())
        words = extracted_name.split()


        # ✅ 출시 연도 감지 (예: 2022, 2023, 2024 등)
        #year_match = extract_patterns_from_string(product_name, [r"^20[2-3][0-9]$"])
        year_match=re.match(self.regex_release_year,word)
        #[word for word in words if re.match(r"^20[2-3][0-9]$", word)]
        release_year = year_match[0] if year_match else ""

        # ✅ 모델 넘버 감지 (예: "11", "12.9", "S8", "M2", "M4", "6세대" 등)
        #model_numbers = extract_patterns_from_string(product_name, [r"^(S\d{1,2}|M\d{1,2}|\d+세대|\d{2,4}GB|\d{1,3}(\.\d+)?GHz|\d{1,2}A|\Ad{1,2}|폴드\d{1}|아이폰\d{1,2}|\d{1}TB)$"])
        model_numbers=extract_patterns_from_string(product_name,[self.regex_model_number])
        keyword_member = extract_set_from_string(product_name, self.product_keywords)
        #[word for word in words if re.match(r"^(\d+(\.\d+)?|S\d+|M\d+|\d+세대+Air)$", word)]
        # ✅ 하드코딩된 제품 리스트와 비교하여 겹치는 단어 찾기
        common_words_set = set()
        for model in self.products:
            common_words = set(words) & set(model.split())  # ✅ 제품명과 겹치는 단어 추출
            if common_words:
                common_words_set = common_words
                break  # ✅ 한 번이라도 겹치면 바로 사용
        # ✅ 등록되지 않은 문구도 추가로 반영
        # ✅ 제조사 감지 (리스트에 없으면 그대로 유지)
        detected_product = self.detect_company(original_name)
        # ✅ 가장 적합한 제품명 찾기
        total_word=[]
        total_word.append(detected_product)
        for i in common_words:
            total_word.append(i)
        for i in model_numbers:
            total_word.append(i)
        total_word.append(release_year)
        total_word.extend(keyword_member)
        unregistered_word=product_name
        for word in total_word:
            unregistered_word = unregistered_word.replace(word, " ")    
        unregistered_words =[word for word in unregistered_word.split() if len(word) >21] 
        total_word.extend(unregistered_words)
        total_word = ["삼성전자" if word == "삼성" else word for word in total_word]
        common_words_set = set(total_word)
        best_match = self.match_best_product(common_words_set,original_name)
        # ✅ 최종 모델명 생성 (제조사 + 정렬된 모델명 + 모델 넘버링 + 출시 연도)
        print(f" before join ✅ 된 제품명: {best_match}, 원본: {original_name}, Process Number: {self.current_id}")
        # ✅ 기존 제품명이 존재하면 그대로 사용, 없으면 새로운 조합 생성
        standardized_name = ' '.join(best_match).strip() if best_match else f"{' '.join(common_words_set)}".strip()

        print(f"✅ 된 제품명: {standardized_name}, 원본: {original_name}, Process Number: {self.current_id}")
        return original_name,standardized_name   # ✅ 원본, 정화된 제품명 함께 반환

    def add_product(self, product_name):
        """새로운 제품을 추가하면서 측정 인덱스 + 원본 제품 ID + 오염 모델명을 함께 저장"""
        original_name, standardized_product = self.filter_and_standardize(product_name)  # ✅ 원본 & 된 제품명
        
        # ✅ 기존 제품이면 기존 ID 유지 (하지만 original_name도 저장해야 함!)
        if standardized_product in self.products:
            assigned_id = self.products[standardized_product]
        else:
            # ✅ 새로운 제품이면 새로운 ID 할당
            assigned_id = self.current_id
            self.products[standardized_product] = assigned_id
            self.current_id += 1  # ✅ 새로운 제품이 추가될 때만 증가!

        # ✅ 원본 데이터 저장 (기존 제품이든 새로운 제품이든 저장!)
        if assigned_id not in self.raw_data:
            self.raw_data[assigned_id] = []  # ✅ ID별로 여러 원본명을 저장 가능하도록 리스트 형태로 변경

        self.raw_data[assigned_id].append({
            "index": self.crawl_index,
            "original_name": original_name,
            "name": standardized_product
        })
        self.crawl_index += 1
        # ✅ Pickle에 저장
        self.save_to_pickle()
    def match_best_product(self, sorted_product,original_order):
        """
        원본 제품명(`original_order`)의 단어 순서를 유지하면서 `sorted_product`의 단어들을 재배열.
        :param original_order: 원본 제품명 단어 리스트
        :param sorted_product: 정렬해야 할 단어 집합 (set)
        :return: 원본 순서대로 정렬된 단어 리스트
        """
        original_order = original_order.replace(" ", "")  # ✅ 공백 제거 후 하나의 문자열로 연결
        matched_words = []  # ✅ 매칭된 단어 저장
        remaining_string = original_order  # ✅ 탐색할 문자열 초기화
        match_found = False
        while remaining_string:  # ✅ 문자열이 남아있는 동안 반복
            for word in sorted_product:
                if not word:
                    continue
                if (word==remaining_string[0:len(word)]) and (word not in matched_words):  # ✅ 단어가 존재하면 반복적으로 제거
                    matched_words.append(word)  # ✅ 매칭된 단어 저장
                    remaining_string = remaining_string.replace(word, "", 1)
                    match_found = True
            if not match_found:
                remaining_string = remaining_string[1:]
            else:
                match_found = False        
        return matched_words
    def export_to_csv(self):
        """현재 데이터를 CSV 파일로 저장 (배포용)"""
        import pandas as pd
        df = pd.DataFrame(self.products.items(), columns=["Standardized_Product", "ID"])
        with self._save_lock:
            df.to_csv(self.csv_filename, index=False)
        print(f"✅ CSV 파일 `{self.csv_filename}` 저장 완료!")
    def add_to_blacklist(self, item):
        """블랙리스트에 단어 추가"""
        self.blacklist.add(item)
        self.save_to_pickle()

    def remove_from_blacklist(self, item):
        """블랙리스트에서 단어 제거"""
        if item in self.blacklist:
            self.blacklist.remove(item)
            self.save_to_pickle()

    def read_blacklist(self):
        """블랙리스트 조회"""
        return list(self.blacklist)

    def add_to_product_list(self, item):
        """제품군 리스트에 단어 추가"""
        self.product_keywords.add(item)
        self.save_to_pickle()

    def remove_from_product_list(self, item):
        """제품군 리스트에서 단어 제거"""
        if item in self.product_keywords:
            self.product_keywords.remove(item)
            self.save_to_pickle()

    def read_product_list(self):
        """제품군 리스트 조회"""
        return list(self.product_keywords)

class TapName:
    def __init__(self, driver):
        self.opinion = "productOpinion"
        self.companyReview = "companyReview"
        self.mcReview = "mcReview"
        self.front = "danawa-prodBlog-"
        self.mid = "-button-tab-"
        self.driver = driver
        self.review=[]
        self.average_star=None
        #review Parsing parm name
        self.second_selector = 'div.common_paginate'
        self.third_selector = 'div.nums_area'
    def getfirst(self):
        html = self.driver.page_source
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tab=WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.front+self.opinion+self.mid+self.companyReview)))
            tab.click()
        except:
            tab=WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.front+self.companyReview+self.mid+self.opinion)))
            tab.click()
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            tab=WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.front+self.opinion+self.mid+self.companyReview)))
            tab.click()
            
        result=self.extract_reviews_general(soup)
        self.get_avg_star()
        return result
    def get_avg_star(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        selector="#danawa-prodBlog-productOpinion-list-self > div.mall_review > div.area_left > div.grade_area > div.grd_stats > div.point_num > strong"
        elems = soup.select(selector)
        if elems:
            self.average_star = elems[0].get_text(strip=True)
        else:
            self.average_star = "no review"
        self.get_second()
    
    def get_second(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        result=self.extract_reviews_general(soup)
        return result
    def oneshot(self):
        out=[]
        out.append(self.getfirst())
        out.extend(self.get_second())
        return out
    def clean(self):
        self.driver.quit()
        return self.review
    def oneshot_iter(self):
        out=[]
        try:
            out.extend(self.oneshot())
        except:
            try:
                flag=True
                n=2
                while flag:
                    flag=self.click_opinion_page(n)
                    if flag:
                        out.extend(self.get_second())
                        n=n+1                   
            except:
                if out:
                    return out
                else:
                    return out.append(["no review"])
        try:
            flag=True
            n=2
            while flag:
                flag=self.click_opinion_page(n)
                if flag:
                    out.extend(self.get_second())
                    n=n+1                   
        except:
            if out:
                return out
            else:
                return out.append(["no review"])
        return out    

    def extract_reviews_general(self, soup, similarity_threshold=0.7):
        try:
            reviews = []
            candidate_selectors = [
                'p.danawa-prodBlog-productOpinion-list-self',
                ("div", {"id": "danawa-prodBlog-productOpinion-list-self"}),
                ('div', {"id": "danawa-prodBlog-companyReview-content-list"}),
            ]
            # 후보 셀렉터들로부터 리뷰 요소(filtered_elems) 수집
            for selector in candidate_selectors:
                if isinstance(selector, str):
                    elems = soup.select(selector)
                else:
                    elems = soup.find_all(*selector)
                if elems:
                    filtered_elems = []
                    for elem in elems:
                        parent_div = elem.find_all('li', class_="danawa-prodBlog-companyReview-clazz-more")
                        if parent_div:
                            filtered_elems.extend(parent_div)
                        else:
                            parent_div = elem.find_all(
                                'p',
                                class_="danawa-prodBlog-productOpinion-clazz-content",
                                attrs={"data-seq": "N"}
                            )
                            if parent_div:
                                for i in parent_div:
                                    if isinstance(i, str):
                                        filtered_elems.append(i.replace("\n", "").replace("\t", ""))
                                    else:
                                        filtered_elems.extend(i.text.replace("\n", "").replace("\t", ""))
                                filtered_elems.extend(parent_div)
            # 각 리뷰 요소에서 텍스트(및 별점) 추출
            for felem in filtered_elems:
                text_elements = felem.find_all('div', class_="atc")
                if self.average_star:
                    star = felem.find_all('span', class_="star_mask")
                    if text_elements:
                        for elem in text_elements:
                            if hasattr(elem, "get_text"):
                                cleaned=elem.get_text()
                            else:
                                cleaned = str(elem)
                                    #if hasattr(elem, "get_text"):
                                    #    cleaned = " ".join(set(elem.get_text(separator=' ', strip=True).split()))
                                    #else:
                                    #    cleaned = " ".join(set(str(elem).split()))
                            if cleaned:
                                # 별점이 있으면 리스트 형태로 추가
                                if star and len(star) > 0:
                                    reviews.append([cleaned, star[0].get_text(strip=True)])
                                else:
                                    reviews.append(cleaned)

            # 중복 제거 (Jaccard 유사도 기준)
            #unique_reviews = []
            #for review in reviews:
            #    is_duplicate = False
            #    for unique_review in unique_reviews:
            #        if jaccard_similarity(review, unique_review) > similarity_threshold:
            #            is_duplicate = True
            #            break
            #    if not is_duplicate:
            #        unique_reviews.append(review)
            return reviews
        except Exception as e:
            print("error", e)
            return reviews
    def click_opinion_page(self, page):
        try:
            # ✅ 첫 번째 선택자 검사 (수정됨: CSS Selector로 변경)
            first = self.driver.find_elements(By.CSS_SELECTOR, "#danawa-prodBlog-companyReview-content-list")
            if not first:
                return False

                
            # ✅ 두 번째 선택자 검사 (self.second_selector 사용)
            Spagr = self.driver.find_elements(By.CSS_SELECTOR, self.second_selector)
            if not Spagr:
                return False
            if page%10==1:
                try:
                    page_next_buttons = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.nav_edge_next.nav_edge_on"))
                    )
                    page_next_buttons.click()
                    return True
                except:
                    return False
             #✅ 세 번째 선택자 검사 (self.third_selector 사용)
            Tpagr = self.driver.find_elements(By.CSS_SELECTOR, self.third_selector)
            if not Tpagr:
                return False
            #if page%10==0:
                #try:
                #    page_last_buttons = WebDriverWait(self.driver, 10).until(
                #            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#danawa-prodBlog-companyReview-content-list > div > div > div > span"))
                #                )
                #    page_last_buttons[0].click()
                #    return True
                #except:
                #    return False
            # ✅ 페이지 버튼 찾기 (WebDriverWait 적용)
            page_buttons = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.page_num[data-pagenumber]"))
            )
            # ✅ 특정 페이지 번호 클릭 (문자열 변환 추가)
            for button in page_buttons:
                page_number = button.get_attribute("data-pagenumber")
                if str(page_number) == str(page):  # 🔹 비교 오류 해결
                    self.driver.execute_script("arguments[0].click();", button)
                    return True  # ✅ 클릭 성공 시 True 반환    
        except Exception as e:
            print(f"오류 발생: {e}")  # ✅ 디버깅을 위해 오류 출력
            return False  # 실패 시 False 반환
        return False  # 페이지 버튼이 없거나 클릭할 수 없을 경우 False
 
def review_loop (url,product_list,save_dir_image,trynum=5):
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")  # ✅ `/dev/shm` 부족 문제 해결
    options.add_argument("--remote-debugging-port=9222")  # ✅ 디버깅 활성화
    driver = webdriver.Chrome(service = Service(),options=options)
    

    
    # 크롤링할 페이지 URL (실제 URL로 변경)
    if len(url)<5:
        print("url")
        print ["no review"]
    num=0
    loopcon=True
    while loopcon:
        try:
            driver.get(url)
            loopcon=False
        except:
            print("fail")
            sleep(1)
            num=num+1
            if num>10:
                print ["can't read review page_driver"]
                return False
    product_list["product_link"] = []
    
    num=0
    loopcon=True
    while loopcon:
        try:
            html = driver.page_source
            loopcon=False
        except:
            print("fail")
            sleep(1)
            num=num+1
            if num>20:
                print ["can't read review page_html"]
                return False
    

      # Selenium에서 가져온 전체 HTML
    # 동적 콘텐츠 로드를 위해 충분한 시간 대기 (WebDriverWait 사용 권장)

    num=0
    loopcon=True
    while loopcon:
        try:
            WebDriverWait(driver, 3).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            loopcon=False
        except:
            print("fail")
            sleep(1)
            num=num+1
            if num>10:
                print ["can't read review page_driver_WebDriverWait1"]
                return False

    # 두 개의 의견/리뷰 탭 ID 목록 (필요한 경우 두 탭 모두 의견/리뷰 범주에 해당한다고 가정)
    desired_tab_ids = {
        "danawa-prodBlog-productOpinion-button-tab-productOpinion",
        "danawa-prodBlog-productOpinion-button-tab-companyReview"
    }
    num=0
    loopcon=True
    while loopcon:
        try:
            active_tab_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.tab_item"))
            )
            loopcon=False
        except:
            print("fail")
            sleep(1)
            num=num+1
            if num>10:
                print ["can't read review page"]
            break

    soup = BeautifulSoup(html, 'html.parser')
    try:
        affiliate_div = soup.select_one("#AffiliateMallListDiv")
        if affiliate_div:
            link_tags = affiliate_div.select("div > div.d_dsc > div.prc_line > a")
            for tag in link_tags:
                product_list["product_link"].append(tag.get("href"))
        openmarket_div = soup.select_one("#OpenMarketMallListDiv")
        if openmarket_div:
            link_tags = openmarket_div.select("div > div.d_dsc > div.prc_line > a")
            for tag in link_tags:
                product_list["product_link"].append(tag.get("href"))
    except:
        print("Error can't find product market link. skip this procedure")
    html=driver.page_source    
    soup = BeautifulSoup(html, 'html.parser')
    ##NEXT IMAGEFUN  save_dir_image
    image_tag = soup.select_one("#baseImage")
    if image_tag:
        image_src = image_tag.get('src')
        download_image(image_src, save_dir_image, product_list['name'])
        product_list['image'] = {
                'src': image_src,
                'saved_path': os.path.join(save_dir_image, product_list['name'])
                        }
    #driver.find_elements(By.CSS_SELECTOR, "#danawa-prodBlog-productOpinion-button-tab-productOpinion")
    for active_tab_element in active_tab_elements:
        classname = active_tab_element.get_attribute("class")
        if classname.endswith("on"):
            if not 'bookmark_cm_opinion_item'==active_tab_element.get_attribute("id"):
                        T=0
                        while T<trynum:
                            try:
                                product_opinion_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#bookmark_cm_opinion_item > a")))
                                driver.execute_script("arguments[0].click();", product_opinion_tab)
                                break
                            except:
                                T=T+1
                                print("retry")
                        if T==trynum:
                            print("fail")
                            return False
            else:
                break
    # 원하는 시작 노드를 지정한 후, 트리 구조를 출력합니다.
    html = driver.page_source  # Selenium에서 가져온 전체 HTML
    soup = BeautifulSoup(html, 'html.parser')
    try:
        reviews=TapName(driver)
        out=reviews.oneshot_iter()
        driver.quit()
        return out
    except:
        print("fail resource release")
        return reviews.clean()


def jaccard_similarity(text_1, text_2):
    """ 두 개의 문장 간 Jaccard Similarity 계산 """
    if isinstance(text_1, list):
        text1 = text_1[0]
    else:
        text1 = text_1
    if isinstance(text_2, list):
        text2 = text_2[0]
    else:
        text2 = text_2
    set1, set2 = set(text1.split()), set(text2.split())
    intersection = len(set1 & set2)  # 공통 단어 개수
    union = len(set1 | set2)  # 전체 단어 개수
    return intersection / union if union != 0 else 0

def click_page(page,driver,timeout=10):
    try:
        # ✅ 첫 번째 선택자 검사 (페이지 콘텐츠가 로딩되었는지 확인)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#productListArea"))
        )
        if page%10==1:
            try:
                next_page_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#productListArea div.prod_num_nav a.edge_nav.nav_next"))
                )
                next_page_button.click()
                return True
            except:
                try:
                    driver.execute_script("arguments[0].click();", next_page_button)
                    return True
                except:
                    return False
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.number_wrap"))
        )
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "div.number_wrap a.num")
        for button in page_buttons:
            page_number = button.text.strip()
            if str(page_number) == str(page):  # 🔹 비교 오류 해결
                driver.execute_script("arguments[0].click();", button)
                WebDriverWait(driver, timeout).until(EC.staleness_of(button))
                return True  # ✅ 클릭 성공 시 True 반환
        return False  # ✅ 페이지 버튼이 없거나 클릭할 수 없을 경우 False 
    except Exception as e:
        print(f"오류 발생: {e}")  # ✅ 디버깅을 위해 오류 출력
        return False  # 실패 시 False 반환



def get_data_from_url_single(url,num,save_dir_image,fail,limiter,reviewfactor,clean_item):
    index_i=0
    options = Options()
    
    options.add_argument('--headless')      
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service = Service(),options=options)
    product_list=[]
    try:
        # ✅ 페이지 이동
        driver.get(url)
        # ✅ 첫 번째 페이지 로딩 완료 대기
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
        # ✅ 페이지 이동 (num 페이지 클릭)
        if num != 1:
            count=click_page(num, driver)  
            if not count:
                fail+=1
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
        html = driver.page_source
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html, 'html.parser')
        # 제품 정보 컨테이너 찾기 (여러 상품이 있을 경우 반복문 사용)
        all_product_divs = soup.find_all('div', class_='prod_main_info')
        # 여러 상품 보를 담을 리스트
        debug=0
        for prod_info_div in all_product_divs:
            R=None
            with open('output/flag.txt', 'r') as f:
                R=f.readline()
            if (R.strip() != "1"):
                break  
            product_info = {}
            if prod_info_div:
                # 제품명 추출: <p class="prod_name"> 내부의 <a name="productName"> 태그
               
                prod_name_tag = prod_info_div.find('p', class_='prod_name')
                if prod_name_tag:
                    a_tag = prod_name_tag.find('a', attrs={"name": "productName"})
                    if a_tag:
                        product_info['name'] = a_tag.get_text(strip=True)
                prod_op_link_tag = prod_info_div.find('p', class_='prod_name')
                if prod_op_link_tag:
                    op_link_tag = prod_op_link_tag.find('a', attrs={"name": "productName"})
                    if a_tag:
                        product_info['name'] = op_link_tag.get_text(strip=True)
                        product_info['opinion'] = {} 
                        product_info['opinion']['link'] = op_link_tag.get('href')
                comment_div = prod_info_div.find('div', class_='meta_item mt_comment')
                if comment_div:
                    a_comment = comment_div.find('a')
                    if a_comment:
                        # 제품의견 관련 정보: 링크, 의견 수 등
                        product_info['opinion']['sub_link'] = a_comment.get('href')
                        strong_tag = a_comment.find('strong')
                        if strong_tag:
                            product_info['opinion']['count'] = strong_tag.get_text(strip=True)
                # 스펙 영역 추출: <div class="spec_list"> 내부의 모든 스펙 정보 추출
                spec_items = []
                spec_div = prod_info_div.find('div', class_='spec_list')
                if spec_div:
                    # <a class="view_dic"> 태그의 텍스트를 각각 추출
                    for a in spec_div.find_all('a', class_='view_dic'):
                        if a:
                            text = a.get_text(strip=True)
                            spec_items.append(text)
                ###NEXT IMAGEFUN  save_dir_image
                #image_tag = prod_info_div.find('img')
                #if image_tag:
                #    image_src = image_tag.get('src')
                #    download_image(image_src, save_dir_image, product_info['name'])
                #    product_info['image'] = {
                #            'src': image_src,
                #            'saved_path': os.path.join(save_dir_image, product_info['name'])
                #        }
                price_info=extract_prod_info_list(prod_info_div)
                #download_image(목표주소, save_dir_image, 이름)
                product_info['price'] = price_info
                # 추출한 스펙 배열을 제품 정보에 추가 (배열 그대로 저장하거나, join()으로 문자열 결합 가능)
                product_info['specs'] = spec_items
                print (f"debug print : {product_info['name']}")
                clean_item.add_product(product_info['name'])
                product_list.append(product_info)
            if reviewfactor:    
                if 'opinion' in product_list[index_i]:
                    try:
                        product_list[index_i]['opinion']["reviews"] =review_loop(product_list[index_i]['opinion']['link'],product_list[index_i],save_dir_image)
                        index_i+=1
                    except:
                        index_i+=1
                        product_list[index_i]['opinion']["reviews"] = ["no review"]
                        product_list[index_i]['product_link'] = ["no link"]
            debug+=1
            if debug>=limiter:
                break       
                        
        return product_list, fail
    except Exception as e:
        print(f"❌ 에러 발생 maim loop: {e}")
        if not product_list:
            product_list = ["get fail"]
        return product_list,fail
    finally:

        driver.quit()  # ✅ 예외 발생 시에도 브라우저를 안전하게 종료
def extract_prod_info_list(soup):
    """
    id가 "productInfoDetail_"로 시작하는 모든 <li> 요소 내부에서,
      - <p> 태그의 class를 키로, 그 내용을 값으로 하는 항목들을 추출하고,
      - 별도로 가격 정보(p.price_sect > a > strong)를 "price" 키에 저장한 딕셔너리를 만듭니다.
    각 <li> 별 딕셔너리를 리스트에 담아 반환합니다.
    """
    result_list = []
    
    # id가 "productInfoDetail_"로 시작하는 모든 <li> 요소 찾기
    li_elements = soup.select('li[id^="productInfoDetail_"]')
    
    for li in li_elements:
        product_dict = {}
        
        # li 내부의 모든 <p> 태그 순회
        p_tags = li.find_all('p')
        for p in p_tags:
            # p 태그에 class 속성이 없으면 건너뜁니다.
            p_classes = p.get("class")
            if not p_classes:
                continue
            
            # 가격 정보용 p 태그("price_sect")는 별도로 처리하므로 건너뜁니다.
            if "price_sect" in p_classes:
                continue
            
            # p 태그의 class 목록을 공백으로 합쳐 key로 사용
            key = " ".join(p_classes)
            # p 태그 내부의 텍스트(자식 태그 포함)를 value로 사용
            value = p.get_text(separator=" ", strip=True)
            
            product_dict[key] = value
        
        # 가격 정보 추출: li 내부의 'p.price_sect > a > strong'
        price_tag = li.select_one("p.price_sect a strong")
        if price_tag:
            product_dict["price"] = price_tag.get_text(strip=True)
        
        result_list.append(product_dict)
    
    return result_list
def download_image(image_url, save_dir, filename=None):
    """
    image_url: 다운로드할 이미지 URL (예: '//img.danawa.com/...' 형식)
    save_dir: 이미지를 저장할 폴더 경로
    filename: 저장할 파일명 (None이면 URL에서 추출)
    """
    # URL이 프로토콜 없이 // 로 시작하면 https: 추가
    if image_url.startswith('//'):
        image_url = 'https:' + image_url
    
    # 저장 폴더가 없으면 생성
    os.makedirs(save_dir, exist_ok=True)
    
    # filename이 지정되지 않으면 URL에서 파일명 추출 (쿼리스트링 제거)
    if not filename:
        filename = os.path.basename(image_url.split('?')[0])
    save_path = os.path.join(save_dir, filename)
    
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # 상태 코드 체크
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"다운로드 성공: {image_url} -> {save_path}")
    except Exception as e:
        print(f"이미지 다운로드 실패: {image_url} 에러: {e}")

def extract_name(manager, fname="output/danawa.csv"):
    out = []
    
    # ProductListManager의 경우 전체 데이터를 가져오기
    data = manager.get_all_data() if hasattr(manager, 'get_all_data') else manager
    
    for d in data:
        if not (d[0] == 'get fail'):
            for i in d:
                if isinstance(i, bytes):
                    try:
                        R = ast.literal_eval(i.decode("utf-8"))
                        out.append(R["name"])
                    except Exception as e:
                        print(f"Error processing item: {e}")
                        continue

    out = pd.DataFrame(out)
    out.to_csv(fname)
    return out

def get_data_from_url_loop(url,start,end,clean_item,product_lists,save_dir_image,limiter,reviewfactor):
    print(clean_item.blacklist)
    futures=range(start,end+1)
    fail=0
    for future in tqdm.tqdm(futures, total=end - start + 1):
        page = future
        try:
            data,fail=get_data_from_url_single(url,page,save_dir_image,fail,limiter,reviewfactor,clean_item) 
            product_lists.append(data)
            R=None
            with open('output/flag.txt', 'r') as f:
                R=f.readline()
            if (R.strip() != "1"):
                break  
            if (fail>3): 
                break
        except Exception as e:
            data = ["get fail"] 
            product_lists.append(data)
    return product_lists

def detect_company(name):
    """제품명에서 제조사 감지 (간단히 '삼성' 또는 '애플/APPLE' 포함 여부로 분류)"""
    if "삼성" in name:
        return "삼성"
    elif "애플" in name or "APPLE" in name:
        return "APPLE"
    else:
        return ""

def flatten_reviews(reviews):
    """
    리뷰 항목이 중첩 리스트일 경우 평탄화하여 문자열 리스트로 반환  
    (의견 테이블에 저장할 때 사용)
    """
    flat = []
    if isinstance(reviews, list):
        for item in reviews:
            flat.extend(flatten_reviews(item))
    else:
        flat.append(reviews)
    return flat

def split_by_product(csv_dir):
    """
    CSV 파일들을 제품별로 분리하여 저장합니다.
    """
    file_types = ['opinions_table.csv', 'product_links.csv']
    
    for file_type in file_types:
        input_path = os.path.join(csv_dir, file_type)
        if not os.path.exists(input_path):
            continue
            
        # CSV 파일 읽기
        rows_by_product = {}
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_name = row['상품명']
                if cleaned_name not in rows_by_product:
                    rows_by_product[cleaned_name] = []
                rows_by_product[cleaned_name].append(row)
        
        # 제품별로 분리하여 저장
        output_dir = os.path.join(csv_dir, f'split_{file_type.split(".")[0]}')
        os.makedirs(output_dir, exist_ok=True)
        
        for product_name, product_rows in rows_by_product.items():
            # 파일명에 사용할 수 없는 문자 제거
            safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name[:100]  # 파일명 길이 제한
            
            output_path = os.path.join(output_dir, f'{safe_name}.csv')
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if product_rows:
                    writer = csv.DictWriter(f, fieldnames=product_rows[0].keys())
                    writer.writeheader()
                    writer.writerows(product_rows)
def export_custom_csv(pickle_file, output_dir, name_mappings):
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
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)
        
    # name_mappings를 딕셔너리로 변환 (된 이름 -> 원본 이름)
    name_map = {item["name"]: item["original_name"] for item in name_mappings}
    
    # 각 CSV에 저장할 행 리스트 초기화
    product_rows = []   # product_table.csv용
    specs_rows = []     # specs_table.csv용
    opinions_rows = []  # opinions_table.csv용
    links_rows = []     # product_links.csv용

    # data는 여러 페이지의 제품 리스트
    all_products = []
    for page in data:
        all_products.extend(page)
    
    # 제품별 최대 가격 개수 확인
    max_price_count = max(len(product.get("price", [])) for product in all_products)
    price_columns = [f"가격{i+1}" for i in range(max_price_count)]
    
    # 각 제품별로 처리
    for product in all_products:
        cleaned_name = product.get("name", "")
        original_name = name_map.get(cleaned_name, cleaned_name)  # 매핑된 원본 이름 또는 된 이름
        
        # 1. product_table.csv용 데이터 생성
        price_list = product.get("price", [])
        prices_formatted = [
            f"{p.get('price', '')} ({p.get('memory_sect', '')})"
            for p in price_list
        ]
        prices_formatted.extend([""] * (max_price_count - len(prices_formatted)))
        
        image_src = product.get("image", {}).get("src", "")
        manufacturer = detect_company(cleaned_name)
        
        # 평균별점 계산
        opinion_data = product.get("opinion", {})
        reviews = opinion_data.get("reviews", [])
        stars = []
        for review in reviews:
            if isinstance(review, list) and len(review) == 2:
                star_str = review[1]
                nums = re.findall(r'\d+\.?\d*', star_str)
                if nums:
                    try:
                        stars.append(float(nums[0]))
                    except:
                        pass
        
        average_star = round(sum(stars) / len(stars), 2) if stars else ""
        
        prod_row = {
            "원본상품명": original_name,
            "상품명": cleaned_name
        }
        for idx, col in enumerate(price_columns):
            prod_row[col] = prices_formatted[idx]
        prod_row.update({
            "이미지src": image_src,
            "제조사": manufacturer,
            "평균별점": average_star
        })
        product_rows.append(prod_row)
        
        # 2. specs_table.csv용 데이터 생성
        specs = product.get("specs", [])
        spec_row = {
            "원본상품명": original_name,
            "상품명": cleaned_name
        }
        for i, spec in enumerate(specs, start=1):
            spec_row[f"스펙{i}"] = spec
        specs_rows.append(spec_row)
        
        # 3. opinions_table.csv용 데이터 생성
        for review in reviews:
            if isinstance(review, list) and len(review) == 2:
                opinions_rows.append({
                    "원본상품명": original_name,
                    "상품명": cleaned_name,
                    "의견": review[0],
                    "star": review[1]
                })
            elif isinstance(review, str):
                opinions_rows.append({
                    "원본상품명": original_name,
                    "상품명": cleaned_name,
                    "의견": review,
                    "star": ""
                })
        
        # 4. product_links.csv용 데이터 생성
        links = product.get("product_link", [])
        for link in links:
            links_rows.append({
                "원본상품명": original_name,
                "상품명": cleaned_name,
                "구매링크": link
            })
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일들 저장
    save_csv(os.path.join(output_dir, "product_table.csv"), product_rows,
             ["원본상품명", "상품명"] + price_columns + ["이미지src", "제조사", "평균별점"])
    
    max_spec_count = max(
        (sum(1 for key in row if key.startswith("스펙")) for row in specs_rows),
        default=0
    )
    save_csv(os.path.join(output_dir, "specs_table.csv"), specs_rows,
             ["원본상품명", "상품명"] + [f"스펙{i}" for i in range(1, max_spec_count+1)])
    
    save_csv(os.path.join(output_dir, "opinions_table.csv"), opinions_rows,
             ["원본상품명", "상품명", "의견", "star"])
             
    save_csv(os.path.join(output_dir, "product_links.csv"), links_rows,
             ["원본상품명", "상품명", "구매링크"])
    
    # 모든 파일들을 제품별로 분리하여 저장
    split_by_product(output_dir)
    
    print(f"CSV 파일들이 저장되었습니다: {output_dir}")

def save_csv(filepath, rows, fieldnames):
    """CSV 파일 저장을 위한 헬퍼 함수"""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # 빈 필드 처리
            for field in fieldnames:
                if field not in row:
                    row[field] = ""
            writer.writerow(row)




def split_csv_by_product(input_path, output_dir, file_type='opinions', encoding='utf-8'):
    """
    opinions_table.csv 또는 product_links.csv를 상품별로 분할하여 저장합니다.
    
    Args:
        input_path: CSV 파일 경로 또는 pickle 파일 경로
        output_dir: 분할된 파일들을 저장할 디렉토리
        file_type: 'opinions' 또는 'links'
        encoding: CSV 파일 인코딩
    """
    # 출력 디렉토리 생성
    split_dir = os.path.join(output_dir, f'split_{file_type}')
    os.makedirs(split_dir, exist_ok=True)
    
    # 데이터 로드
    data = []
    if input_path.endswith('.pkl'):
        with open(input_path, 'rb') as f:
            pickle_data = pickle.load(f)
            # pickle 데이터를 적절한 형식으로 변환
            if file_type == 'opinions':
                for page in pickle_data:
                    for product in page:
                        original_name = product.get("original_name", "")
                        cleaned_name = product.get("name", "")
                        reviews = product.get("opinion", {}).get("reviews", [])
                        for review in reviews:
                            if isinstance(review, list) and len(review) == 2:
                                data.append({
                                    "원본상품명": original_name,
                                    "상품명": cleaned_name,
                                    "의견": review[0],
                                    "star": review[1]
                                })
                            elif isinstance(review, str):
                                data.append({
                                    "원본상품명": original_name,
                                    "상품명": cleaned_name,
                                    "의견": review,
                                    "star": ""
                                })
            else:  # links
                for page in pickle_data:
                    for product in page:
                        original_name = product.get("original_name", "")
                        cleaned_name = product.get("name", "")
                        links = product.get("product_link", [])
                        for link in links:
                            data.append({
                                "원본상품명": original_name,
                                "상품명": cleaned_name,
                                "구매링크": link
                            })
    else:  # CSV 파일
        with open(input_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            data = list(reader)
    
    # 상품별로 데이터 그룹화
    products = {}
    for row in data:
        key = row['상품명']  # 된 이름으로 그룹화
        if key not in products:
            products[key] = []
        products[key].append(row)
    
    # 상품별로 파일 저장
    for product_name, product_data in products.items():
        # 파일명에 사용할 수 없는 문자 제거
        safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name[:100]  # 파일명 길이 제한
        
        output_path = os.path.join(split_dir, f'{safe_name}_{file_type}.csv')
        
        # 필드 이름 결정
        fieldnames = ['원본상품명', '상품명']
        if file_type == 'opinions':
            fieldnames.extend(['의견', 'star'])
        else:
            fieldnames.append('구매링크')
        
        # CSV 파일로 저장
        with open(output_path, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(product_data)
    
    return split_dir

def split_all_by_product(input_source, output_dir):
    """
    opinions와 links 데이터를 모두 상품별로 분할하여 저장합니다.
    
    Args:
        input_source: pickle 파일 경로 또는 CSV 파일들이 있는 디렉토리
        output_dir: 분할된 파일들을 저장할 디렉토리
    """
    if input_source.endswith('.pkl'):
        # pickle 파일에서 직접 분할
        split_csv_by_product(input_source, output_dir, 'opinions')
        split_csv_by_product(input_source, output_dir, 'links')
    else:
        # CSV 파일들에서 분할
        opinions_path = os.path.join(input_source, 'opinions_table.csv')
        links_path = os.path.join(input_source, 'product_links.csv')
        
        if os.path.exists(opinions_path):
            split_csv_by_product(opinions_path, output_dir, 'opinions')
        if os.path.exists(links_path):
            split_csv_by_product(links_path, output_dir, 'links')
    
    print(f"파일 분할이 완료되었습니다. 저장 위치: {output_dir}")


def run(clean_item,url="https://prod.danawa.com/list/?cate=22254632",start=1,end=11,output="output"
        ,limiter=100,reviewfactor_in=1):

    limiter=limiter
    
    if (reviewfactor_in == 1): 
        reviewfactor= True
    else: 
        reviewfactor= False
    print(f"reviewfactor: {reviewfactor}")
    # 리눅스에서는 '/'와 null 문자가 문제되지만, '/'는 반드시 치환해야 합니다.
    # 여기에 Windows에서 문제가 될 수 있는 문자들도 함께 치환하면 호환성이 높아집니다.
    safe_url = re.sub(r'[\\/:*?"<>|]', '_', url)
    hashed_filename = hashlib.sha256(url.encode("utf-8")).hexdigest()
    csvname=hashed_filename+".csv"
    # 안전한 경로 생성
    csv_path = f"{output}/csv"
    pickle_path = f"{output}/pickle"
    image_path = f"{output}/images"
    save_dir_image = Path(image_path) / safe_url
    save_dir_image.mkdir(parents=True, exist_ok=True)
    csv_dir = Path(csv_path)
    pickle_dir = Path(pickle_path)
    pickle_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_filename=csv_path+"/"+csvname
    csv_filpath=Path(csv_filename)
    csv_filpath.touch(exist_ok=True)  
    file_path = Path('output/flag.txt')
    file_path.touch()
    
    print(f"이미지 저장 경로: {save_dir_image}")
    print(f"현재 워킹 디렉토리: {os.getcwd()}")

    csv_raw_filename=csv_path+"/"+hashed_filename+"_raw.csv"
    pickle_filename=pickle_path+"/"+hashed_filename+".pickle"
    pickle_output=pickle_path+"/"+hashed_filename+"_output"+".pickle"


    with open('output/flag.txt', 'w') as f:
        f.write("1")
    
    
    product_list=ProductListManager()

    
    data =get_data_from_url_loop(url,start,end,clean_item,product_list,save_dir_image,limiter,reviewfactor)
    clean_item.export_to_csv()
    clean_item.export_raw_data_to_csv(csv_raw_filename)
    extract_name(data)
    data.merge_and_save(pickle_output) 

    export_custom_csv(pickle_output, csv_path,clean_item.export_original_name())
    return True
 
if __name__ == "__main__":
    run()