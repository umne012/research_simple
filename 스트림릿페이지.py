import streamlit as st
from datetime import date, timedelta
import requests
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_tags import st_tags
import time

st.set_page_config(layout="wide")

# ✅ 전체 폰트 Pretendard 적용
st.markdown("""
    <style>
    * {
        font-family: 'Pretendard', sans-serif;
    }
    .st-emotion-cache-6qob1r {
        font-weight: bold;
    }
    .tag-box {
        background-color: #f1f3f5;
        padding: 8px 12px;
        margin: 4px;
        border-radius: 8px;
        display: inline-block;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ 사이드 네비게이션 메뉴 적용
with st.sidebar:
    selected_tab = option_menu(
        menu_title="research",
        options=["검색트렌드", "연관어 분석", "긍부정 분석"],
        icons=["bar-chart", "graph-up", "emoji-smile"],
        menu_icon="cast",
        default_index=0,
    )

# ✅ 초기 검색 그룹 설정
original_search_groups = [
    {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
    {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
    {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
    {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
]

search_groups = original_search_groups.copy()

if selected_tab == "검색트렌드":
    st.title("검색트렌드 분석")

    # 📅 날짜 입력 (한 줄에 배치)
    col1, col2 = st.columns([1, 1])
    with col1:
        start_date = st.date_input("시작일", value=date(2025, 3, 12))
    with col2:
        end_date = st.date_input("종료일", value=date(2025, 3, 18))

    # 📌 그룹별 검색어/제외어 수정 인터페이스 (태그형 + 적용 버튼)
    with st.expander("📋 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(
                label="검색어",
                text="엔터로 여러 개 등록",
                value=group["keywords"],
                key=f"kw_{group['groupName']}"
            )
            ex_tags = st_tags(
                label="제외어",
                text="엔터로 여러 개 등록",
                value=group["exclude"],
                key=f"ex_{group['groupName']}"
            )
            group_inputs[group["groupName"]] = {
                "keywords": kw_tags,
                "exclude": ex_tags
            }

        if st.button("🔁 설정 적용"):
            search_groups = [
                {
                    "groupName": name,
                    "keywords": values["keywords"],
                    "exclude": values["exclude"]
                }
                for name, values in group_inputs.items()
            ]

    # ✅ 분석 버튼 별도 배치
    if st.button("🔍 검색량 및 언급량 분석 시작"):
        st.session_state["run_analysis"] = True

    if st.session_state.get("run_analysis", False):
        def get_date_range(start, end):
            return [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]

        date_range = get_date_range(start_date, end_date)

        # 검색 트렌드 API 호출
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
            else:
                st.error(f"검색 트렌드 오류: {response.status_code}")
        except Exception as e:
            st.error(f"API 요청 실패: {e}")

        # 언급량 수집 (뉴스+블로그)
        mention_data = {"labels": date_range, "datasets": []}
        group_mentions = {g["groupName"]: [] for g in search_groups}

        with st.spinner("📰 뉴스·블로그 언급량 수집 중..."):
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

        # 그래프 그리기
        st.subheader("검색량 및 언급량 그래프")
        gcol1, gcol2 = st.columns(2)

        plot_layout = go.Layout(
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            title=dict(x=0.05, font=dict(size=18)),
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(title="날짜", showgrid=True),
            yaxis=dict(title="값", showgrid=True),
            legend=dict(orientation="h",x=1, y=-0.2, xanchor="center")
        )

        with gcol1:
            fig = go.Figure(layout=plot_layout)
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
            fig2 = go.Figure(layout=plot_layout)
            fig2.update_layout(title="뉴스·블로그 언급량")
            for ds in mention_data.get("datasets", []):
                fig2.add_trace(go.Scatter(
                    x=mention_data.get("labels", []),
                    y=ds["data"],
                    mode="lines+markers",
                    name=ds["label"]
                ))
            st.plotly_chart(fig2, use_container_width=True)

        # 뉴스·블로그 문장 4열 출력 (스타일 개선)
        st.subheader("실시간 뉴스·블로그 문장 리스트")
        cols = st.columns(4)
        for idx, group in enumerate(search_groups):
            with cols[idx % 4]:
                st.markdown(f"<h4 style='text-align:center; color:#0366d6'>{group['groupName']}</h4>", unsafe_allow_html=True)
                for item in group_mentions[group['groupName']][:10]:
                    st.markdown(f"""
                    <div style='border:1px solid #eee; padding:10px; margin-bottom:8px; border-radius:8px; background-color:#fafafa;'>
                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#333; font-weight:500;">
                            🔗 {item['title']}
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
