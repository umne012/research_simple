import streamlit as st
import pandas as pd
import json
import plotly.express as px
from streamlit.components.v1 import html


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

    # ✅ 실제 GitHub 경로로 정의
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

    # ✅ 버블차트용 데이터 구성
    brands = ["KT", "KT Skylife", "LGU+", "SKB"]
    bubble_data = {}
    sentence_map = {}

    for brand in brands:
        brand_df = morph_df[morph_df["그룹"] == brand]
        word_sentiment_counts = (
            brand_df.groupby(["단어", "감정"])["문장ID"]
            .count()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        top_words = word_sentiment_counts.groupby("감정").head(10)

        nodes = []
        for _, row in top_words.iterrows():
            nodes.append({
                "id": row["단어"],
                "group": row["감정"],
                "size": row["count"]
            })

            matched_ids = brand_df[
                (brand_df["단어"] == row["단어"]) & (brand_df["감정"] == row["감정"])
            ]["문장ID"].unique()
            matched_sents = sent_df[(sent_df["문장ID"].isin(matched_ids)) & (sent_df["그룹"] == brand)]

            sentence_map[row["단어"]] = [
                {
                    "문장": s["문장"][:100] + "..." if len(s["문장"]) > 100 else s["문장"],
                    "링크": s["원본링크"]
                }
                for _, s in matched_sents.iterrows()
            ]

        bubble_data[brand] = nodes

    # ✅ 레이아웃 구성 (2x2 버블 + 오른쪽 1개 문장 패널)
    st.markdown("### 🧼 브랜드별 버블차트")
    layout_cols = st.columns([2, 2, 2, 1.5])
    for i, brand in enumerate(brands):
        with layout_cols[i % 3]:
            st.markdown(f"**{brand}**")
            nodes_json = json.dumps(bubble_data[brand], ensure_ascii=False)
            sentences_json = json.dumps(sentence_map, ensure_ascii=False)

            html_code = f"""
            <html>
            <head>
            <script src=\"https://d3js.org/d3.v7.min.js\"></script>
            <style>
                svg {{ width: 100%; height: 300px; }}
                text {{ fill: white; font-size: 10px; pointer-events: none; }}
                rect {{ stroke: black; stroke-width: 1px; }}
            </style>
            </head>
            <body>
            <svg></svg>
            <script>
                const nodes = {nodes_json};
                const sentenceData = {sentences_json};

                const width = document.querySelector("svg").clientWidth;
                const height = document.querySelector("svg").clientHeight;
                const svg = d3.select("svg");

                const simulation = d3.forceSimulation(nodes)
                    .force("charge", d3.forceManyBody().strength(10))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("collision", d3.forceCollide().radius(d => d.size * 1.3))
                    .alphaDecay(0.05);

                const node = svg.append("g")
                    .selectAll("g")
                    .data(nodes)
                    .enter().append("g")
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                node.append("rect")
                    .attr("width", d => d.size * 3)
                    .attr("height", d => d.size * 2)
                    .attr("x", d => -d.size * 1.5)
                    .attr("y", d => -d.size)
                    .attr("rx", 10)
                    .attr("ry", 10)
                    .attr("fill", d => d.group === "positive" ? "#68a0cf" : "#fa7b7b")
                    .attr("stroke", "black")
                    .attr("stroke-width", 1.5);

                node.append("text")
                    .attr("dy", "0.3em")
                    .attr("text-anchor", "middle")
                    .text(d => d.id);

                node.on("click", (event, d) => {{
                    const msgPanel = parent.document.getElementById("sentence-panel");
                    const sents = sentenceData[d.id];
                    if (!msgPanel || !sents) return;
                    msgPanel.innerHTML = sents.map(s => `<div style='margin-bottom:4px'><a href='${{s.링크}}' target='_blank'>📌 ${{s.문장}}</a></div>`).join("");
                }});

                simulation.on("tick", () => {{
                    node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
                }});

                function dragstarted(event, d) {{ if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
                function dragged(event, d) {{ d.fx = event.x; d.fy = event.y; }}
                function dragended(event, d) {{ if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}
            </script>
            </body>
            </html>
            """
            html(html_code, height=320)

    # ✅ 문장 패널 (고정)
    with layout_cols[3]:
        st.markdown("#### 관련 문장")
        html("<div id='sentence-panel' style='height:600px; overflow-y:auto; background:#f5f5f5; padding:10px;'>단어를 클릭하면 문장이 여기에 표시됩니다.</div>", height=650)

    # ✅ 긍정 비율 시간 변화 선그래프
    st.divider()
    st.markdown("### 📈 긍정 단어 비율 추이 (일별)")
    if "날짜" in morph_df.columns:
        trend_df = (
            morph_df.groupby(["날짜", "그룹", "감정"])['단어']
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
        st.warning("📌 '날짜' 컬럼이 분석 파일에 필요합니다.")
