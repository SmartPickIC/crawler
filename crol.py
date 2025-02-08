import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tqdm
from itertools import combinations
import pandas as pd
import h5py
import json
from queue import Queue

class RecursiveDOMExplorer:
    def __init__(self, root_node):
        """
        :param root_node: 재귀 탐색의 시작 노드 (BeautifulSoup Tag)
        """
        self.root = root_node

    def traverse(self, node=None, depth=0):
        """
        지정한 노드부터 시작하여 자식 노드를 재귀적으로 탐색합니다.
        각 노드의 태그 이름과 속성, 텍스트(있는 경우)를 들여쓰기로 출력합니다.
        :param node: 탐색할 현재 노드 (없으면 self.root 사용)
        :param depth: 들여쓰기 깊이 (재귀 호출시 사용)
        """
        if node is None:
            node = self.root

        indent = " " * (depth * 2)  # depth에 따라 들여쓰기

        # Tag 객체인 경우 (예: <div>, <p> 등)
        if hasattr(node, 'name') and node.name is not None:
            # 노드 이름과 속성 출력
            print(f"{indent}Tag: {node.name}  Attributes: {node.attrs}")
        else:
            # NavigableString 등의 경우, 텍스트만 출력 (빈 문자열은 건너뜀)
            text = str(node).strip()
            if text:
                print(f"{indent}Text: {text}")

        # 현재 노드의 자식들(contents)을 순회하면서 재귀적으로 탐색
        if hasattr(node, 'contents'):
            for child in node.contents:
                self.traverse(child, depth + 1)
def jaccard_similarity(text1, text2):
    """ 두 개의 문장 간 Jaccard Similarity 계산 """
    set1, set2 = set(text1.split()), set(text2.split())
    intersection = len(set1 & set2)  # 공통 단어 개수
    union = len(set1 | set2)  # 전체 단어 개수
    return intersection / union if union != 0 else 0
class TapName:
    def __init__(self, driver):
        self.opinion = "productOpinion"
        self.companyReview = "companyReview"
        self.mcReview = "mcReview"
        self.front = "danawa-prodBlog-"
        self.mid = "-button-tab-"
        self.driver = driver
        self.review=[]
        #review Parsing parm name
        self.second_selector = 'div.common_paginate'
        self.third_selector = 'div.nums_area'
    def getfirst(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        tab=WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.front+self.opinion+self.mid+self.companyReview)))
        tab.click()
        result=self.extract_reviews_general(soup)
        return result
    def get_second(self):
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        result=self.extract_reviews_general(soup)
        return result
    def oneshot(self):
        self.review.append(self.getfirst())
        self.review.extend(self.get_second())
        return self.review
    def clean(self):
        self.driver.quit()
        return self.review
    def oneshot_iter(self):
        out=[]
        try:
            out.extend(self.oneshot())
        except:
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            tab=WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, self.front+self.opinion+self.mid+self.companyReview)))
            tab.click()
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
                return False
        return out    
    @staticmethod 
    def extract_reviews_general(soup, similarity_threshold=0.7):
        reviews = []
        candidate_selectors = [
            'p.danawa-prodBlog-productOpinion-list-self',
            ("div",{"id":"danawa-prodBlog-productOpinion-list-self"}),
            ('div', {"id": "danawa-prodBlog-companyReview-content-list"}),
        ]     
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
                        parent_div = elem.find_all('p', class_="danawa-prodBlog-productOpinion-clazz-content", attrs={"data-seq": "N"})
                        if parent_div:  
                            filtered_elems.extend(parent_div)
        for felem in filtered_elems:
            text=felem.find_all('div', class_="atc")
            if text:
                for i in text:
                    text=" ".join(set(i.get_text(separator=' ', strip=True).split()))
                    if text:
                        reviews.append(text)
            else:
                text=" ".join(set(felem.get_text(separator=' ', strip=True).split()))
                if text:
                    reviews.append(text)
        # ✅ **유사도 필터링 (Jaccard Similarity 이용)**
        unique_reviews = []
        for i, review in enumerate(reviews):
            is_duplicate = False
            for unique_review in unique_reviews:
                if jaccard_similarity(review, unique_review) > similarity_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_reviews.append(review)
        return unique_reviews
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
            # ✅ 세 번째 선택자 검사 (self.third_selector 사용)
            Tpagr = self.driver.find_elements(By.CSS_SELECTOR, self.third_selector)
            if not Tpagr:
                return False
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
 
def detail (url,trynum=5):
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service = Service(),options=options)
    # 크롤링할 페이지 URL (실제 URL로 변경)
    driver.get("https://prod.danawa.com/"+url)
    # 동적 콘텐츠 로드를 위해 충분한 시간 대기 (WebDriverWait 사용 권장)
    WebDriverWait(driver, 5).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    # 두 개의 의견/리뷰 탭 ID 목록 (필요한 경우 두 탭 모두 의견/리뷰 범주에 해당한다고 가정)
    desired_tab_ids = {
        "danawa-prodBlog-productOpinion-button-tab-productOpinion",
        "danawa-prodBlog-productOpinion-button-tab-companyReview"
    }
    # 현재 활성 탭의 <a> 태그 선택 (상위 탭 영역에서 활성 탭은 li 요소에 "on" 클래스가 붙어 있습니다)
    active_tab_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.tab_item"))
    )
    #driver.find_elements(By.CSS_SELECTOR, "#danawa-prodBlog-productOpinion-button-tab-productOpinion")

    for active_tab_element in active_tab_elements:
        classname = active_tab_element.get_attribute("class")
        if classname.endswith("on"):
            if not 'bookmark_cm_opinion_item'==active_tab_element.get_attribute("id"):
                        T=0
                        while T<trynum:
                            try:
                                product_opinion_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#danawa-prodBlog-productOpinion-button-tab-productOpinion")))
                                product_opinion_tab.click(),
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
def click_page(page,driver,timeout=10):
    try:
        # ✅ 첫 번째 선택자 검사 (페이지 콘텐츠가 로딩되었는지 확인)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#productListArea"))
        )
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
    except Exception as e:
        print(f"오류 발생: {e}")  # ✅ 디버깅을 위해 오류 출력
        return False  # 실패 시 False 반환
def get_data_from_url_multi_thread(url,start,end,num_threads=8):
    product_lists = {}
    task_queue = Queue()

    # ✅ 크롤링할 페이지를 큐에 삽입
    for page in range(start, end + 1):
        task_queue.put(page)

    
    with concurrent.futures.ThreadPoolExecutor(num_threads) as executor:
        futures = {}

        # ✅ 초기 스레드 실행 (최대 `num_threads` 개수만큼)
        for _ in range(min(num_threads, task_queue.qsize())):
            page = task_queue.get()
            future = executor.submit(get_data_from_url_single, url, page)
            futures[future] = page

        # ✅ 동적으로 작업 할당
        for future in tqdm.tqdm(concurrent.futures.as_completed(futures), total=end - start + 1):
            page = futures[future]
            try:
                #print(f"DEBUG: future 객체 = {future}")  # ✅ future가 뭔지 확인
                data = future.result()  # ❌ 여기서 에러 발생 가능
                #print(f"DEBUG: future.result() = {data}")  # ✅ 여기까지 도달하면 정상 반환됨
                product_lists[page] = data
            except Exception as e:
                #print(f"❌ 페이지 {page} 크롤링 실패: {e}")
                data = ["get fail"]  # ✅ 예외 발생 시 기본값 설정
                product_lists[page] = data

           # ✅ 페이지 순서 유지하여 저장

            # ✅ 새로운 작업 할당 (스레드가 하나 끝나면 새로운 페이지 크롤링)
            if not task_queue.empty():
                new_page = task_queue.get()
                new_future = executor.submit(get_data_from_url_single, url, new_page)
                futures[new_future] = new_page

            # ✅ 기존 future 제거 (메모리 해제)
            del futures[future]

    # ✅ 페이지 순서대로 결과 정리
    return [product_lists[page] for page in range(start, end + 1)]




def get_data_from_url_single(url,num):
    # Selenium 옵션 설정 (headless 모드)
    options = Options()
    options.add_argument('--headless')       # 브라우저 창 없이 실행
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # ChromeDriver 실행 (경로는 환경변수에 있거나 직접 지정)
    driver = webdriver.Chrome(service = Service(),options=options)
    try:
        # ✅ 페이지 이동
        driver.get(url)
        
        # ✅ 첫 번째 페이지 로딩 완료 대기
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # ✅ 페이지 이동 (num 페이지 클릭)
        if num != 1:
            click_page(num, driver)  
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")

        html = driver.page_source
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html, 'html.parser')
        # 제품 정보 컨테이너 찾기 (여러 상품이 있을 경우 반복문 사용)
        all_product_divs = soup.find_all('div', class_='prod_info')
        # 여러 상품 보를 담을 리스트
        product_list = []
        for prod_info_div in all_product_divs:
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
                comment_div = prod_info_div.find('div', class_='meta_item mt_comment')
                if comment_div:
                    a_comment = comment_div.find('a')
                    if a_comment:
                        # 제품의견 관련 정보: 링크, 의견 수 등
                        product_info['opinion'] = {} 
                        product_info['opinion']['link'] = a_comment.get('href')
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
                # 추출한 스펙 배열을 제품 정보에 추가 (배열 그대로 저장하거나, join()으로 문자열 결합 가능)
                product_info['specs'] = spec_items
                product_list.append(product_info)
               
        for i in range(0, len(product_list)):
            if 'opinion' in product_list[i]:
                try:
                    product_list[i]['opinion']["reviews"] =detail(product_list[i]['opinion']['link'])
                except:
                    product_list[i]['opinion']["reviews"] = ["no review"]
        return product_list  
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        product_list = ["get fail"]
        return product_list
    finally:
        driver.quit()  # ✅ 예외 발생 시에도 브라우저를 안전하게 종료

        
 

def get_data_from_url(url):
    # Selenium 옵션 설정 (headless 모드)
    options = Options()
    options.add_argument('--headless')       # 브라우저 창 없이 실행
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # ChromeDriver 실행 (경로는 환경변수에 있거나 직접 지정)
    driver = webdriver.Chrome(service = Service(),options=options)
    # 크롤링할 URL (실제 다나와 상품 목록 URL로 변경)   
    driver.get(url)
    # 동적 콘텐츠 로드를 위해 대기 (WebDriverWait 사용 권장)
    WebDriverWait(driver, 5).until(lambda driver: driver.execute_script("return document.readyState") == "complete")

    # 렌더링된 HTML 소스 가져오기
    product_lists=[]
    mainFlag=True
    loopnum=2  
    while mainFlag:
        html = driver.page_source
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(html, 'html.parser')
        # 제품 정보 컨테이너 찾기 (여러 상품이 있을 경우 반복문 사용)
        all_product_divs = soup.find_all('div', class_='prod_info')
        # 여러 상품 보를 담을 리스트
        product_list = []
        for prod_info_div in all_product_divs:
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
                comment_div = prod_info_div.find('div', class_='meta_item mt_comment')
                if comment_div:
                    a_comment = comment_div.find('a')
                    if a_comment:
                        # 제품의견 관련 정보: 링크, 의견 수 등
                        product_info['opinion'] = {} 
                        product_info['opinion']['link'] = a_comment.get('href')
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
                # 추출한 스펙 배열을 제품 정보에 추가 (배열 그대로 저장하거나, join()으로 문자열 결합 가능)
                product_info['specs'] = spec_items
                product_list.append(product_info)        
        for i in tqdm.tqdm(range(0, len(product_list))):
            if 'opinion' in product_list[i]:
                product_list[i]['opinion']["reviews"] =detail(product_list[i]['opinion']['link'])
            
        product_lists.append(product_list)
        mainFlag=click_page(loopnum,driver)
        if loopnum>3:
            break
        loopnum=loopnum+1

    driver.quit()
    return product_lists
def save_hdf5(data, filename="danawa_data.h5"):
    with h5py.File(filename, "w") as f:
        json_data = json.dumps(data, ensure_ascii=False)  # ✅ JSON 직렬화
        f.create_dataset("danawa_reviews", data=json_data.encode("utf-8"))  # ✅ UTF-8 인코딩

def load_hdf5(filename="danawa_data.h5"):
    with h5py.File(filename, "r") as f:
        json_data = f["danawa_reviews"][()].decode("utf-8")  # ✅ UTF-8 디코딩
        return json.loads(json_data)  # ✅ JSON 파싱 (원형 복원)

def save_hdf5_separate(data, filename="danawa_data_separate.h5"):
    with h5py.File(filename, "w") as f:
        for i, page in enumerate(data):
            page_data = json.dumps(page, ensure_ascii=False)  # JSON 변환
            f.create_dataset(f"page_{i}", data=page_data.encode("utf-8"))  # UTF-8 인코딩

def load_hdf5_partial(filename="danawa_data_separate.h5", page_index=0):
    with h5py.File(filename, "r") as f:
        json_data = f[f"page_{page_index}"][()].decode("utf-8")  # 특정 페이지만 로드
        return json.loads(json_data)  # JSON 파싱

def extract_name(data,fname="danawa.csv"):
    out=[]
    for d in data:
        if not (d[0]=='get fail'):
            for i in d:
                out.append(i["name"])

    out=pd.DataFrame(out)
    out.to_csv(fname)
    return out
if __name__ == "__main__":
    url = 'https://prod.danawa.com/list/?cate=22254632s'
    #data = get_data_from_url(url)
    data = get_data_from_url_multi_thread(url,1,10)
    extract_name(data)
    save_hdf5(data, "danawa_data.h5")


