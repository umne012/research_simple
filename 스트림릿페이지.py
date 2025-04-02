import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# ✅ 스타일 제거된 버전 (PDF 버튼 제거됨)
st.markdown("""
<style>
* {
    font-family: 'Pretendard', sans-serif;
}

/* 분석 버튼 */
div.stButton:nth-of-type(1) > button {
    background-color: transparent;
    color: #FA8072;
    padding: 7px 24px;
    border: 1px dashed #FA8072;
    border-radius: 6px;
    font-size: 16px;
    width: 100%;
    cursor: pointer;
    transition: all 0.3s ease;
}
div.stButton:nth-of-type(1) > button:hover {
    background-color: #FA8072;
    color: white;
    border: 1px solid #FA8072;
}
</style>
""", unsafe_allow_html=True)

# ✅ 사이드 메뉴
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=0,
    )

# ✅ 그룹 설정
original_search_groups = [
    {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]
if "search_groups" not in st.session_state:
    st.session_state.search_groups = original_search_groups.copy()
search_groups = st.session_state.search_groups

if selected_tab == "검색트렌드":
    st.title("검색트렌드 분석")

    with st.expander("\U0001F4CB 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(label="검색어", text="엔터로 여러 개 등록", value=group["keywords"], key=f"kw_{group['groupName']}")
            ex_tags = st_tags(label="제외어", text="엔터로 여러 개 등록", value=group["exclude"], key=f"ex_{group['groupName']}")
            group_inputs[group["groupName"]] = {"keywords": kw_tags, "exclude": ex_tags}

        if st.button("\U0001F501 설정 적용", key="apply_button"):
            st.session_state.search_groups = [
                {"groupName": name, "keywords": values["keywords"], "exclude": values["exclude"]}
                for name, values in group_inputs.items()
            ]
            search_groups = st.session_state.search_groups

    today = date.today()
    default_start = today - timedelta(days=7)
    default_end = today

    col1, col2, col3 = st.columns([2.1, 2.1, 1])
    with col1:
        start_date = st.date_input("시작일", value=default_start)
    with col2:
        end_date = st.date_input("종료일", value=default_end)
    with col3:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        run_analysis = st.button("\U0001F50D 분석 시작", key="run_button")
        st.markdown("</div>", unsafe_allow_html=True)

    if run_analysis:
        def get_date_range(start, end):
            return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]

        date_range = get_date_range(start_date, end_date)
        trend_data = {}
        try:
            response = requests.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id": st.secrets["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["NAVER_CLIENT_SECRET"],
                    "Content-Type": "application/json",
                },
                json={
                    "startDate": str(start_date),
                    "endDate": str(end_date),
                    "timeUnit": "date",
                    "keywordGroups": [
                        {"groupName": g["groupName"], "keywords": g["keywords"]} for g in search_groups
                    ],
                },
            )
            if response.ok:
                trend_data = response.json()
                st.session_state.trend_data = trend_data
            else:
                st.error(f"검색 트렌드 오류: {response.status_code}")
        except Exception as e:
            st.error(f"API 요청 실패: {e}")

        mention_data = {"labels": date_range, "datasets": []}
        group_mentions = {g["groupName"]: [] for g in search_groups}

        with st.spinner("\U0001F4F0 뉴스·블로그 언급량 수집 중..."):
            for group in search_groups:
                values = []
                for d in date_range:
                    exclude_query = " ".join([f"-{word}" for word in group.get("exclude", [])])
                    total_mentions = 0
                    for keyword in group["keywords"]:
                        full_query = f"{keyword} {exclude_query} {d}"
                        for endpoint in ["news.json", "blog.json"]:
                            try:
                                res = requests.get(
                                    f"https://openapi.naver.com/v1/search/{endpoint}",
                                    headers={
                                        "X-Naver-Client-Id": st.secrets["NAVER_CLIENT_ID_2"],
                                        "X-Naver-Client-Secret": st.secrets["NAVER_CLIENT_SECRET_2"],
                                    },
                                    params={"query": full_query, "display": 5, "start": 1, "sort": "date"},
                                )
                                if res.ok:
                                    total_mentions += res.json().get("total", 0)
                                    for item in res.json().get("items", []):
                                        group_mentions[group["groupName"]].append({
                                            "title": item["title"].replace("<b>", "").replace("</b>", ""),
                                            "link": item["link"]
                                        })
                            except:
                                pass
                    values.append(total_mentions)
                mention_data["datasets"].append({"label": group["groupName"], "data": values})

        st.session_state.mention_data = mention_data
        st.session_state.group_mentions = group_mentions

    trend_data = st.session_state.get("trend_data", {})
    mention_data = st.session_state.get("mention_data", {})
    group_mentions = st.session_state.get("group_mentions", {})

    if trend_data and mention_data:
        st.subheader("검색량 및 언급량 그래프")
        gcol1, gcol2 = st.columns(2)

        layout = go.Layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            title=dict(x=0.05, font=dict(size=18)),
            margin=dict(l=40, r=40, t=60, b=100),
            xaxis=dict(title="날짜", showgrid=True),
            yaxis=dict(title="값", showgrid=True),
            legend=dict(orientation="h", x=0.5, y=-0.2, xanchor="center", yanchor="top")
        )

        with gcol1:
            fig = go.Figure(layout=layout)
            fig.update_layout(title="네이버 검색량")
            for group in trend_data.get("results", []):
                fig.add_trace(go.Scatter(
                    x=[d["period"] for d in group["data"]],
                    y=[d["ratio"] for d in group["data"]],
                    mode="lines+markers",
                    name=group["title"]
                ))
            st.plotly_chart(fig, use_container_width=True)

        with gcol2:
            fig2 = go.Figure(layout=layout)
            fig2.update_layout(title="뉴스·블로그 언급량")
            for ds in mention_data.get("datasets", []):
                fig2.add_trace(go.Scatter(
                    x=mention_data.get("labels", []),
                    y=ds["data"],
                    mode="lines+markers",
                    name=ds["label"]
                ))
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("실시간 뉴스·블로그 문장 리스트")
        cols = st.columns(4)
        for idx, group in enumerate(search_groups):
            with cols[idx % 4]:
                st.markdown(f"<h4 style='text-align:center; color:#0366d6'>{group['groupName']}</h4>", unsafe_allow_html=True)
                for item in group_mentions.get(group['groupName'], [])[:10]:
                    st.markdown(f'''
                    <div style='border:1px solid #eee; padding:10px; margin-bottom:8px; border-radius:8px; background-color:#fafafa;'>
                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#333; font-weight:500;">
                            \ud83d\udd17 {item['title']}
                        </a>
                    </div>
                    ''', unsafe_allow_html=True)

