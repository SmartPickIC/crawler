import streamlit as st
import pandas as pd
import os
from controller import Danawacontroller
from datetime import datetime
import YTE as yt    

# 페이지 설정
st.set_page_config(page_title="Crawler Control Panel", layout="wide")
st.title("Crawler Control Panel")
st.write("전체 이용자: 5명 (UI 데모)")

# 사이드바: 모듈 선택
st.sidebar.header("모듈 선택")
use_youtube = st.sidebar.checkbox("유튜브 자막 다운로드")
use_danawa = st.sidebar.checkbox("다나와 크롤링")
use_log = st.sidebar.checkbox("로그 확인")
use_file_explorer = st.sidebar.checkbox("파일 탐색 및 확인")

st.write("## 모듈별 설정 및 실행")

# --- 유튜브 자막 다운로드 ---
if use_youtube:
    st.subheader("유튜브 자막 다운로드")
    yt_search_query = st.text_input("검색어 입력:", placeholder="예: 디에이트")
    if st.button("유튜브 자막 다운로드 실행"):
        st.info("유튜브 자막 다운로드 기능 실행 (기능 구현 필요)")

# --- 다나와 크롤링 ---
if use_danawa:
    st.subheader("다나와 크롤링")

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
        limiter = st.number_input("리미터 값:", min_value=1, value=100, step=10)
        review_factor = st.number_input("리뷰 팩터:", min_value=1, value=1, step=1)

    # 세션 스테이트에서 Danawacontroller 인스턴스 초기화
    if 'controller' not in st.session_state:
        st.session_state.controller = Danawacontroller(
            url=danawa_base_link,
            start=start_page,
            end=end_page,
            output=output_base,
            limiter=limiter,
            reviewfactor=review_factor
        )

    controller = st.session_state.controller  # 컨트롤러 인스턴스 가져오기

    # ✅ 현재 실행 상태 확인
    if controller.is_thread_running():
        st.warning("⚠️ 현재 크롤링 실행 중...")
    else:
        st.success("✅ 크롤링이 실행되지 않은 상태입니다.")

    # 크롤링 실행 버튼
    if st.button("다나와 크롤링 실행", type="primary", disabled=controller.is_thread_running()):
        st.session_state.start_time = datetime.now()
        controller.run_threaded_danawa()
        st.success("🚀 크롤링을 시작했습니다.")

    # 크롤링 종료 버튼
    if controller.is_thread_running():
        if st.button("크롤링 종료", type="primary"):
            controller.stop_threaded_danawa()
            st.warning("🛑 크롤링 종료 요청을 보냈습니다.")

    # 크롤링 종료 대기
    if not controller.is_thread_running() and 'start_time' in st.session_state:
        elapsed_time = (datetime.now() - st.session_state.start_time).total_seconds()
        st.info(f"⌛ 크롤링 완료. 총 소요 시간: {elapsed_time:.2f}초")

    # 크롤링 완료 시 알림
    if not controller.is_thread_running() and controller.crawling_status == "completed":
        st.success("✅ 크롤링이 완료되었습니다!")

    # 데이터베이스 관리 섹션
    st.subheader("데이터베이스 관리")

    tab1, tab2, tab3 = st.tabs(["제품 목록", "블랙리스트", "제품 키워드"])
    
    with tab1:
        st.write("등록된 제품 목록")
        products_df = controller.get_products()
        st.dataframe(products_df)

        # 제품 추가
        new_product = st.text_input("새 제품명 입력")
        if st.button("제품 추가"):
            if new_product:
                controller.add_product(new_product)
                st.rerun()

    with tab2:
        st.write("블랙리스트 관리")
        blacklist_df = pd.DataFrame(controller.clean_item.blacklist, columns=['블랙리스트 단어'])
        st.dataframe(blacklist_df)

        new_blacklist = st.text_input("새 블랙리스트 단어")
        if st.button("단어 추가"):
            if new_blacklist:
                controller.add_to_blacklist(new_blacklist)
                st.rerun()

    with tab3:
        st.write("제품 키워드 관리")
        keywords_df = pd.DataFrame(controller.clean_item.product_keywords, columns=['키워드'])
        st.dataframe(keywords_df)

        new_keyword = st.text_input("새 키워드")
        if st.button("키워드 추가"):
            if new_keyword:
                controller.add_to_product_list(new_keyword)
                st.rerun()

# --- 로그 확인 ---
if use_log:
    st.subheader("로그 확인")
    log_file_path = os.path.join("path", "to", "system.log")  # 실제 로그 파일 경로로 수정 필요
    logs = "시스템 로그 내용 (실제 로그 파일 읽기 기능 구현 필요)"
    st.text_area("시스템 로그", logs, height=300)
    if st.button("로그 새로고침"):
        st.info("로그 새로고침 기능 실행 (기능 구현 필요)")

# --- 파일 탐색 및 확인 ---
if use_file_explorer:
    st.subheader("파일 탐색 및 확인")
    col_left, col_right = st.columns(2)

    with col_left:
        st.write("파일 목록 (테이블 형식)")
        sample_files = pd.DataFrame({
            "파일명": ["product_table.csv", "specs_table.csv", "opinions_table.csv"],
            "크기": ["15KB", "10KB", "12KB"],
            "업데이트": ["2025-02-09", "2025-02-09", "2025-02-09"]
        })
        st.dataframe(sample_files)

    with col_right:
        st.write("파일 미리보기 / 탐색기")
        st.text("선택된 파일 내용 미리보기 (기능 구현 필요)")
        if st.button("파일 다운로드"):
            st.info("파일 다운로드 기능 실행 (기능 구현 필요)")

st.write("각 모듈의 세부 기능은 추후 구현됩니다.")
