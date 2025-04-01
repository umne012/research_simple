import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
import time

st.set_page_config(layout="wide")

# ✅ 전체 폰트 Pretendard 적용
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
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]

search_groups = original_search_groups.copy()

if selected_tab == "검색트렌드":
    st.title("검색트렌드 분석")

    # 📅 날짜 입력 (한 줄에 배치)
    col1, col2 = st.columns([1, 1])
    with col1:
        start_date = st.date_input("시작일", value=date(2025, 3, 12))
    with col2:
        end_date = st.date_input("종료일", value=date(2025, 3, 18))

    # 📌 그룹별 검색어/제외어 수정 인터페이스 (태그형 + 적용 버튼)
    with st.expander("📋 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(
                label="검색어",
                text="엔터로 여러 개 등록",
                value=group["keywords"],
                key=f"kw_{group['groupName']}"
            )
            ex_tags = st_tags(
                label="제외어",
                text="엔터로 여러 개 등록",
                value=group["exclude"],
                key=f"ex_{group['groupName']}"
            )
            group_inputs[group["groupName"]] = {
                "keywords": kw_tags,
                "exclude": ex_tags
            }

        if st.button("🔁 설정 적용"):
            search_groups = [
                {
                    "groupName": name,
                    "keywords": values["keywords"],
                    "exclude": values["exclude"]
                }
                for name, values in group_inputs.items()
            ]

    # ✅ 분석 버튼 별도 배치
    st.markdown("""
    <div style='margin-top: 20px; margin-bottom: 20px;'>
        <h4>📊 분석 시작</h4>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 검색량 및 언급량 분석 시작"):
        st.session_state["run_analysis"] = True

    if st.session_state.get("run_analysis", False):
        # 분석 코드 여기에 이어서 실행 (예: 트렌드 API 호출 등)
        st.info("🔄 분석 중입니다...")
