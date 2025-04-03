import streamlit as st
import pandas as pd
import requests
from io import StringIO
from pyvis.network import Network
import streamlit.components.v1 as components
import json
import tempfile

def show_relation_tab():
    st.title("📌 연관어 네트워크 분석")

    @st.cache_data
    def load_word_and_sentence_data():
        # 👉 단어 카운트 데이터 (병합된 CSV)
        word_url = "https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_word_count_merged.csv"
        word_response = requests.get(word_url)
        word_response.raise_for_status()
        word_df = pd.read_csv(StringIO(word_response.text))

        # 👉 브랜드별로 분할
        word_data = {
            brand: df for brand, df in word_df.groupby("그룹")
        }

        # 👉 감정 분석 CSV 파트별 불러오기
        parts = ["part1", "part2", "part3"]
        morph_frames = []
        for part in parts:
            url = f"https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_analysis_{part}.csv"
            response = requests.get(url)
            response.raise_for_status()
            morph_frames.append(pd.read_csv(StringIO(response.text)))

        # 👉 전체 문장 데이터 합치기
        sentence_df = pd.concat(morph_frames, ignore_index=True)

        return word_data, sentence_df

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

        # ✅ 고유한 임시파일에 저장 → 캐시 충돌 및 덮어쓰기 방지
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.save_graph(tmp_file.name)
            components.iframe(tmp_file.name, height=750, scrolling=True)

    with right_col:
        st.subheader("📝 단어 관련 문장 보기")
        st.markdown("노드를 클릭하면 해당 단어가 포함된 문장이 여기에 표시됩니다.")
        st.markdown("<div id='sentence-list'></div>", unsafe_allow_html=True)

        # sentence_map을 JSON 문자열로 전달하고, 클릭된 nodeId로 문장 정보 동적 표시
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
