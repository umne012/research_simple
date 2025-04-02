import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
import streamlit.components.v1 as components
from pyvis.network import Network
import pandas as pd

st.set_page_config(layout="wide")

# ✅ 스타일 제거된 버전 (PDF 버튼 제거됨)
st.markdown("""
<style>
* {
    font-family: 'Pretendard', sans-serif;
}

/* 분석 버튼 */
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
</style>
""", unsafe_allow_html=True)

# ✅ 사이드 메뉴
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=0,
    )

# ✅ 그룹 설정
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
    # (기존 검색트렌드 분석 코드 생략)
    pass

elif selected_tab == "연관어 분석":
    st.title("📌 연관어 네트워크 분석")

    # ✅ GitHub raw 링크 대신 Excel 불러오기
    word_count_xlsx = "https://raw.githubusercontent.com/your-username/your-repo/main/morpheme_word_count.xlsx"

    @st.cache_data
    def load_excel_grouped_word_counts(xlsx_url):
        xls = pd.ExcelFile(xlsx_url)
        data = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            word_counts = {
                row["단어"]: {"positive": row.get("positive", 0), "negative": row.get("negative", 0)}
                for _, row in df.iterrows()
            }
            data[sheet] = word_counts
        return data

    word_count_data = load_excel_grouped_word_counts(word_count_xlsx)

    net = Network(height="700px", width="100%", notebook=False, directed=False, bgcolor="#ffffff")
    added_word_nodes = {}

    for brand, words in word_count_data.items():
        net.add_node(brand, label=brand, size=30, color="skyblue", shape="box", font={"size": 16, "color": "black"})

        word_entries = []
        for word, counts in words.items():
            if counts.get("positive", 0) > 0:
                word_entries.append((f"{word}_positive", counts["positive"], "positive", word))
            if counts.get("negative", 0) > 0:
                word_entries.append((f"{word}_negative", counts["negative"], "negative", word))

        top_entries = sorted(word_entries, key=lambda x: x[1], reverse=True)[:10]

        for node_id, freq, sentiment, word in top_entries:
            node_size = max(20, min(50, freq * 0.5))
            color = "lightcoral" if sentiment == "positive" else "lightblue"

            if node_id not in added_word_nodes:
                net.add_node(
                    node_id,
                    label=f"{word}\n({sentiment})",
                    size=node_size,
                    color=color,
                    shape="circle",
                    font={"size": 14, "color": "white"},
                    title=f"언급 횟수: {freq}"
                )
                added_word_nodes[node_id] = True

            net.add_edge(brand, node_id, weight=freq)

    net.force_atlas_2based(gravity=-50, central_gravity=0.02, spring_length=20, spring_strength=0.8)
    net.save_graph("network_graph.html")
    components.iframe("network_graph.html", height=750, scrolling=True)
