def show_relation_tab():
    import streamlit as st
    import pandas as pd
    import requests
    import matplotlib.pyplot as plt
    import seaborn as sns
    from io import StringIO
    import json

    st.title("📌 연관어 분석")

    # ✅ 주차 선택
    weeks = {
        "3월 1주차 ('25.3.1~3.7)": "2025_03w1",
        "3월 2주차 ('25.3.8~3.14)": "2025_03w2",
        "3월 3주차 ('25.3.15~3.21)": "2025_03w3"
    }
    selected_label = st.selectbox("🗂️ 주차 선택", list(weeks.keys()), index=0)
    selected_week = weeks[selected_label]

    base_url = f"https://raw.githubusercontent.com/umne012/research_simple/main/{selected_week}"
    word_url = f"{base_url}/morpheme_word_count.csv"
    morph_urls = [f"{base_url}/morpheme_analysis_part{i}.csv" for i in range(1, 4)]
    sentiment_url = f"{base_url}/sentiment_analysis.csv"
    mention_url = f"{base_url}/mention_volume.csv"

    @st.cache_data(show_spinner=False)
    def load_data():
        word_df = pd.read_csv(word_url)
        word_data = {brand: df for brand, df in word_df.groupby("그룹")}

        morph_frames = [pd.read_csv(url) for url in morph_urls]
        morph_df = pd.concat(morph_frames, ignore_index=True)

        sentiment_df = pd.read_csv(sentiment_url)
        mention_df = pd.read_csv(mention_url)
        return word_data, morph_df, sentiment_df, mention_df

    try:
        word_data, morph_df, sent_df, mention_df = load_data()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return

    nodes, links, added_words = [], [], set()
    sentence_map = {}
    link_counter = {}

    def highlight_and_shorten(text, keyword):
        if keyword not in text:
            return text[:50] + "..." if len(text) > 50 else text
        idx = text.index(keyword)
        start = max(0, idx - 15)
        end = min(len(text), idx + len(keyword) + 15)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet += "..."
        return snippet.replace(keyword, f"<b style='background:yellow'>{keyword}</b>")

    for brand, df in word_data.items():
        nodes.append({"id": brand, "group": "brand"})
        word_entries = []
        for _, row in df.iterrows():
            word = row["단어"]
            if row.get("positive", 0) > 0:
                word_entries.append((f"{word}_positive", row["positive"], "positive", word))
            if row.get("negative", 0) > 0:
                word_entries.append((f"{word}_negative", row["negative"], "negative", word))
        top_entries = sorted(word_entries, key=lambda x: x[1], reverse=True)[:10]
        for node_id, freq, sentiment, word in top_entries:
            if node_id not in added_words:
                nodes.append({"id": node_id, "group": sentiment, "freq": freq})
                added_words.add(node_id)

                match = morph_df[(morph_df["단어"] == word) & (morph_df["감정"] == sentiment)]
                matched_ids = match["문장ID"].unique()
                matched_sents = sent_df[sent_df["문장ID"].isin(matched_ids)]
                shown = []
                for _, row in matched_sents.iterrows():
                    snippet = highlight_and_shorten(str(row["문장"]), word)
                    shown.append({"문장": snippet, "원본링크": row["원본링크"]})
                sentence_map[node_id] = shown

            links.append({"source": brand, "target": node_id})
            link_counter[node_id] = link_counter.get(node_id, 0) + 1

    nodes_json = json.dumps(nodes)
    links_json = json.dumps(links)
    sentences_json = json.dumps(sentence_map, ensure_ascii=False)

    html_code = f"""
    <html><head><meta charset='UTF-8'>
    <style>
    body {{ display: flex; font-family: Arial, sans-serif; }}
    svg {{ width: 75%; height: 600px; border: 1px solid #ccc; }}
    #sentence-panel {{ width: 25%; padding: 10px; background: #f9f9f9; overflow-y: auto; }}
    .text-link {{ display: block; margin-bottom: 10px; font-size: 13px; }}
    </style><script src="https://d3js.org/d3.v7.min.js"></script></head>
    <body><svg></svg>
    <div id="sentence-panel"><h3>📝 관련 문장</h3><div id="sentences">노드를 클릭해보세요.</div></div>
    <script>
    const nodes = {nodes_json};
    const links = {links_json};
    const sentenceData = {sentences_json};
    const width = document.querySelector("svg").clientWidth;
    const height = document.querySelector("svg").clientHeight;
    const svg = d3.select("svg");

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(70))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(width / 2, height / 2));

    const linkCount = {{}};
    links.forEach(l => {{ linkCount[l.target] = (linkCount[l.target] || 0) + 1; }});

    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("stroke", "#aaa").attr("stroke-width", 2)
        .attr("stroke-dasharray", d => linkCount[d.target] > 1 ? "0" : "4,4");

    const node = svg.append("g")
        .selectAll("g")
        .data(nodes)
        .enter().append("g")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    node.append("circle")
        .attr("r", d => d.freq ? Math.max(5, Math.min(30, d.freq * 0.3)) : 20)
        .attr("fill", d => d.group === "positive" ? "#ADD8E6" : d.group === "negative" ? "#FA8072" : "#FFD700")
        .attr("stroke", "#333").attr("stroke-width", 2).attr("stroke-dasharray", "4,2")
        .on("mouseover", function (event, d) {{ d3.select(this).attr("stroke-dasharray", "0"); }})
        .on("mouseout", function (event, d) {{ d3.select(this).attr("stroke-dasharray", "4,2"); }});

    node.append("title")
        .text(d => d.group === "brand" ? "브랜드" : `감정: ${d.group}, 언급횟수: ${d.freq}`);

    node.append("text")
        .attr("dy", "0.35em").attr("text-anchor", "middle")
        .attr("font-size", "11px")
        .text(d => d.id.replace("_positive", "").replace("_negative", ""));

    node.on("click", (event, d) => {{
        const panel = document.getElementById("sentences");
        const data = sentenceData[d.id];
        if (!data || data.length === 0) {{ panel.innerHTML = "<i>관련 문장이 없습니다.</i>"; return; }}
        panel.innerHTML = data.map(s => `<a class='text-link' href='${{s["원본링크"]}}' target='_blank'>${{s["문장"]}}</a>`).join("");
    }});

    simulation.on("tick", () => {{
        link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        node.attr("transform", d => `translate(${d.x},${d.y})`);
    }});

    function dragstarted(event, d) {{ if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
    function dragged(event, d) {{ d.fx = event.x; d.fy = event.y; }}
    function dragended(event, d) {{ if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}
    </script></body></html>
    """

    st.components.v1.html(html_code, height=650)

    # 📈 선그래프
    st.markdown("### 📈 일자별 언급량 추이")
    fig, ax = plt.subplots(figsize=(10, 3.5))
    sns.lineplot(data=mention_df, x="날짜", y="언급량", hue="브랜드", marker="o", ax=ax)
    ax.set_ylabel("언급량")
    ax.set_xlabel("날짜")
    ax.tick_params(axis='x', rotation=45)
    ax.set_title("일자별 브랜드 언급량")
    st.pyplot(fig)
