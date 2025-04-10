
import streamlit as st
import pandas as pd
import plotly.express as px

# 📁 페이지 기본 설정
st.set_page_config(layout="wide")
st.title("🙂 긍·부정 분석")

# ✅ 주차 선택
available_weeks = ["2024-03-01", "2024-03-08", "2024-03-15", "2024-03-22"]
selected_week = st.selectbox("분석 주차 선택", available_weeks)

brands = ["Skylife", "KT", "LGU+", "SKB"]

# ✅ 클릭 단어 상태 관리
if "clicked_word" not in st.session_state:
    st.session_state.clicked_word = None
if "clicked_brand" not in st.session_state:
    st.session_state.clicked_brand = None

# ✅ 버블차트용 데이터 불러오기
@st.cache_data
def load_bubble_data(brand, week):
    url = f"https://raw.githubusercontent.com/yourusername/yourrepo/main/data/positive_negative/{week}/{brand}_bubble.csv"
    return pd.read_csv(url)

# ✅ 문장 데이터 로딩
@st.cache_data
def load_sentences(week):
    morph_url = f"https://raw.githubusercontent.com/yourusername/yourrepo/main/data/sentences/{week}/morpheme_analysis.csv"
    senti_url = f"https://raw.githubusercontent.com/yourusername/yourrepo/main/data/sentences/{week}/sentiment_analysis.csv"
    morph_df = pd.read_csv(morph_url)
    senti_df = pd.read_csv(senti_url)
    return morph_df, senti_df

morph_df, sent_df = load_sentences(selected_week)

# ✅ 버블차트 2x2 + 오른쪽 문장 패널
chart_cols = st.columns([2, 2, 2, 1.5])  # 마지막 col은 문장 출력용
brand_to_col = dict(zip(brands, chart_cols[:4]))

for brand in brands:
    with brand_to_col[brand]:
        st.markdown(f"#### {brand}")
        df = load_bubble_data(brand, selected_week)

        fig = px.scatter(
            df,
            x="x", y="y",
            size="count",
            color="sentiment",
            color_discrete_map={"positive": "#9370DB", "negative": "#FA8072"},
            hover_name="word",
            size_max=60,
        )
        fig.update_traces(marker=dict(line=dict(width=1, color="black")))
        fig.update_layout(height=600, margin=dict(l=5, r=5, t=40, b=5), showlegend=False)

        # (임시) 단어 선택용
        word = st.selectbox(f"{brand} 단어 선택", df["word"].unique(), key=f"{brand}_word")
        if word:
            st.session_state.clicked_word = word
            st.session_state.clicked_brand = brand

# ✅ 오른쪽 문장 패널
with chart_cols[-1]:
    st.markdown("#### 📄 관련 문장")
    word = st.session_state.clicked_word
    brand = st.session_state.clicked_brand
    if word and brand:
        sentence_ids = morph_df[morph_df["단어"] == word]["문장ID"].unique()
        filtered_sentences = sent_df[sent_df["문장ID"].isin(sentence_ids)]
        if not filtered_sentences.empty:
            row = filtered_sentences.iloc[0]
            snippet = row["문장"]
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            snippet = snippet.replace(word, f"**🟨{word}**")
            st.markdown(f"🔗 [원문링크]({row['링크']})")
            st.markdown(snippet)
        else:
            st.markdown("문장을 찾을 수 없습니다.")
    else:
        st.markdown("단어를 선택해 주세요.")

# ✅ 하단: 긍정 단어 비율 변화 선그래프
st.divider()
st.subheader("📈 긍정 단어 비율 비교")

# 예시용: 4개 그룹의 긍정 비율 (실제 데이터로 대체 필요)
@st.cache_data
def load_positive_ratio():
    # 아래는 예시용 데이터프레임
    data = {
        "week": ["2024-03-01", "2024-03-08", "2024-03-15", "2024-03-22"] * 4,
        "brand": sum([[b] * 4 for b in brands], []),
        "positive_ratio": [58, 62, 60, 65, 70, 72, 74, 73, 66, 68, 70, 72, 55, 58, 60, 62],
    }
    return pd.DataFrame(data)

ratio_df = load_positive_ratio()
fig_line = px.line(
    ratio_df,
    x="week",
    y="positive_ratio",
    color="brand",
    markers=True,
    title="긍정 단어 비율 (%)",
    labels={"week": "주차", "positive_ratio": "긍정 비율 (%)"},
)
fig_line.update_layout(height=400)
st.plotly_chart(fig_line, use_container_width=True)
