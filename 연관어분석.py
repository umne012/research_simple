import streamlit as st
import pandas as pd
import requests
from io import StringIO
import json

st.title("📌 D3.js 네트워크 그래프 (CSV 기반)")

@st.cache_data
def load_data():
    # 👉 단어 카운트 데이터
    word_url = "https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_word_count_merged.csv"
    word_df = pd.read_csv(StringIO(requests.get(word_url).text))

    # 👉 브랜드별로 분할
    word_data = {
        brand: df for brand, df in word_df.groupby("그룹")
    }

    return word_data

word_data = load_data()

# ✅ nodes와 links 리스트 생성
nodes = []
links = []
added_words = set()

for brand, df in word_data.items():
    # 브랜드 노드 추가
    nodes.append({"id": brand, "group": "brand"})

    word_entries = []
    for _, row in df.iterrows():
        word = row["단어"]
        if row.get("positive", 0) > 0:
            word_entries.append((f"{word}_positive", row["positive"], "positive", word))
        if row.get("negative", 0) > 0:
            word_entries.append((f"{word}_negative", row["negative"], "negative", word))

    # 상위 10개 단어만
    top_entries = sorted(word_entries, key=lambda x: x[1], reverse=True)[:10]

    for node_id, freq, sentiment, word_text in top_entries:
        # 단어 노드 추가
        if node_id not in added_words:
            nodes.append({
                "id": node_id,
                "group": sentiment,
                "freq": freq
            })
            added_words.add(node_id)

        # 링크 추가 (브랜드 → 단어)
        links.append({
            "source": brand,
            "target": node_id
        })

# ✅ D3.js 시각화 삽입
st.components.v1.html(f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        svg {{ width: 100%; height: 600px; border: 1px solid #ccc; }}
        text {{ fill: white; font-size: 11px; pointer-events: none; }}
        circle {{ stroke: black; stroke-width: 1px; }}
    </style>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <svg></svg>
    <script>
        const nodes = {json.dumps(nodes)};
        const links = {json.dumps(links)};

        const width = document.querySelector("svg").clientWidth;
        const height = document.querySelector("svg").clientHeight;
        const svg = d3.select("svg");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke", "#aaa")
            .attr("stroke-width", 2);

        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => {{
                if (d.freq) return Math.max(10, Math.min(40, d.freq * 0.5));
                return 30; // 브랜드 크기
            }})
            .attr("fill", d => {{
                if (d.group === "positive") return "#9370DB";
                if (d.group === "negative") return "#FA8072";
                return "#FFD700"; // 브랜드
            }});

        node.append("text")
            .attr("dy", "0.35em")
            .attr("text-anchor", "middle")
            .text(d => d.id.replace("_positive", "").replace("_negative", ""));

        simulation.on("tick", () => {{
            link.attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
""", height=650)
