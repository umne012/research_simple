import streamlit as st
from streamlit_option_menu import option_menu

# ✅ 페이지 설정은 맨 위에 한 번만
st.set_page_config(layout="wide")

# ✅ 탭 상태 유지
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "검색트렌드"

# ✅ 사이드 메뉴
with st.sidebar:
    selected_tab = option_menu(
        menu_title="Research",
        options=["검색트렌드", "연관어 분석", "긍·부정 분석", "트렌드 변화 분석"],
        icons=["bar-chart", "diagram-3", "emoji-smile", "shuffle"],
        menu_icon="cast",
        default_index=["검색트렌드", "연관어 분석", "긍·부정 분석", "트렌드 변화 분석"].index(st.session_state.selected_tab),
    )
    st.session_state.selected_tab = selected_tab

# ✅ 탭별 파일 불러오기 (중복 import 방지)
if selected_tab == "검색트렌드":
    from 검색트렌드 import show_trend_tab
    show_trend_tab()

elif selected_tab == "연관어 분석":
    from 연관어분석 import show_relation_tab
    show_relation_tab()

elif selected_tab == "긍·부정 분석":
    st.title("🙂 긍·부정 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")

elif selected_tab == "트렌드 변화 분석":
    st.title("🙂 트렌드 변화 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")
