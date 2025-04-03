import streamlit as st
from streamlit_option_menu import option_menu
st.set_page_config(layout="wide")

# ✅ 탭 선택 상태 유지
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "검색트렌드"

# ✅ 사이드바 탭 메뉴
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=["검색트렌드", "연관어 분석", "긍부정 분석"].index(st.session_state.selected_tab),
    )
    st.session_state.selected_tab = selected_tab

# ✅ 탭별 기능 호출
if selected_tab == "검색트렌드":
    from 검색트렌드 import show_trend_tab
    show_trend_tab(st)

elif selected_tab == "연관어 분석":
    from 연관어분석 import show_network_tab
    show_network_tab(st)

elif selected_tab == "긍부정 분석":
    st.title("🙂 긍·부정 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")
