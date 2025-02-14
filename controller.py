import threading
import pandas as pd
import os
from danawa import ProductDatabasePickleFixed, run
import hashlib
#from datetime import datetime
import re
import YTE as yt   
from pathlib import Path
import time
class YTcontroller:
    def __init__(self,save_base="output/youtube"):
        self.status = "Idle"
        self.save_base = save_base
        self.thread = None
        self.nowrun=None
        self.base_dir = os.getcwd()
        self.flag_file_path = Path(self.base_dir+"/"+self.save_base)
        print (f"플래그 경로 IN control{self.flag_file_path}")
        self.flag_file_path.mkdir(parents=True, exist_ok=True)
        self.flag_file_path = Path( str(self.flag_file_path)  +"/flag.txt")
        with open("YTref.txt", "r", encoding="utf-8") as file:
            names = [line.strip() for line in file if line.strip()]
        self.search_querys = names
    def is_youtube_running(self):
        if self.status == "Running":
            return True
        else:
            return False

    def is_thread_running(self):
        """ ✅ 현재 스레드가 실행 중인지 확인 """
        return self.thread is not None and self.thread.is_alive()
    
    def run_threaded_youtube(self):
        """ ✅ 멀티스레드로 크롤링 실행 """
        if self.thread and self.thread.is_alive():
            print("⚠️ 이미 실행 중입니다. 새 작업을 시작할 수 없습니다.")
            return False  # 이미 실행 중이면 실행하지 않음
        self.thread = threading.Thread(target=self.run_youtube)
        self.thread.start()
        print(f"✅ 크롤링 스레드 시작")
        return True
    def stop_threaded_danawa(self):
        """ ✅ 멀티스레드 크롤링 중지 요청 (flag.txt 변경) """
        with open(self.flag_file_path, "w") as f:
            f.write("0")
    
    def run_youtube(self):
        self.status = "Running"
        for search_query in self.search_querys:
            print(f"✅ 크롤링 유튜버 : {search_query}")
            yt.run(search_query, self.save_base,self.base_dir)
            with open(self.flag_file_path, "r") as f:
                flag = f.read().strip()
            if flag != "1":
                print("⛔ 크롤링 중지 요청됨")
                self.status = "Idle"
                return True
        self.status = "Idle"
        return True
    


        
class Danawacontroller:
    def __init__(self, url, start, end, output, limiter, reviewfactor):
        self.thread = None
        self.crawling_status = None
        self.url = url
        self.start = start
        self.end = end
        self.output = output
        self.csv_path = f"{output}/csv"
        self.pickle_path = f"{output}/pickle"
        safe_url = re.sub(r'[\\/:*?"<>|]', '_', url)
        image_path = f"{output}/images"
        save_dir_image = Path(image_path) / safe_url
        save_dir_image.mkdir(parents=True, exist_ok=True)
        self.image_path = save_dir_image
        self.hashed_filename = hashlib.sha256(url.encode("utf-8")).hexdigest()
        csvname = self.hashed_filename + ".csv"
        pickle_dir = Path(self.pickle_path)
        csv_dir = Path(self.csv_path)
        pickle_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(parents=True, exist_ok=True)
        self.csv_filename = os.path.join(self.csv_path, csvname)
        self.pickle_filename = os.path.join(self.pickle_path, self.hashed_filename + ".pickle")
        self.csv_raw_filename=self.csv_path+"/"+self.hashed_filename+"_raw.csv"
        self.pickle_filename=self.pickle_path+"/"+self.hashed_filename+".pickle"
        self.pickle_output=self.pickle_path+"/"+self.hashed_filename+"_output"+".pickle"
        self.limiter = limiter
        self.reviewfactor = reviewfactor
        defualt=Path("output")
        defualt.mkdir(parents=True, exist_ok=True)
        self.flagpath = "output/flag.txt"  
        csv_filename = os.path.join(self.csv_path, csvname)
        pickle_filename = os.path.join(self.pickle_path, self.hashed_filename + ".pickle")
        self.clean_item = ProductDatabasePickleFixed(
            pickle_filename=pickle_filename, 
            csv_filename=csv_filename
        )

    def run_danawa(self):
        result=run(self.clean_item,self.url,start=self.start,end=self.end,output=self.output,limiter=self.limiter,reviewfactor_in=self.reviewfactor)
        return result
    def run_threaded_danawa(self):
        """ ✅ 멀티스레드로 크롤링 실행 """
        if self.thread and self.thread.is_alive():
            print("⚠️ 이미 실행 중입니다. 새 작업을 시작할 수 없습니다.")
            self.crawling_status = "⚠️ 이미 실행 중입니다. 새 작업을 시작할 수 없습니다."
            return False  # 이미 실행 중이면 실행하지 않음
        self.thread = threading.Thread(target=self.run_danawa)
        self.thread.start()
        print(f"✅ 크롤링 스레드 시작: {self.url}")
        self.crawling_status = f"✅ 크롤링 스레드 시작: {self.url}"
        return True
    def stop_threaded_danawa(self):
        """ ✅ 멀티스레드 크롤링 중지 요청 (flag.txt 변경) """
        with open(self.flagpath, "w") as f:
            f.write("0")

        print("⛔ 크롤링 중지 요청됨")
        self.crawling_status = "⛔ 중지 요청됨"
        return True

    def is_thread_running(self):
        """ ✅ 현재 스레드가 실행 중인지 확인 """
        return self.thread is not None and self.thread.is_alive()

    def wait_for_completion(self, check_interval=2):
        """ ✅ 크롤링이 정상 종료될 때까지 대기 """
        print("⌛ 크롤링 종료 대기 중...")
        while self.is_thread_running():
            time.sleep(check_interval)  # 일정 간격으로 확인
        print("✅ 크롤링이 정상적으로 종료됨.")
        return True
    def add_product(self,new_product):
        self.clean_item.add_product(new_product)
        return self.clean_item.products
    def add_to_blacklist(self,new_blacklist):
        self.clean_item.add_to_blacklist(new_blacklist)
        return self.clean_item.blacklist

    def remove_from_blacklist(self,selected_blacklist):
        self.clean_item.remove_from_blacklist(selected_blacklist)
        return self.clean_item.blacklist

    def add_to_product_list(self,new_keyword):
        self.clean_item.add_to_product_list(new_keyword)
        return self.clean_item.product_keywords

    def remove_from_product_list(self,selected_keyword):
        self.clean_item.remove_from_product_list(selected_keyword)
        return self.clean_item.product_keywords
    def split_pattern(pattern):
        pattern = pattern.strip('^$()')
        return pattern.split('|')
    def add_pattern(self,pattern_type,new_pattern):
        patterns = {
            "release_year": self.clean_item.regex_release_year.pattern,
            "model_number": self.clean_item.regex_model_number.pattern
        }
        current_patterns = (self.split_pattern(patterns["release_year"]) if pattern_type == "출시연도"
                            else self.split_pattern(patterns["model_number"]))
        if new_pattern not in current_patterns:
            current_patterns.append(new_pattern)
            if pattern_type == "출시연도":
                patterns["release_year"] = "^(" + "|".join(current_patterns) + ")$"
            else:
                patterns["model_number"] = "^(" + "|".join(current_patterns) + ")$"
            with open("regex_patterns.txt", "w", encoding="utf-8") as f:
                for key, pattern in patterns.items():
                    f.write(f"{key}:{pattern}\n")
            self.clean_item.load_regex_patterns()
            return self.clean_item.regex_release_year.pattern,self.clean_item.regex_model_number.pattern
    def remove_pattern(self,pattern_type,pattern_to_remove):
        patterns = {
            "release_year": self.clean_item.regex_release_year.pattern,
            "model_number": self.clean_item.regex_model_number.pattern
        }
        current_patterns = (self.split_pattern(patterns["release_year"]) if pattern_type == "출시연도"
                            else self.split_pattern(patterns["model_number"]))
        current_patterns.remove(pattern_to_remove)
        if pattern_type == "출시연도":
            patterns["release_year"] = "^(" + "|".join(current_patterns) + ")$"
        else:
            patterns["model_number"] = "^(" + "|".join(current_patterns) + ")$"
        with open("regex_patterns.txt", "w", encoding="utf-8") as f:
            for key, pattern in patterns.items():
                f.write(f"{key}:{pattern}\n")
        self.clean_item.load_regex_patterns()
        return self.clean_item.regex_release_year.pattern,self.clean_item.regex_model_number.pattern

    def get_products(self):
        products_df = pd.DataFrame(list(self.clean_item.products.items()),columns=['제품명', 'ID'])
        return products_df

   
   


class CrawlerStateManager:
    def __init__(self):
        self.danawa_state = "IDLE"  # 상태: "IDLE" 또는 "RUNNING"
        self.youtube_state = "IDLE"
        self.rerun_state = 1

    def start_danawa(self):
        """ 다나와 크롤링 시작 시 상태 변경 """
        self.danawa_state = "RUNNING"

    def stop_danawa(self, controller):
        """ 다나와 크롤링 종료 요청 후 실제 종료되었는지 확인 """
        controller.stop_threaded_danawa()
        while controller.is_thread_running():  # ✅ 실제 크롤링이 중지될 때까지 대기
            time.sleep(0.5)
        self.danawa_state = "IDLE"  # ✅ 중지 확인 후 상태 변경

    def start_youtube(self):
        """ 유튜브 크롤링 시작 시 상태 변경 """
        self.youtube_state = "RUNNING"

    def stop_youtube(self, controller):
        """ 유튜브 크롤링 종료 요청 후 실제 종료되었는지 확인 """
        controller.stop_threaded_danawa()
        while controller.is_youtube_running():  # ✅ 실제 크롤링이 중지될 때까지 대기
            time.sleep(0.5)
        self.youtube_state = "IDLE"  # ✅ 중지 확인 후 상태 변경

    def is_danawa_running(self):
        return self.danawa_state == "RUNNING"

    def is_youtube_running(self):
        return self.youtube_state == "RUNNING"
