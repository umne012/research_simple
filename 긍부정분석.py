import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

def show_sentimental_tab():
    st.title("🙂 긍·부정 분석")

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

    # ✅ 데이터 로딩
    @st.cache_data
    def load_data():
        word_df = pd.read_csv(word_url)
        word_df.columns = word_df.columns.str.strip()
        word_data = {brand: df for brand, df in word_df.groupby("그룹")}

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

        return word_data, morph_df, sent_df

    word_data, morph_df, sent_df = load_data()
    brands = ["Skylife", "KT", "LGU+", "SKB"]

    # ✅ 클릭 상태 초기화
    if "clicked_word" not in st.session_state:
        st.session_state.clicked_word = None
    if "clicked_brand" not in st.session_state:
        st.session_state.clicked_brand = None

    st.markdown("### 🔎 감정 단어 버블 차트")
    chart_cols = st.columns([2, 2, 2, 1.5])  # 마지막 열은 문장 출력용

    for idx, brand in enumerate(brands):
        with chart_cols[idx]:
            df = word_data.get(brand)
            if df is None:
                continue

            word_entries = []
            for _, row in df.iterrows():
                word = row["단어"]
                if row.get("positive", 0) > 0:
                    word_entries.append((word, row["positive"], "positive"))
                if row.get("negative", 0) > 0:
                    word_entries.append((word, row["negative"], "negative"))

            top_entries = sorted(word_entries, key=lambda x: x[1], reverse=True)[:10]
            chart_df = pd.DataFrame(top_entries, columns=["word", "count", "sentiment"])

            fig = px.scatter(
                chart_df,
                x=[i for i in range(len(chart_df))],
                y=[1]*len(chart_df),
                size="count",
                color="sentiment",
                hover_name="word",
                color_discrete_map={"positive": "#9370DB", "negative": "#FA8072"},
                size_max=60
            )
            fig.update_traces(marker=dict(line=dict(width=1, color="black")))
            fig.update_layout(height=600, margin=dict(l=5, r=5, t=30, b=5), showlegend=False)

            st.plotly_chart(fig, use_container_width=True)

            # 단어 선택 대체 (임시)
            selected_word = st.selectbox(f"{brand} 단어 선택", chart_df["word"].unique(), key=f"{brand}_word")
            if selected_word:
                st.session_state.clicked_word = selected_word
                st.session_state.clicked_brand = brand

    # ✅ 오른쪽 문장 출력 영역
    with chart_cols[-1]:
        st.markdown("#### 📝 관련 문장")
        word = st.session_state.clicked_word
        brand = st.session_state.clicked_brand

        if word and brand:
            match_ids = morph_df[
                (morph_df["단어"] == word) & (morph_df["그룹"] == brand)
            ]["문장ID"].unique()
            matched = sent_df[sent_df["문장ID"].isin(match_ids) & (sent_df["그룹"] == brand)]
            if not matched.empty:
                row = matched.iloc[0]
                sentence = row["문장"]
                if len(sentence) > 100:
                    sentence = sentence[:100] + "..."
                sentence = sentence.replace(word, f"**🟨{word}**")
                st.markdown(f"🔗 [원문링크]({row['원본링크']})")
                st.markdown(sentence)
            else:
                st.info("❗ 관련 문장이 없습니다.")
        else:
            st.markdown("📌 단어를 선택해 주세요.")

    # ✅ 하단: 긍정 단어 비율 선그래프
    st.divider()
    st.markdown("### 📈 긍정 단어 비율 변화 (예시)")

    # 예시용 데이터 (추후 실제 비율 계산 로직으로 교체 가능)
    fake_ratio = pd.DataFrame({
        "week": ["3월 1주차", "3월 2주차", "3월 3주차"] * 4,
        "brand": sum([[b] * 3 for b in brands], []),
        "positive_ratio": [64, 66, 65, 70, 72, 74, 60, 62, 61, 58, 59, 60],
    })

    fig_line = px.line(
        fake_ratio,
        x="week",
        y="positive_ratio",
        color="brand",
        markers=True,
        labels={"week": "주차", "positive_ratio": "긍정 비율 (%)"},
    )
    fig_line.update_layout(height=400, title="긍정 단어 비율 추이")
    st.plotly_chart(fig_line, use_container_width=True)
