import streamlit as st
from streamlit_option_menu import option_menu
from 검색트렌드 import show_trend_tab
from 연관어분석 import show_relation_tab

# ✅ 반드시 가장 먼저 호출해야 함
st.set_page_config(layout="wide")

# ✅ 사이드 메뉴로 탭 구분
with st.sidebar:
    selected_tab = option_menu(
        menu_title="📊 Research Dashboard",
        options=["검색트렌드", "연관어 분석"],
        icons=["bar-chart", "graph-up"],
        default_index=0
    )

# ✅ 탭별 함수 호출
if selected_tab == "검색트렌드":
    show_trend_tab()  # 검색트렌드.py에 정의된 함수
elif selected_tab == "연관어 분석":
    show_relation_tab()  # 연관어분석.py에 정의된 함수
