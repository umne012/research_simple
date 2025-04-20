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

    # ✅ 긍정 비율 시간 변화 선그래프
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
