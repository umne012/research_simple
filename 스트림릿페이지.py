import streamlit as st
from streamlit_option_menu import option_menu

# ✅ 꼭 첫 줄에 위치해야 함!
st.set_page_config(layout="wide")

# ✅ 스타일 설정 (모듈 내부에 중복 정의하지 않도록 여기서만 정의)
st.markdown("""
    <style>
    * { font-family: 'Pretendard', sans-serif; }
    div.stButton:nth-of-type(1) > button {
        background-color: transparent;
        color: #FA8072;
        padding: 7px 24px;
        border: 1px dashed #FA8072;
        border-radius: 6px;
        font-size: 16px;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    div.stButton:nth-of-type(1) > button:hover {
        background-color: #FA8072;
        color: white;
        border: 1px solid #FA8072;
    }
    button.pdf-btn {
        background-color: transparent;
        color: #4CAF50;
        padding: 7px 24px;
        border: 1px dashed #4CAF50;
        border-radius: 6px;
        font-size: 16px;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    button.pdf-btn:hover {
        background-color: #4CAF50;
        color: white;
        border: 1px solid #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ 탭 상태 유지
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "검색트렌드"

with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=["검색트렌드", "연관어 분석", "긍부정 분석"].index(st.session_state.selected_tab),
    )
    st.session_state.selected_tab = selected_tab

# ✅ 각 탭 실행
if st.session_state.selected_tab == "검색트렌드":
    from 검색트렌드 import show_trend_tab
    show_trend_tab()

elif st.session_state.selected_tab == "연관어 분석":
    from 연관어분석 import show_relation_tab
    show_relation_tab()

elif st.session_state.selected_tab == "긍부정 분석":
    st.title("🙂 긍·부정 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")
