import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags

st.set_page_config(layout="wide")

# ✅ 전체 폰트 Pretendard 적용 및 버튼 스타일 통합
st.markdown("""
    <style>
    * {
        font-family: 'Pretendard', sans-serif;
    }
    .st-emotion-cache-6qob1r {
        font-weight: bold;
    }
    .tag-box {
        background-color: #f1f3f5;
        padding: 8px 12px;
        margin: 4px;
        border-radius: 8px;
        display: inline-block;
        font-size: 14px;
    }
    div.stButton > button.run-button {
        background-color: transparent;
        color: #0366d6;
        padding: 7px 24px;
        border: 1px dashed #0366d6;
        border-radius: 6px;
        font-size: 16px;
        width: 100%;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    div.stButton > button.run-button:hover {
        background-color: #0366d6;
        color: white;
        border-style: solid;
    }
    div.stButton > button.pdf-button {
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
    div.stButton > button.pdf-button:hover {
        background-color: #4CAF50;
        color: white;
        border-style: solid;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ 사이드 네비게이션 메뉴 적용
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=0,
    )

# ✅ 초기 검색 그룹 설정
original_search_groups = [
    {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]

if "search_groups" not in st.session_state:
    st.session_state.search_groups = original_search_groups.copy()

search_groups = st.session_state.search_groups

if selected_tab == "검색트렌드":
    st.title("검색트렌드 분석")

    with st.expander("📋 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(label="검색어", text="엔터로 여러 개 등록", value=group["keywords"], key=f"kw_{group['groupName']}")
            ex_tags = st_tags(label="제외어", text="엔터로 여러 개 등록", value=group["exclude"], key=f"ex_{group['groupName']}")
            group_inputs[group["groupName"]] = {"keywords": kw_tags, "exclude": ex_tags}

        if st.button("🔁 설정 적용", key="apply_button"):
            st.session_state.search_groups = [
                {"groupName": name, "keywords": values["keywords"], "exclude": values["exclude"]}
                for name, values in group_inputs.items()
            ]
            search_groups = st.session_state.search_groups

    today = date.today()
    default_start = today - timedelta(days=7)
    default_end = today

    col1, col2, col3, col4 = st.columns([2.1, 2.1, 1, 1])
    with col1:
        start_date = st.date_input("시작일", value=default_start)
    with col2:
        end_date = st.date_input("종료일", value=default_end)
    with col3:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🔍 분석 시작", key="run_button"):
            st.session_state.run_analysis = True
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        if st.button("📄 PDF 저장", key="pdf_button"):
            js = "window.print();"
            st.components.v1.html(f"<script>{js}</script>", height=0)
        st.markdown("</div>", unsafe_allow_html=True)
