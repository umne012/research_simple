import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
from io import BytesIO
import pandas as pd
import json
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# ✅ 전역 스타일
st.markdown("""
<style>
* {
    font-family: 'Pretendard', sans-serif;
}
div.stButton > button {
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
div.stButton > button:hover {
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

# ✅ 그룹 설정 (검색어/제외어)
original_search_groups = [
    {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]
if "search_groups" not in st.session_state:
    st.session_state.search_groups = original_search_groups.copy()

# ✅ 검색트렌드 탭
if selected_tab == "검색트렌드":
    st.title("검색트렌드 분석")
    search_groups = st.session_state.search_groups

    with st.expander("📋 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(label="검색어", text="엔터로 여러 개 등록", value=group["keywords"], key=f"kw_{group['groupName']}")
            ex_tags = st_tags(label="제외어", text="엔터로 여러 개 등록", value=group["exclude"], key=f"ex_{group['groupName']}")
            group_inputs[group["groupName"]] = {"keywords": kw_tags, "exclude": ex_tags}

        if st.button("🔁 설정 적용"):
            st.session_state.search_groups = [
                {"groupName": name, "keywords": values["keywords"], "exclude": values["exclude"]}
                for name, values in group_inputs.items()
            ]

    today = date.today()
    start_date = st.date_input("시작일", value=today - timedelta(days=7))
    end_date = st.date_input("종료일", value=today)
    run_analysis = st.button("🔍 분석 시작")

    if run_analysis:
        def get_date_range(start, end):
            return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]

        search_groups = st.session_state.search_groups
        date_range = get_date_range(start_date, end_date)
        trend_data = {}
        mention_data = {"labels": date_range, "datasets": []}
        group_mentions = {g["groupName"]: [] for g in search_groups}

        # 네이버 검색 API 요청
        try:
            response = requests.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id": st.secrets["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["NAVER_CLIENT_SECRET"],
                    "Content-Type": "application/json",
                },
                json={
                    "startDate": str(start_date),
                    "endDate": str(end_date),
                    "timeUnit": "date",
                    "keywordGroups": [{"groupName": g["groupName"], "keywords": g["keywords"]} for g in search_groups],
                },
            )
            if response.ok:
                trend_data = response.json()
                st.session_state.trend_data = trend_data
            else:
                st.error(f"검색 트렌드 오류: {response.status_code}")
        except Exception as e:
            st.error(f"API 요청 실패: {e}")

        with st.spinner("📰 뉴스·블로그 언급량 수집 중..."):
            for group in search_groups:
                values = []
                for d in date_range:
                    total_mentions = 0
                    for keyword in group["keywords"]:
                        full_query = f"{keyword} {' '.join(['-' + w for w in group['exclude']])} {d}"
                        for endpoint in ["news.json", "blog.json"]:
                            res = requests.get(
                                f"https://openapi.naver.com/v1/search/{endpoint}",
                                headers={
                                    "X-Naver-Client-Id": st.secrets["NAVER_CLIENT_ID_2"],
                                    "X-Naver-Client-Secret": st.secrets["NAVER_CLIENT_SECRET_2"],
                                },
                                params={"query": full_query, "display": 5, "start": 1, "sort": "date"},
                            )
                            if res.ok:
                                total_mentions += res.json().get("total", 0)
                                for item in res.json().get("items", []):
                                    group_mentions[group["groupName"]].append({
                                        "title": item["title"].replace("<b>", "").replace("</b>", ""),
                                        "link": item["link"]
                                    })
                    values.append(total_mentions)
                mention_data["datasets"].append({"label": group["groupName"], "data": values})

        st.session_state.mention_data = mention_data
        st.session_state.group_mentions = group_mentions

    # 시각화
    trend_data = st.session_state.get("trend_data", {})
    mention_data = st.session_state.get("mention_data", {})
    group_mentions = st.session_state.get("group_mentions", {})

    if trend_data and mention_data:
        st.subheader("검색량 및 언급량 그래프")
        col1, col2 = st.columns(2)
        layout = go.Layout(margin=dict(l=40, r=40, t=60, b=100))

        with col1:
            fig = go.Figure(layout=layout)
            fig.update_layout(title="네이버 검색량")
            for group in trend_data.get("results", []):
                fig.add_trace(go.Scatter(
                    x=[d["period"] for d in group["data"]],
                    y=[d["ratio"] for d in group["data"]],
                    mode="lines+markers",
                    name=group["title"]
                ))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure(layout=layout)
            fig2.update_layout(title="뉴스·블로그 언급량")
            for ds in mention_data.get("datasets", []):
                fig2.add_trace(go.Scatter(
                    x=mention_data.get("labels", []),
                    y=ds["data"],
                    mode="lines+markers",
                    name=ds["label"]
                ))
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("뉴스·블로그 문장 리스트")
        cols = st.columns(4)
        for idx, group in enumerate(search_groups):
            with cols[idx % 4]:
                st.markdown(f"<h4 style='text-align:center; color:#0366d6'>{group['groupName']}</h4>", unsafe_allow_html=True)
                for item in group_mentions.get(group['groupName'], [])[:10]:
                    st.markdown(f'''
                    <div style='border:1px solid #eee; padding:10px; margin-bottom:8px; border-radius:8px; background-color:#fafafa;'>
                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#333; font-weight:500;">
                            🔗 {item['title']}
                        </a>
                    </div>
                    ''', unsafe_allow_html=True)

# ✅ 연관어 분석 탭
elif selected_tab == "연관어 분석":
    st.title("📌 연관어 네트워크 분석")

    @st.cache_data
    def load_word_and_sentence_data():
        word_url = "https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_word_count_recovered.xlsx"
        morph_url = "https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_analysis_recovered.xlsx"

        word_response = requests.get(word_url)
        morph_response = requests.get(morph_url)

        word_response.raise_for_status()
        morph_response.raise_for_status()

        word_xls = pd.ExcelFile(BytesIO(word_response.content), engine="openpyxl")
        word_data = {
            sheet: pd.read_excel(word_xls, sheet_name=sheet, engine="openpyxl")
            for sheet in word_xls.sheet_names
        }

        morph_df = pd.read_excel(BytesIO(morph_response.content), sheet_name=None, engine="openpyxl")
        all_sentences = pd.concat(morph_df.values(), ignore_index=True)

        return word_data, all_sentences

    word_data, sentence_df = load_word_and_sentence_data()
    left_col, right_col = st.columns([2, 1])
    with left_col:
        net = Network(height="700px", width="100%", notebook=False, directed=False, bgcolor="#ffffff")
        added_word_nodes = {}
        sentence_map = {}

        for brand, df in word_data.items():
            net.add_node(brand, label=brand, size=30, color="skyblue", shape="box", font={"size": 16})
            word_entries = []
            for _, row in df.iterrows():
                word = row["단어"]
                if row.get("positive", 0) > 0:
                    word_entries.append((f"{word}_positive", row["positive"], "positive", word))
                if row.get("negative", 0) > 0:
                    word_entries.append((f"{word}_negative", row["negative"], "negative", word))

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
                    added_word_nodes[node_id] = word
                    matched = sentence_df[(sentence_df["단어"] == word) & (sentence_df["감정"] == sentiment)]
                    sentences = matched[["문장ID", "단어", "원본링크"]].drop_duplicates().to_dict("records")
                    sentence_map[node_id] = sentences

                net.add_edge(brand, node_id, weight=freq)

        net.force_atlas_2based(gravity=-50, central_gravity=0.02, spring_length=20, spring_strength=0.8)
        net.save_graph("network_graph.html")
        components.iframe("network_graph.html", height=750, scrolling=True)

    with right_col:
        st.subheader("📝 단어 관련 문장 보기")
        st.markdown("노드를 클릭하면 해당 단어가 포함된 문장이 여기에 표시됩니다.")
        st.markdown("<div id='sentence-list'></div>", unsafe_allow_html=True)

        st.components.v1.html(f"""
        <script>
        const sentenceData = {json.dumps(sentence_map)};
        window.addEventListener('message', (e) => {{
            const nodeId = e.data;
            const container = window.parent.document.querySelector('#sentence-list');
            if (!container) return;
            if (sentenceData[nodeId]) {{
                let html = '';
                sentenceData[nodeId].forEach((s, i) => {{
                    html += `<div style='margin-bottom:8px;'>
                        <a href='${{s["원본링크"]}}' target='_blank'>🔗 문장ID: ${{s["문장ID"]}} (${{s["단어"]}})</a>
                    </div>`;
                }});
                container.innerHTML = html;
            }}
        }});
        </script>
        """, height=0)

# ✅ 긍부정 분석 탭
elif selected_tab == "긍부정 분석":
    st.title("🙂 긍·부정 분석 (개발 예정)")
    st.info("이 탭은 준비 중입니다.")
