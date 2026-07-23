import datetime
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st

# 기본 API 키 설정
DEFAULT_API_KEY = "AIzaSyCG8MzQ9rkN6WXGAyWJNP2xN27iHZjZPEg"

# 웹페이지 기본 레이아웃 및 제목 설정
st.set_page_config(
    page_title="유튜브 딥 서치 & 떡상지수 분석기", layout="wide"
)

# 8. 다크 모드 커스텀 CSS 적용
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stTextInput input, .stSelectbox select {
        background-color: #1a1c23 !important;
        color: #ffffff !important;
    }
    .stDataFrame {
        border: 1px solid #2d3139;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🔥 유튜브 딥 서치 & 떡상 지수 분석 도구")

# 1. API 키 설정 (기본값 자동 적용 및 수동 입력 탭)
with st.sidebar:
    st.header("⚙️ 설정 및 필터")
    with st.expander("🔑 API Key 수동 설정", expanded=False):
        custom_key = st.text_input(
            "수동 API Key 입력",
            type="password",
            help="입력하지 않으면 기본 키가 사용됩니다.",
        )

    api_key = custom_key.strip() if custom_key.strip() else DEFAULT_API_KEY

    # 2. 서버 단계 검색 필터 설정
    st.subheader("🎯 검색 필터")
    order_opt = st.selectbox(
        "정렬 방식 (order)",
        ["viewCount", "date", "relevance", "rating"],
        index=0,
    )
    duration_opt = st.selectbox(
        "영상 길이 (videoDuration)",
        ["any", "short", "medium", "long"],
        index=0,
    )
    period_opt = st.selectbox(
        "게시 기간 (publishedAfter)",
        ["전체", "최근 7일", "최근 30일", "최근 1년"],
        index=0,
    )

    # 3. Deep Search 수집 수량 설정 (최대 200개)
    target_count = st.slider(
        "수집 영상 수량 (Deep Search)", 10, 200, 50, step=10
    )


# 게시 기간 날짜 변환 함수
def get_published_after_date(period_str):
    if period_str == "전체":
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    if period_str == "최근 7일":
        delta = datetime.timedelta(days=7)
    elif period_str == "최근 30일":
        delta = datetime.timedelta(days=30)
    elif period_str == "최근 1년":
        delta = datetime.timedelta(days=365)
    else:
        return None
    return (now - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


# 유튜브 API 수집 함수
@st.cache_data(ttl=1800)
def fetch_youtube_deep_data(
    key, query, order, duration, pub_after, total_target
):
    youtube = build("youtube", "v3", developerKey=key)

    video_items = []
    next_page_token = None

    # 3. Deep Search 페이지네이션 루프
    while len(video_items) < total_target:
        fetch_limit = min(50, total_target - len(video_items))

        req_params = {
            "q": query,
            "part": "id,snippet",
            "maxResults": fetch_limit,
            "type": "video",
            "order": order,
        }
        if duration != "any":
            req_params["videoDuration"] = duration
        if pub_after:
            req_params["publishedAfter"] = pub_after
        if next_page_token:
            req_params["pageToken"] = next_page_token

        search_res = youtube.search().list(**req_params).execute()
        items = search_res.get("items", [])
        video_items.extend(items)

        next_page_token = search_res.get("nextPageToken")
        if not next_page_token or not items:
            break

    if not video_items:
        return pd.DataFrame()

    # 비디오 상세 정보 조회 (조회수, 좋아요 수)
    v_ids = [
        item["id"]["videoId"]
        for item in video_items
        if "videoId" in item["id"]
    ]
    video_details = []
    channel_ids = set()

    for i in range(0, len(v_ids), 50):
        chunk = v_ids[i : i + 50]
        v_res = (
            youtube.videos()
            .list(id=",".join(chunk), part="snippet,statistics")
            .execute()
        )
        for item in v_res.get("items", []):
            video_details.append(item)
            channel_ids.add(item["snippet"]["channelId"])

    # 채널 정보 조회 (구독자 수)
    channel_sub_map = {}
    ch_list = list(channel_ids)
    for i in range(0, len(ch_list), 50):
        c_chunk = ch_list[i : i + 50]
        c_res = (
            youtube.channels()
            .list(id=",".join(c_chunk), part="statistics")
            .execute()
        )
        for c_item in c_res.get("items", []):
            sub_cnt = int(c_item["statistics"].get("subscriberCount", 0))
            channel_sub_map[c_item["id"]] = sub_cnt

    # 5. 떡상 지수 산출 및 데이터 정리
    parsed_data = []
    for v in video_details:
        stats = v.get("statistics", {})
        snip = v.get("snippet", {})
        v_id = v["id"]
        c_id = snip.get("channelId")

        views = int(stats.get("viewCount", 0))
        subs = channel_sub_map.get(c_id, 0)

        # Viral Score = (조회수 / 구독자수) * 100
        if subs > 0:
            viral_score = round((views / subs) * 100, 1)
        else:
            viral_score = 0.0

        # 10000% 이상 붉은색 불꽃 배지 표기
        badge = "🔥 " if viral_score >= 10000 else ""

        parsed_data.append({
            "배지": badge,
            "제목": snip.get("title", ""),
            "채널명": snip.get("channelTitle", ""),
            "조회수": views,
            "구독자수": subs,
            "떡상지수(%)": viral_score,
            "좋아요 수": int(stats.get("likeCount", 0)),
            "게시일": snip.get("publishedAt", "")[:10],
            "URL": f"https://www.youtube.com/watch?v={v_id}",
        })

    return pd.DataFrame(parsed_data)


# 메인 검색 영역
keyword = st.text_input("분석할 주제/키워드를 입력하세요", "쇼핑추천")

if st.button("🚀 Deep Search 수집 및 분석 시작"):
    pub_after_val = get_published_after_date(period_opt)
    with st.spinner("데이터 수집 및 채널 분석 진행 중..."):
        try:
            df_result = fetch_youtube_deep_data(
                api_key,
                keyword,
                order_opt,
                duration_opt,
                pub_after_val,
                target_count,
            )
            st.session_state["search_data"] = df_result
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# 6. 결과 정렬 및 출력
if "search_data" in st.session_state and not st.session_state[
    "search_data"
].empty:
    df = st.session_state["search_data"]

    st.subheader("📊 데이터 분석 결과")

    sort_metric = st.selectbox(
        "결과 재정렬 기준", ["조회수", "구독자수", "떡상지수(%)"], index=0
    )
    df_sorted = df.sort_values(by=sort_metric, ascending=False).reset_index(
        drop=True
    )

    st.dataframe(df_sorted, use_container_width=True)

    # 7. AI 기획 프롬프트 복사 기능
    st.subheader("💡 AI 기획 프롬프트 생성")
    selected_num = st.number_input(
        "프롬프트를 추출할 영상 순위 번호 (0부터 시작)",
        min_value=0,
        max_value=len(df_sorted) - 1,
        value=0,
        step=1,
    )

    target_video = df_sorted.iloc[selected_num]
    prompt_content = f"""다음 유튜브 영상의 성공 요인을 분석하고 숏폼 스크립트를 기획해줘.

- 영상 제목: {target_video['제목']}
- 채널명: {target_video['채널명']}
- 조회수: {target_video['조회수']:,}회 / 구독자수: {target_video['구독자수']:,}명
- 떡상지수: {target_video['떡상지수(%)']:,}%
- 영상 링크: {target_video['URL']}

[요청 사항]
1. 이 영상의 주요 흥행 요소 및 훅(Hook) 포인트 분석
2. 동일한 셀링 포인트를 활용한 30초 숏폼 기획안 작성 (대사 및 연출 포함)"""

    st.markdown(
        f"**선택된 영상:** `{target_video['제목']}` ({target_video['채널명']})"
    )
    st.code(prompt_content, language="markdown")
    st.caption("코드 상자 우측 상단의 복사 버튼을 누르면 즉시 복사됩니다.")
