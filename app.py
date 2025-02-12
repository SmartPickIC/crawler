import threading
import streamlit as st
import pandas as pd
import os
from danawa import ProductDatabasePickleFixed, run
import hashlib
from datetime import datetime
import re
import YTE as yt    
from pathlib import Path
# 페이지 설정: 제목, 레이아웃 등
st.set_page_config(page_title="Crawler Control Panel", layout="wide")
st.title("Crawler Control Panel")
st.write("전체 이용자: 5명 (UI 데모)")

# 사이드바: 모듈 선택용 체크박스 4개
st.sidebar.header("모듈 선택")
use_youtube = st.sidebar.checkbox("유튜브 자막다운로드")
use_danawa = st.sidebar.checkbox("다나와 크롤링")
use_log = st.sidebar.checkbox("로그 확인")
use_file_explorer = st.sidebar.checkbox("파일 탐색 및 확인")

st.write("## 모듈별 설정 및 실행")











# --- 유튜브 자막다운로드 ---
if use_youtube:
    st.subheader("유튜브 자막다운로드")
    # 검색어 입력칸 (필요에 따라 영상 링크 입력 등 추가 가능)
    yt_search_query = st.text_input("검색어 입력:", placeholder="예: 디에이트")
    # (필요 시 다른 입력 필드 추가)
    if st.button("유튜브 자막다운로드 실행"):
        # 여기에서 유튜브 자막 다운로드 기능을 호출하는 코드를 넣으세요.
        st.info("유튜브 자막다운로드 기능 실행 (기능 구현 필요)")

if use_danawa:
    st.subheader("다나와 크롤링")
    
    # 메인 설정들을 컬럼으로 나눠서 배치
    col1, col2 = st.columns(2)
    
    with col1:
        danawa_base_link = st.text_input(
            "다나와 베이스링크 입력:", 
            value="https://prod.danawa.com/list/?cate=22254632",
            help="크롤링할 다나와 카테고리 페이지의 URL을 입력하세요"
        )
        
        start_page = st.number_input("시작 페이지:", min_value=1, value=1, step=1)
        end_page = st.number_input("종료 페이지:", min_value=1, value=11, step=1)
    
    with col2:
        output_base = st.text_input("기본 출력 경로:", value="output", help="기본 출력 폴더명을 지정하세요")
        csv_path = f"{output_base}/csv"
        pickle_path = f"{output_base}/pickle"
        image_path = f"{output_base}/images"

    # 디버그 설정 숨기기
    with st.expander("디버그 설정 (개발자용)"):
        limiter = st.number_input("리미터 값:", min_value=1, value=100, step=10)
        review_factor = st.number_input("리뷰 팩터:", min_value=1, value=1, step=1)

    # 세션 스테이트 초기화
    if 'crawling_status' not in st.session_state:
        st.session_state.crawling_status = None
    if 'crawling_thread' not in st.session_state:
        st.session_state.crawling_thread = None
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'clean_itam' not in st.session_state:
        url = danawa_base_link
        safe_url = re.sub(r'[\\/:*?"<>|]', '_', url)
        hashed_filename = hashlib.sha256(url.encode("utf-8")).hexdigest()
        csvname = hashed_filename + ".csv"
        pickle_dir = Path(pickle_path)
        csv_dir = Path(csv_path)
        pickle_dir.mkdir(parents=True, exist_ok=True)
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_filename = os.path.join(csv_path, csvname)
        pickle_filename = os.path.join(pickle_path, hashed_filename + ".pickle")
        st.session_state.clean_itam = ProductDatabasePickleFixed(
            pickle_filename=pickle_filename, 
            csv_filename=csv_filename
        )
    # 데이터베이스 관리 섹션
    st.subheader("데이터베이스 관리")
    
    tab1, tab2, tab3, tab4 = st.tabs(["제품 목록", "블랙리스트", "제품 키워드", "정규표현식 패턴"])
    with tab1:
        # 제품 목록 표시
        st.write("등록된 제품 목록")
        products_df = pd.DataFrame(list(st.session_state.clean_itam.products.items()), 
                                 columns=['제품명', 'ID'])
        st.dataframe(products_df)
        
        # 제품 수동 추가
        col1, col2 = st.columns(2)
        with col1:
            new_product = st.text_input("새 제품명 입력")
        with col2:
            if st.button("제품 추가", key="add_product"):
                if new_product:
                    st.session_state.clean_itam.add_product(new_product)
                    st.rerun()

    with tab2:
        # 블랙리스트 관리
        st.write("블랙리스트 단어 목록")
        blacklist_df = pd.DataFrame(list(st.session_state.clean_itam.blacklist), 
                                  columns=['블랙리스트 단어'])
        st.dataframe(blacklist_df)
        
        # 블랙리스트 단어 추가/제거
        col1, col2, col3 = st.columns(3)
        with col1:
            new_blacklist = st.text_input("새 블랙리스트 단어")
        with col2:
            if st.button("단어 추가", key="add_blacklist"):
                if new_blacklist:
                    st.session_state.clean_itam.add_to_blacklist(new_blacklist)
                    st.rerun()
        with col3:
            selected_blacklist = st.selectbox(
                "제거할 단어 선택",
                options=list(st.session_state.clean_itam.blacklist)
            )
            if st.button("단어 제거", key="remove_blacklist"):
                if selected_blacklist:
                    st.session_state.clean_itam.remove_from_blacklist(selected_blacklist)
                    st.rerun()

    with tab3:
        # 제품 키워드 관리
        st.write("제품 키워드 목록")
        keywords_df = pd.DataFrame(list(st.session_state.clean_itam.product_keywords), 
                                 columns=['키워드'])
        st.dataframe(keywords_df)
        
        # 키워드 추가/제거
        col1, col2, col3 = st.columns(3)
        with col1:
            new_keyword = st.text_input("새 키워드")
        with col2:
            if st.button("키워드 추가", key="add_keyword"):
                if new_keyword:
                    st.session_state.clean_itam.add_to_product_list(new_keyword)
                    st.rerun()
        with col3:
            selected_keyword = st.selectbox(
                "제거할 키워드 선택",
                options=list(st.session_state.clean_itam.product_keywords)
            )
            if st.button("키워드 제거", key="remove_keyword"):
                if selected_keyword:
                    st.session_state.clean_itam.remove_from_product_list(selected_keyword)
                    st.rerun()
# 정규표현식 패턴 관리 탭 수정
    with tab4:
        st.write("정규표현식 패턴 관리")
        
        # 패턴을 | 단위로 분리하여 표시
        def split_pattern(pattern):
            # 패턴에서 괄호 묶음 제거 후 | 로 분리
            pattern = pattern.strip('^$()') 
            return pattern.split('|')

        # 현재 패턴 표시
        st.write("출시연도 패턴:")
        year_patterns = split_pattern(st.session_state.clean_itam.regex_release_year.pattern)
        year_df = pd.DataFrame({"패턴": year_patterns})
        st.dataframe(year_df)

        st.write("모델번호 패턴:")
        model_patterns = split_pattern(st.session_state.clean_itam.regex_model_number.pattern)
        model_df = pd.DataFrame({"패턴": model_patterns})
        st.dataframe(model_df)
        
        # 패턴 추가
        pattern_type = st.selectbox("패턴 종류 선택", ["출시연도", "모델번호"])
        new_pattern = st.text_input("새 패턴")
        
        if st.button("패턴 추가", key="add_pattern"):
            try:
                # 현재 패턴 가져오기
                current_patterns = (year_patterns if pattern_type == "출시연도" 
                                else model_patterns)
                
                # 새 패턴 추가
                if new_pattern not in current_patterns:
                    current_patterns.append(new_pattern)
                    
                    # 패턴 저장
                    patterns = {
                        "release_year": st.session_state.clean_itam.regex_release_year.pattern,
                        "model_number": st.session_state.clean_itam.regex_model_number.pattern
                    }
                    
                    if pattern_type == "출시연도":
                        patterns["release_year"] = "^(" + "|".join(current_patterns) + ")$"
                    else:
                        patterns["model_number"] = "^(" + "|".join(current_patterns) + ")$"
                    
                    with open("regex_patterns.txt", "w", encoding="utf-8") as f:
                        for key, pattern in patterns.items():
                            f.write(f"{key}:{pattern}\n")
                    
                    st.session_state.clean_itam.load_regex_patterns()
                    st.success("패턴이 추가되었습니다.")
                    st.rerun()
            except Exception as e:
                st.error(f"패턴 추가 중 오류 발생: {str(e)}")

        # 패턴 제거
        st.write("패턴 제거")
        current_patterns = year_patterns if pattern_type == "출시연도" else model_patterns
        pattern_to_remove = st.selectbox("제거할 패턴 선택", current_patterns)
        
        if st.button("패턴 제거", key="remove_pattern"):
            try:
                patterns = {
                    "release_year": st.session_state.clean_itam.regex_release_year.pattern,
                    "model_number": st.session_state.clean_itam.regex_model_number.pattern
                }
                
                current_patterns.remove(pattern_to_remove)
                
                if pattern_type == "출시연도":
                    patterns["release_year"] = "^(" + "|".join(current_patterns) + ")$"
                else:
                    patterns["model_number"] = "^(" + "|".join(current_patterns) + ")$"
                
                with open("regex_patterns.txt", "w", encoding="utf-8") as f:
                    for key, pattern in patterns.items():
                        f.write(f"{key}:{pattern}\n")
                
                st.session_state.clean_itam.load_regex_patterns()
                st.success("패턴이 제거되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"패턴 제거 중 오류 발생: {str(e)}")

        # 상태 표시 영역
        status_area = st.empty()

    # 상태 표시 영역과 컨트롤 버튼들
    col1, col2 = st.columns(2)

    with col1:
        status_area = st.empty()  # 상태 표시 영역

    with col2:
        # 크롤링 중일 때만 종료 버튼 표시
        if st.session_state.crawling_status == "running":
            if st.button("크롤링 종료", type="primary", use_container_width=True):
                try:
                    with open('output/flag.txt', 'w') as f:
                        f.write("0")
                    st.warning("크롤링 종료 신호를 보냈습니다. 현재 작업 완료 후 종료됩니다...")
                except Exception as e:
                    st.error(f"종료 신호 전송 중 오류 발생: {str(e)}")


    # 크롤링 실행 부분 수정
    if st.button("다나와 크롤링 실행", type="primary", 
                disabled=st.session_state.crawling_status == "running"):
        try:
            st.session_state.crawling_status = "running"
            st.session_state.start_time = datetime.now()
            
            run(
                st.session_state.clean_itam,
                url=danawa_base_link,
                start=start_page,
                end=end_page,
                output=output_base,
                csv_path=csv_path,
                pickle_path=pickle_path,
                image_path=image_path,
                limiter=limiter,
                reviewfactor=review_factor  
            )
            st.session_state.running_status = False
            st.rerun()
            st.session_state.crawling_status = "completed"
            st.success("크롤링이 완료되었습니다!")
        except Exception as e:
            st.session_state.running_status = False
            st.session_state.crawling_status = f"error: {str(e)}"
            st.error(f"크롤링 중 오류가 발생했습니다: {str(e)}")
            st.exception(e)

# --- 로그 확인 ---
if use_log:
    st.subheader("로그 확인")
    # 이 부분은 Docker 내부의 시스템 메시지를 읽어와서 보여줘야 합니다.
    # 예를 들어, 특정 로그 파일을 읽어와서 표시하도록 구현할 수 있습니다.
    log_file_path = os.path.join("path", "to", "system.log")  # 실제 로그 파일 경로로 수정 필요
    # 로그 파일 내용 읽기 (기능 구현 필요)
    logs = "시스템 로그 내용 (실제 로그 파일 읽기 기능 구현 필요)"
    st.text_area("시스템 로그", logs, height=300)
    if st.button("로그 새로고침"):
        # 로그를 새로고침하는 기능 구현
        st.info("로그 새로고침 기능 실행 (기능 구현 필요)")

# --- 파일 탐색 및 확인 ---
if use_file_explorer:
    st.subheader("파일 탐색 및 확인")
    # 화면을 두 개의 열로 분할: 좌측은 테이블 형식의 파일 목록, 우측은 파일 미리보기 또는 탐색기 형태
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("파일 목록 (테이블 형식)")
        # 실제 파일 목록을 불러와서 DataFrame으로 표시하는 코드를 넣으세요.
        sample_files = pd.DataFrame({
            "파일명": ["product_table.csv", "specs_table.csv", "opinions_table.csv"],
            "크기": ["15KB", "10KB", "12KB"],
            "업데이트": ["2025-02-09", "2025-02-09", "2025-02-09"]
        })
        st.dataframe(sample_files)
    with col_right:
        st.write("파일 미리보기 / 탐색기")
        # 선택된 파일의 내용을 보여주고, 다운로드 버튼을 제공하는 기능을 구현하세요.
        st.text("선택된 파일 내용 미리보기 (기능 구현 필요)")
        if st.button("파일 다운로드"):
            st.info("파일 다운로드 기능 실행 (기능 구현 필요)")

st.write("각 모듈의 세부 기능은 추후 구현됩니다.")
