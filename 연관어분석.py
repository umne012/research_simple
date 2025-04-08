def show_relation_tab():
    import streamlit as st
    import pandas as pd
    import requests
    import plotly.graph_objects as go
    from io import StringIO
    import json

    st.title("📌 연관어 분석")

    # ✅ 주차 선택
    weeks = {
        "3월 1주차 ('25.3.1~3.7)": "2025_03w1",
        "3월 2주차 ('25.3.8~3.14)": "2025_03w2",
        "3월 3주차 ('25.3.15~3.21)": "2025_03w3"
    }
    selected_label = st.selectbox("📂 주차 선택", list(weeks.keys()), index=0)
    selected_week = weeks[selected_label]

    base_url = f"https://raw.githubusercontent.com/umne012/research_simple/main/{selected_week}"
    word_url = f"{base_url}/morpheme_word_count_merged.csv"
    morph_urls = [f"{base_url}/morpheme_analysis_part{i}.csv" for i in range(1, 4)]
    sentiment_url = f"{base_url}/sentiment_analysis_merged.csv"

    @st.cache_data(show_spinner=False)
    def load_data():
        word_df = pd.read_csv(word_url)
        word_data = {brand: df for brand, df in word_df.groupby("그룹")}

        morph_frames = []
        for url in morph_urls:
            try:
                df = pd.read_csv(url)
                if not df.empty and all(col in df.columns for col in ["단어", "감정", "문장ID"]):
                    morph_frames.append(df)
            except Exception as e:
                st.warning(f"⚠️ {url} 불러오기 실패: {e}")
        if not morph_frames:
            st.error("❌ 형태소 분석 데이터가 없거나 비어 있습니다.")
            return None, None, None
        morph_df = pd.concat(morph_frames, ignore_index=True)

        try:
            sent_df = pd.read_csv(sentiment_url)
        except Exception as e:
            st.error(f"sentiment_analysis.csv 불러오기 오류: {e}")
            return None, None, None

        morph_df["문장ID"] = morph_df["문장ID"].astype(str)
        sent_df["문장ID"] = sent_df["문장ID"].astype(str)

        return word_data, morph_df, sent_df

    word_data, morph_df, sent_df = load_data()
    if word_data is None:
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
                    shown.append({"문장": snippet, "원본링크": row["원본링크"], "count": freq})
                sentence_map[node_id] = shown

            links.append({"source": brand, "target": node_id})
            link_counter[node_id] = link_counter.get(node_id, 0) + 1

    nodes_json = json.dumps(nodes)
    links_json = json.dumps(links)
    sentences_json = json.dumps(sentence_map, ensure_ascii=False)

    html_template = open("network_graph.html", encoding="utf-8").read()
    st.components.v1.html(html_template, height=650)

    # ✅ 선그래프 (Plotly Graph Object 방식으로 교체)
    st.markdown("### 📊 일자별 언급량 추이")
    if sent_df is not None and "날짜" in sent_df.columns and "원본링크" in sent_df.columns and "그룹" in sent_df.columns:
        mention_daily = sent_df.groupby(["날짜", "그룹"])["원본링크"].nunique().reset_index(name="언급량")

        layout = go.Layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            title=dict(text="일자별 브랜드 언급량 추이", x=0.05, font=dict(size=18)),
            margin=dict(l=40, r=40, t=60, b=100),
            xaxis=dict(title="날짜", showgrid=True, tickangle=-45),
            yaxis=dict(title="언급량", showgrid=True),
            legend=dict(
                orientation="h",
                x=0.5,
                y=-0.2,
                xanchor="center",
                yanchor="top"
            )
        )

        fig = go.Figure(layout=layout)
        for group, df in mention_daily.groupby("그룹"):
            fig.add_trace(go.Scatter(
                x=df["날짜"],
                y=df["언급량"],
                mode="lines+markers",
                name=group
            ))

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📌 일자별 언급량을 시각화하려면 sentiment_analysis.csv에 '날짜', '그룹' 컬럼이 있어야 합니다.")
