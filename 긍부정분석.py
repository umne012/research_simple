import streamlit as st
import pandas as pd
import json
from streamlit.components.v1 import html
import plotly.express as px

def show_sentimental_tab():
    st.title("🙂 긍·부정 분석 (D3.js 버전)")

    # ✅ 주차 선택
    weeks = {
        "3월 1주차 ('25.3.1~3.7')": "2025_03w1",
        "3월 2주차 ('25.3.8~3.14')": "2025_03w2",
        "3월 3주차 ('25.3.15~3.21')": "2025_03w3"
    }
    selected_label = st.selectbox("📂 주차 선택", list(weeks.keys()), index=0)
    selected_week = weeks[selected_label]

    base_url = f"https://raw.githubusercontent.com/umne012/research_simple/main/{selected_week}"
    morph_urls = [f"{base_url}/morpheme_analysis_part{i}.csv" for i in range(1, 4)]
    sentiment_url = f"{base_url}/sentiment_analysis_merged.csv"

    @st.cache_data
    def load_data():
        morph_frames = []
        for url in morph_urls:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            morph_frames.append(df)
        morph_df = pd.concat(morph_frames, ignore_index=True)
        morph_df["문장ID"] = morph_df["문장ID"].astype(str)

        sent_df = pd.read_csv(sentiment_url)
        sent_df.columns = sent_df.columns.str.strip()
        sent_df["문장ID"] = sent_df["문장ID"].astype(str)
        return morph_df, sent_df

    morph_df, sent_df = load_data()

    # ✅ 버블차트 데이터 준비
    brands = ["KT", "KT Skylife", "LGU+", "SKB"]
    bubble_data, sentence_map = {}, {}

    for brand in brands:
        brand_df = morph_df[morph_df["그룹"] == brand]
        word_counts = (
            brand_df.groupby(["단어", "감정"])["문장ID"]
            .count()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        top_words = word_counts.groupby("감정").head(10)
        nodes = []
        for _, row in top_words.iterrows():
            nodes.append({"id": row["단어"], "group": row["감정"], "size": row["count"]})
            matched_ids = brand_df[(brand_df["단어"] == row["단어"]) & (brand_df["감정"] == row["감정"])]["문장ID"]
            matched_sents = sent_df[(sent_df["문장ID"].isin(matched_ids)) & (sent_df["그룹"] == brand)]
            sentence_map[row["단어"]] = [
                {"문장": s["문장"][:100] + "..." if len(s["문장"]) > 100 else s["문장"], "링크": s["원본링크"]}
                for _, s in matched_sents.iterrows()
            ]
        bubble_data[brand] = nodes

    # ✅ 2x2 버블차트 + 오른쪽 문장 패널 구성
    st.markdown("### 🧼 브랜드별 버블차트")
    row1 = st.columns([3, 3, 1])
    row2 = st.columns([3, 3, 1])
    all_rows = row1[:2] + row2[:2]
    sentence_panel_col = row1[2]

    for i, brand in enumerate(brands):
        col = all_rows[i]
        with col:
            st.markdown(f"**{brand}**")
            nodes_json = json.dumps(bubble_data[brand], ensure_ascii=False)
            sents_json = json.dumps(sentence_map, ensure_ascii=False)

            html_code = f"""
            <html><head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                svg {{ width: 100%; height: 300px; }}
                rect {{ stroke: black; stroke-width: 1.2px; }}
                text {{ font-size: 11px; pointer-events: none; fill: white; }}
            </style></head><body>
            <svg></svg>
            <script>
                const nodes = {nodes_json};
                const sentenceData = {sents_json};
                const svg = d3.select("svg");
                const width = document.querySelector("svg").clientWidth;
                const height = document.querySelector("svg").clientHeight;

                const sim = d3.forceSimulation(nodes)
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("charge", d3.forceManyBody().strength(1))  // 💡 약한 힘으로 덜 밀려나게
                    .force("collision", d3.forceCollide().radius(d => Math.sqrt(d.size) * 4))  // 💡 간격 조정
                    .alphaDecay(0.06);

                const node = svg.selectAll("g")
                    .data(nodes).enter().append("g")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                node.append("rect")
                    .attr("width", d => Math.max(40, Math.min(120, d.size * 2.5)))
                    .attr("height", d => Math.max(20, Math.min(60, d.size * 1.4)))
                    .attr("x", d => -Math.max(20, Math.min(60, d.size * 1.25)))
                    .attr("y", d => -Math.max(10, Math.min(30, d.size * 0.7)))
                    .attr("rx", 12).attr("ry", 12)
                    .attr("fill", d => d.group === "positive" ? "#68a0cf" : "#fa7b7b")

                node.append("text")
                    .attr("text-anchor", "middle")
                    .attr("dy", "0.3em")
                    .text(d => d.id);

                sim.on("tick", () => {{
                    node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
                }});

                node.on("click", (e, d) => {{
                    const box = parent.document.getElementById("sentence-panel");
                    const sents = sentenceData[d.id] || [];
                    box.innerHTML = sents.length
                        ? sents.map(s => `<a href='${{s.링크}}' target='_blank'>📌 ${{s.문장}}</a>`).join("<br><br>")
                        : "<i>문장이 없습니다</i>";
                }});

                function dragstarted(event, d) {{ if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
                function dragged(event, d) {{ d.fx = event.x; d.fy = event.y; }}
                function dragended(event, d) {{ if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }}
            </script></body></html>
            """
            html(html_code, height=320)

    with sentence_panel_col:
        st.markdown("#### 📄 관련 문장")
        html("<div id='sentence-panel' style='height:620px; overflow-y:auto; background:#f7f7f7; padding:10px;'>단어를 클릭하면 문장이 여기에 표시됩니다.</div>", height=650)

    # ✅ 긍정 비율 변화 선그래프
    st.divider()
    st.markdown("### 📈 긍정 단어 비율 추이 (일별)")
    if "날짜" in morph_df.columns:
        trend_df = (
            morph_df.groupby(["날짜", "그룹", "감정"])["단어"]
            .count()
            .reset_index(name="count")
            .pivot_table(index=["날짜", "그룹"], columns="감정", values="count", fill_value=0)
            .reset_index()
        )
        trend_df["긍정비율"] = trend_df["positive"] / (trend_df["positive"] + trend_df["negative"] + 1e-9) * 100

        fig = px.line(trend_df, x="날짜", y="긍정비율", color="그룹", markers=True)
        fig.update_layout(yaxis_title="긍정 비율 (%)", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("📌 '날짜' 컬럼이 필요합니다.")
