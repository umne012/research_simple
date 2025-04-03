def show_relation_tab():

    import streamlit as st
    import pandas as pd
    import requests
    from io import StringIO
    import json
    
    st.title("📌 연관어 분석")
    
    @st.cache_data
    def load_data():
        # 단어 카운트
        word_df = pd.read_csv("https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_word_count_merged.csv")
        word_data = {brand: df for brand, df in word_df.groupby("그룹")}
    
        # 형태소 분석 문장
        parts = ["part1", "part2", "part3"]
        morph_frames = []
        for part in parts:
            df = pd.read_csv(f"https://raw.githubusercontent.com/umne012/research_simple/main/morpheme_analysis_{part}.csv")
            morph_frames.append(df)
        morph_df = pd.concat(morph_frames, ignore_index=True)
    
        # 전체 문장
        sent_df = pd.read_csv("https://raw.githubusercontent.com/umne012/research_simple/main/sentiment_analysis_merged.csv")
        return word_data, morph_df, sent_df
    
    word_data, morph_df, sent_df = load_data()
    
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
    
    # HTML 코드
    html_code = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8">
    <style>
    body {{ display: flex; font-family: Arial, sans-serif; }}
    svg {{ width: 75%; height: 600px; border: 1px solid #ccc; }}
    #sentence-panel {{
        width: 25%; padding: 10px; background: #f9f9f9;
        border-left: 1px solid #ddd; overflow-y: auto; height: 580px;
    }}
    h3 {{ margin-top: 0; }}
    .text-link {{ margin-bottom: 12px; display: block; font-size: 11px; }}
    </style>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    </head>
    <body>
    <svg></svg>
    <div id="sentence-panel">
        <h3>📝 관련 문장</h3>
        <div id="sentences">노드를 클릭해보세요.</div>
    </div>
    <script>
    const nodes = {nodes_json};
    const links = {links_json};
    const sentenceData = {sentences_json};
    
    const width = document.querySelector("svg").clientWidth;
    const height = document.querySelector("svg").clientHeight;
    const svg = d3.select("svg");
    
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(80))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(width / 2, height / 2));
        
    const linkCount = {{}};
    links.forEach(l => {{
        linkCount[l.target] = (linkCount[l.target] || 0) + 1;
    }});
    
    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("stroke", "#aaa")
        .attr("stroke-width", 2)
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
        .attr("fill", d => {{
            if (d.group === "positive") return "#ADD8E6";
            if (d.group === "negative") return "#FA8072";
            return "#FFD700";
        }})
        .attr("stroke", "#333")
        .attr("stroke-width", 2)
        .attr("stroke-dasharray", "4,2")
        .on("mouseover", function (event, d) {{
            d3.select(this)
                .transition().duration(150)
                .attr("stroke-dasharray", "0")
                .attr("fill", () => {{
                    if (d.group === "positive") return "#87CEEB";
                    if (d.group === "negative") return "#E75454";
                    return "#FFC700";
                }});
        }})
        .on("mouseout", function (event, d) {{
            d3.select(this)
                .transition().duration(150)
                .attr("stroke-dasharray", "4,2")
                .attr("fill", () => {{
                    if (d.group === "positive") return "#ADD8E6";
                    if (d.group === "negative") return "#FA8072";
                    return "#FFD700";
                }});
        }});
    
    node.append("title")
        .text(d => {{
            if (d.group === "brand") return "브랜드";
            return `감정: ${{d.group}}, 언급횟수: ${{d.freq}}`;
        }});
    
    node.append("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .attr("font-size", "11px")
        .text(d => d.id.replace("_positive", "").replace("_negative", ""));
    
    node.on("click", (event, d) => {{
        const panel = document.getElementById("sentences");
        const data = sentenceData[d.id];
        if (!data || data.length === 0) {{
            panel.innerHTML = "<i>관련 문장이 없습니다.</i>";
            return;
        }}
        panel.innerHTML = data.map(s => `
            <a class="text-link" href="${{s['원본링크']}}" target="_blank">
                ${{s['문장']}}
            </a>
        `).join("");
    }});
    
    simulation.on("tick", () => {{
        link.attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
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
    """
    
    st.components.v1.html(html_code, height=650)
