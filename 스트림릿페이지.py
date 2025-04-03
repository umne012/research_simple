import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
from io import BytesIO, StringIO
import pandas as pd
import json
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# ✅ 전체 스타일 적용
st.markdown("""
    <style>
    * {
        font-family: 'Pretendard', sans-serif;
    }

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

# ✅ 초기 그룹
original_search_groups = [
    {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]

# ✅ 세션 상태 초기화
if "search_groups" not in st.session_state:
    st.session_state.search_groups = original_search_groups.copy()
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "검색트렌드"

# ✅ 사이드 메뉴 (렌더링만 수행)
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=["검색트렌드", "연관어 분석", "긍부정 분석"].index(st.session_state.selected_tab),
    )
    st.session_state.selected_tab = selected_tab

# ✅ 세션 상태 사용
search_groups = st.session_state.search_groups
selected_tab = st.session_state.selected_tab

# ✅ 탭별 기능 호출 (선택된 탭일 때만 해당 모듈 실행)
if selected_tab == "검색트렌드":
    from 검색트렌드 import show_trend_tab
    show_trend_tab(st, st_tags, date, timedelta, requests, go, search_groups)

elif selected_tab == "연관어 분석":
    from 연관어분석 import show_network_tab
    show_network_tab(st, requests, pd, json, Network, components)

elif selected_tab == "긍부정 분석":
    st.title("🙂 긍·부정 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")
