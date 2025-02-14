import streamlit as st
import pandas as pd
import os
from controller import Danawacontroller, YTcontroller,CrawlerStateManager
from datetime import datetime   
import time 

# ✅ Streamlit 앱 실행 시 상태 관리 클래스 초기화
if "state_manager" not in st.session_state:
    st.session_state.state_manager = CrawlerStateManager()


state_manager = st.session_state.state_manager  # ✅ 클래스 인스턴스 가져오기

# ✅ 현재 실행 상태 확인
is_danawa_running = state_manager.is_danawa_running()
is_youtube_running = state_manager.is_youtube_running()

# ✅ 사이드바 체크박스 (크롤링 중이면 비활성화)
st.sidebar.header("모듈 선택")
use_youtube = st.sidebar.checkbox("유튜브 크롤링", disabled=is_danawa_running or is_youtube_running)
use_danawa = st.sidebar.checkbox("다나와 크롤링", disabled=is_danawa_running or is_youtube_running)

st.write("## 모듈별 설정 및 실행")

# --- 유튜브 크롤링 ---
if use_youtube:
    st.subheader("유튜브 크롤링")
    
    save_base = st.text_input("저장 폴더:", value="output/youtube", help="유튜브 크롤링 데이터 저장 폴더", disabled=is_youtube_running)

    # ✅ 유튜브 컨트롤러 인스턴스 생성
    if "youtube_controller" not in st.session_state:
        st.session_state.youtube_controller = YTcontroller(save_base=save_base)

    youtube_controller = st.session_state.youtube_controller

    # ✅ 크롤링 실행 버튼 (다나와 실행 중이면 비활성화)
    if st.button("유튜브 크롤링 실행", type="primary", disabled=is_youtube_running or is_danawa_running):
        state_manager.start_youtube()  # ✅ 버튼 누르는 순간 즉시 상태 변경
        youtube_controller.run_threaded_youtube()
        st.success("🚀 유튜브 크롤링을 시작했습니다.")
        st.session_state.state_manager.rerun_state=1
        st.rerun()  # ✅ 데이터프레임 갱신

    # ✅ 크롤링 종료 버튼 (실행 중일 때만 활성화)
    if is_youtube_running:
        if st.button("크롤링 종료", type="primary"):
            state_manager.stop_youtube(youtube_controller)  # ✅ 실제 종료 확인 후 상태 변경
            st.warning("🛑 유튜브 크롤링 종료 요청을 보냈습니다.")
            st.session_state.state_manager.rerun_state=1
            st.rerun()  # ✅ 데이터프레임 갱신


# --- 다나와 크롤링 ---
if use_danawa:
    st.subheader("다나와 크롤링")

    col1, col2 = st.columns(2)

    with col1:
        danawa_base_link = st.text_input(
            "다나와 베이스링크 입력:",
            value="https://prod.danawa.com/list/?cate=22254632",
            help="크롤링할 다나와 카테고리 페이지의 URL을 입력하세요",
            disabled=is_danawa_running or is_youtube_running
        )
        start_page = st.number_input("시작 페이지:", min_value=1, value=1, step=1, disabled=is_danawa_running or is_youtube_running)
        end_page = st.number_input("종료 페이지:", min_value=1, value=100, step=1, disabled=is_danawa_running or is_youtube_running)

    with col2:
        output_base = st.text_input("기본 출력 경로:", value="output/first", help="기본 출력 폴더명을 지정하세요", disabled=is_danawa_running or is_youtube_running)
        limiter = st.number_input("리미터 값:", min_value=1, value=100, step=10, disabled=is_danawa_running or is_youtube_running)
        review_factor = st.number_input("리뷰 팩터:", min_value=1, value=1, step=1, disabled=is_danawa_running or is_youtube_running)

    # ✅ 다나와 컨트롤러 인스턴스 생성
    if "controller" not in st.session_state:
        st.session_state.controller = Danawacontroller(
            url=danawa_base_link,
            start=start_page,
            end=end_page,
            output=output_base,
            limiter=limiter,
            reviewfactor=review_factor
        )

    controller = st.session_state.controller  # 컨트롤러 인스턴스 가져오기

    # ✅ 크롤링 실행 버튼 (유튜브 실행 중이면 비활성화)
    if st.button("다나와 크롤링 실행", type="primary", disabled=is_danawa_running or is_youtube_running):
        state_manager.start_danawa()  # ✅ 버튼 누르는 순간 즉시 상태 변경
        controller.run_threaded_danawa()
        st.success("🚀 다나와 크롤링을 시작했습니다.")
        st.session_state.state_manager.rerun_state=1
        st.rerun()  # ✅ 데이터프레임 갱신

    # ✅ 다나와 크롤링 종료 버튼 (실행 중일 때만 활성화)
    if is_danawa_running:
        if st.button("크롤링 종료", type="primary"):
            state_manager.stop_danawa(controller)  # ✅ 실제 종료 확인 후 상태 변경
            st.warning("🛑 다나와 크롤링 종료 요청을 보냈습니다.")
            st.session_state.state_manager.rerun_state=1
            st.rerun()  # ✅ 데이터프레임 갱신

    tab1, tab2, tab3 = st.tabs(["제품 목록", "블랙리스트", "제품 키워드"])

    # --- 제품 목록 ---
    with tab1:
        st.write("📌 등록된 제품 목록")
        products_df = controller.get_products()
        st.dataframe(products_df)

        new_product = st.text_input("새 제품명 입력", key="add_product")
        if st.button("제품 추가"):
            if new_product:
                controller.add_product(new_product)
                st.session_state["products_df"] = controller.get_products()  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신

        # ✅ 제품 제거 기능 추가 (데이터가 있을 때만 실행)
        if not products_df.empty:
            selected_product = st.selectbox("제거할 제품 선택", products_df["제품명"], key="remove_product")
            if st.button("제품 제거"):
                controller.clean_item.products.pop(selected_product, None)  # ✅ 제품 제거
                st.session_state["products_df"] = controller.get_products()  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신
        else:
            st.warning("❌ 제거할 제품이 없습니다.")

    # --- 블랙리스트 관리 ---
    with tab2:
        st.write("🚫 블랙리스트 관리")
        blacklist_df = pd.DataFrame(controller.clean_item.blacklist, columns=['블랙리스트 단어'])
        st.dataframe(blacklist_df)

        new_blacklist = st.text_input("새 블랙리스트 단어", key="add_blacklist")
        if st.button("단어 추가"):
            if new_blacklist:
                controller.add_to_blacklist(new_blacklist)
                st.session_state["blacklist_df"] = pd.DataFrame(controller.clean_item.blacklist, columns=['블랙리스트 단어'])  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신

        # ✅ 블랙리스트 제거 기능 추가 (데이터가 있을 때만 실행)
        if not blacklist_df.empty:
            selected_blacklist = st.selectbox("제거할 단어 선택", blacklist_df["블랙리스트 단어"], key="remove_blacklist")
            if st.button("단어 제거"):
                controller.remove_from_blacklist(selected_blacklist)  # ✅ 단어 제거
                st.session_state["blacklist_df"] = pd.DataFrame(controller.clean_item.blacklist, columns=['블랙리스트 단어'])  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신
        else:
            st.warning("❌ 제거할 블랙리스트 단어가 없습니다.")

    # --- 제품 키워드 관리 ---
    with tab3:
        st.write("🔍 제품 키워드 관리")
        keywords_df = pd.DataFrame(controller.clean_item.product_keywords, columns=['키워드'])
        st.dataframe(keywords_df)

        new_keyword = st.text_input("새 키워드", key="add_keyword")
        if st.button("키워드 추가"):
            if new_keyword:
                controller.add_to_product_list(new_keyword)
                st.session_state["keywords_df"] = pd.DataFrame(controller.clean_item.product_keywords, columns=['키워드'])  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신

        # ✅ 제품 키워드 제거 기능 추가 (데이터가 있을 때만 실행)
        if not keywords_df.empty:
            selected_keyword = st.selectbox("제거할 키워드 선택", keywords_df["키워드"], key="remove_keyword")
            if st.button("키워드 제거"):
                controller.remove_from_product_list(selected_keyword)  # ✅ 키워드 제거
                st.session_state["keywords_df"] = pd.DataFrame(controller.clean_item.product_keywords, columns=['키워드'])  # ✅ 세션 상태 업데이트
                st.session_state.state_manager.rerun_state=1
                st.rerun()  # ✅ 데이터프레임 갱신
        else:
            st.warning("❌ 제거할 키워드가 없습니다.")
if st.session_state.state_manager.rerun_state<4:
    st.session_state.state_manager.rerun_state += 1
    time.sleep(0.1)
    st.rerun()

