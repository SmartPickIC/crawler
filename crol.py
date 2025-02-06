from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import tqdm
from itertools import combinations
import re


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
        self.driver.quit()
        return self.review
    def clean(self):
        self.driver.quit()
        return self.review      
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
 
def detail (url):
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    # 크롤링할 페이지 URL (실제 URL로 변경)
    driver.get("https://prod.danawa.com/"+url)
    # 동적 콘텐츠 로드를 위해 충분한 시간 대기 (WebDriverWait 사용 권장)
    time.sleep(5)
    # 두 개의 의견/리뷰 탭 ID 목록 (필요한 경우 두 탭 모두 의견/리뷰 범주에 해당한다고 가정)
    desired_tab_ids = {
        "danawa-prodBlog-productOpinion-button-tab-productOpinion",
        "danawa-prodBlog-productOpinion-button-tab-companyReview"
    }
    # 현재 활성 탭의 <a> 태그 선택 (상위 탭 영역에서 활성 탭은 li 요소에 "on" 클래스가 붙어 있습니다)
    active_tab_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "li.tab_item.on > a"))
    )
    active_tab_id = active_tab_element.get_attribute("id")
    if active_tab_id not in desired_tab_ids:
        print("활성 탭이 의견/리뷰가 아니므로 의견/리뷰 탭으로 전환합니다.")
        # 여기서는 기본으로 "다나와 상품의견" 탭을 선택합니다.
        product_opinion_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "danawa-prodBlog-productOpinion-button-tab-productOpinion"))
        )
        product_opinion_tab.click(),
    # 원하는 시작 노드를 지정한 후, 트리 구조를 출력합니다.
    html = driver.page_source  # Selenium에서 가져온 전체 HTML
    soup = BeautifulSoup(html, 'html.parser')
    try:
        reviews=TapName(driver)
        return reviews.oneshot()
    except:
        print("fail resource release")
        return reviews.clean()
# Selenium 옵션 설정 (headless 모드)
options = Options()
options.add_argument('--headless')       # 브라우저 창 없이 실행
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
# ChromeDriver 실행 (경로는 환경변수에 있거나 직접 지정)
driver = webdriver.Chrome(options=options)
# 크롤링할 URL (실제 다나와 상품 목록 URL로 변경)
url = 'https://prod.danawa.com/list/?cate=22254632'
driver.get(url)
# 동적 콘텐츠 로드를 위해 대기 (WebDriverWait 사용 권장)
time.sleep(5)
# 렌더링된 HTML 소스 가져오기
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
                text = a.get_text(strip=True)
                spec_items.append(text)
        # 추출한 스펙 배열을 제품 정보에 추가 (배열 그대로 저장하거나, join()으로 문자열 결합 가능)
        product_info['specs'] = spec_items
        product_list.append(product_info)
for i in tqdm.tqdm(range(0, len(product_list))):
    product_list[i]['opinion']["reviews"] =detail(product_list[i]['opinion']['link'])




# 브라우저 종료
driver.quit()
print (product_list[2]['opinion']['count'])
print (product_list[2]['opinion']['link'])
print (len(product_list[2]['opinion']['reviews']))
print (len(product_list))