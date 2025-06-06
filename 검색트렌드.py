import streamlit as st
import requests
from datetime import date, timedelta
import plotly.graph_objects as go
from streamlit_tags import st_tags


def show_trend_tab():
    # ✅ 전체 스타일 적용
    st.markdown("""
        <style>
        * {
            font-family: 'Pretendard', sans-serif;

        }

        /* 🔍 분석 버튼 (붉은 강조) - 첫 번째 st.button */
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

        /* 📄 PDF 저장 버튼 (hover 초록 강조) */
        button.pdf-btn {
            background-color: transparent;
            color: #4CAF50;
            padding: 7px 24px;
            border: 1px dashed #4CAF50;
            border-radius: 6px;
            font-size: 16px;
            width: 100%;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button.pdf-btn:hover {
            background-color: #4CAF50;
            color: white;
            border: 1px solid #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("검색트렌드 분석")

    # 나머지 코드는 그대로 유지
    # ✅ 초기 그룹 상태 유지
    original_search_groups = [
        {"groupName": "Skylife", "keywords": ["스카이라이프", "skylife"], "exclude": []},
        {"groupName": "KT", "keywords": ["KT", "케이티", "기가지니", "지니티비"], "exclude": ["SKT", "M 모바일"]},
        {"groupName": "SKB", "keywords": ["skb", "브로드밴드", "btv", "비티비", "b티비"], "exclude": []},
        {"groupName": "LGU", "keywords": ["LGU+", "유플러스", "유플"], "exclude": []},
    ]
    if "search_groups" not in st.session_state:
        st.session_state.search_groups = original_search_groups.copy()

    search_groups = st.session_state.search_groups
    
    # ✅ 검색어/제외어 설정
    with st.expander("📋 그룹별 검색어/제외어 설정", expanded=False):
        group_inputs = {}
        for group in original_search_groups:
            st.markdown(f"<h5 style='color: #333;'>{group['groupName']}</h5>", unsafe_allow_html=True)
            kw_tags = st_tags(label="검색어", text="엔터로 여러 개 등록", value=group["keywords"], key=f"kw_{group['groupName']}")
            ex_tags = st_tags(label="제외어", text="엔터로 여러 개 등록", value=group["exclude"], key=f"ex_{group['groupName']}")
            group_inputs[group["groupName"]] = {"keywords": kw_tags, "exclude": ex_tags}

        if st.button("🔁 설정 적용", key="apply_button"):
            st.session_state.search_groups = [
                {"groupName": name, "keywords": values["keywords"], "exclude": values["exclude"]}
                for name, values in group_inputs.items()
            ]
            search_groups = st.session_state.search_groups

    # ✅ 날짜 선택 (기본값: 어제 ~ 7일 전)
    today = date.today()
    default_end = today - timedelta(days=1)  # 어제
    default_start = default_end - timedelta(days=7)
    
    col1, col2, col3, col4 = st.columns([2.1, 2.1, 1, 1])
    with col1:
        start_date = st.date_input("시작일", value=default_start)
    with col2:
        end_date = st.date_input("종료일", value=default_end)

    # ✅ 분석 시작 버튼 → rerun 없이 바로 실행
    with col3:
        st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
        run_analysis = st.button("🔍 분석 시작", key="run_button")
        st.markdown("</div>", unsafe_allow_html=True)

    # ✅ Excel 저장 버튼 (스타일 유지 + 기능 연결)
    import io
    import pandas as pd
    import base64

    with col4:
        if "trend_data" in st.session_state and "mention_data" in st.session_state and "group_mentions" in st.session_state:
            trend_data = st.session_state["trend_data"]
            mention_data = st.session_state["mention_data"]
            group_mentions = st.session_state["group_mentions"]

            # 1. 검색량 데이터
            trend_df = pd.DataFrame()
            for group in trend_data.get("results", []):
                df = pd.DataFrame(group["data"])
                df["group"] = group["title"]
                trend_df = pd.concat([trend_df, df])
            trend_df = trend_df.rename(columns={"period": "날짜", "ratio": "검색비율"})

            # 2. 언급량 데이터
            mention_df = pd.DataFrame(mention_data["labels"], columns=["날짜"])
            for dataset in mention_data["datasets"]:
                mention_df[dataset["label"]] = dataset["data"]

            # 3. 뉴스·블로그 문장 리스트
            mention_list = []
            for group, articles in group_mentions.items():
                for item in articles:
                    mention_list.append({
                        "그룹명": group,
                        "제목": item["title"],
                        "링크": item["link"]
                    })
            mention_detail_df = pd.DataFrame(mention_list)

            # 4. 엑셀 파일로 저장
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                trend_df.to_excel(writer, index=False, sheet_name="검색량 데이터")
                mention_df.to_excel(writer, index=False, sheet_name="언급량 데이터")
                mention_detail_df.to_excel(writer, index=False, sheet_name="뉴스_블로그_문장")
            output.seek(0)
            b64 = base64.b64encode(output.read()).decode()
            href = f"""
                <div style='padding-top: 28px;'>
                    <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"
                       download="검색트렌드_분석결과.xlsx">
                        <button class="pdf-btn">📄 Excel 저장</button>
                    </a>
                </div>
            """
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style='padding-top: 28px;'>
                    <button class="pdf-btn" disabled>📄 Excel 저장</button>
                </div>
            """, unsafe_allow_html=True)



    # ✅ run_analysis 클릭 시 분석 수행
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
                    "endDate": str(end_date + timedelta(days=1)),  # ✅ 하루 추가
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

        st.session_state.mention_data = mention_data
        st.session_state.group_mentions = group_mentions
        
        
        import io
        import pandas as pd
        
        if download_excel:
            # 1. 검색량 데이터 정리
            trend_df = pd.DataFrame()
            for group in trend_data.get("results", []):
                df = pd.DataFrame(group["data"])
                df["group"] = group["title"]
                trend_df = pd.concat([trend_df, df])
        
            trend_df = trend_df.rename(columns={"period": "날짜", "ratio": "검색비율"})
        
            # 2. 언급량 데이터 정리
            mention_df = pd.DataFrame(mention_data["labels"], columns=["날짜"])
            for dataset in mention_data["datasets"]:
                mention_df[dataset["label"]] = dataset["data"]
        
            # 3. 문장 데이터 정리
            mention_list = []
            for group, articles in group_mentions.items():
                for item in articles:
                    mention_list.append({
                        "그룹명": group,
                        "제목": item["title"],
                        "링크": item["link"]
                    })
            mention_detail_df = pd.DataFrame(mention_list)
        
            # 4. 엑셀로 저장
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                trend_df.to_excel(writer, index=False, sheet_name="검색량 데이터")
                mention_df.to_excel(writer, index=False, sheet_name="언급량 데이터")
                mention_detail_df.to_excel(writer, index=False, sheet_name="뉴스_블로그_문장")
        
            output.seek(0)
            st.download_excel(
                label="📥 엑셀 다운로드",
                data=output,
                file_name="검색트렌드_분석결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    
    # ✅ 시각화
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
            legend=dict(
                orientation="h",
                x=0.5,
                y=-0.2,
                xanchor="center",
                yanchor="top"
            )
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
                            🔗 {item['title']}
                        </a>
                    </div>
                    ''', unsafe_allow_html=True)
