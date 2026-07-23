import datetime
import html
import re
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st

# 1. 고정 기본 API 키 설정
DEFAULT_API_KEY = "AIzaSyCG8MzQ9rkN6WXGAyWJNP2xN27iHZjZPEg"

st.set_page_config(
    page_title="YouTube Native + Insight V3.0",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. UI 가독성 보정 및 고대비 다크 테마 CSS
st.markdown(
    """
    <style>
    :root {
        --bg-color: #0f1117;
        --card-bg: #1a1d24;
        --panel-bg: #222630;
        --text-main: #ffffff;
        --text-sub: #b0b8c4;
        --accent-color: #3ea6ff;
        --border-color: #2f3542;
    }

    .stApp {
        background-color: var(--bg-color);
        color: var(--text-main);
    }

    /* 상단 헤더 영역 가독성 보정 */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }
    header[data-testid="stHeader"] * {
        color: #ffffff !important;
    }

    /* Streamlit 입력 폼 및 필터 드롭다운 글자색 보정 */
    .stWidgetLabel, p, .stCaption {
        color: #ffffff !important;
    }
    div[data-baseweb="input"] input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #3ea6ff !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #3ea6ff !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] * {
        color: #000000 !important;
    }
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
    div[data-baseweb="popover"] * {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    ul[role="listbox"] li {
        color: #000000 !important;
    }

    /* Deep Search 버튼 UI 가독성 개선 */
    div.stButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border-radius: 6px !important;
        height: 42px !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
        border-color: #60a5fa !important;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.6) !important;
    }

    /* 개별 카드 디자인 */
    .card {
        background: var(--card-bg);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
        display: flex;
        flex-direction: column;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 5px;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.6);
    }
    .thumb-box {
        position: relative;
        overflow: hidden;
    }
    .thumb-img {
        width: 100%;
        aspect-ratio: 16/9;
        object-fit: cover;
        display: block;
    }
    .duration-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0, 0, 0, 0.85);
        color: #ffffff !important;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .card-body {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .card-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: #ffffff !important;
        height: 40px;
    }
    .channel-info {
        font-size: 12px;
        color: var(--text-sub) !important;
    }
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        background: #11141a;
        padding: 10px;
        border-radius: 8px;
        font-size: 12px;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
    }
    .stat-val {
        font-weight: 700;
        color: #ffffff !important;
    }

    /* 6단계 떡상 지수 배지 */
    .viral-badge {
        text-align: center;
        padding: 6px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 12px;
        color: #ffffff !important;
    }
    .lv-1 { background: #383d48; color: #ccc !important; }
    .lv-2 { background: #1b5e20; }
    .lv-3 { background: #0d47a1; }
    .lv-4 { background: #4a148c; }
    .lv-5 { background: #e65100; }
    .lv-6 { 
        background: linear-gradient(135deg, #d50000, #ff1744, #ff5252); 
        box-shadow: 0 0 12px rgba(255, 23, 68, 0.8); 
    }
    
    /* Expander 및 st.code 프롬프트 박스 가독성 스타일 지정 */
    div[data-testid="stExpander"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] summary p {
        color: #a855f7 !important;
        font-weight: 700 !important;
        font-size: 13px !important;
    }
    div[data-testid="stCodeBlock"] {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
    }
    div[data-testid="stCodeBlock"] * {
        color: #58a6ff !important;
        background-color: transparent !important;
        font-family: monospace !important;
        font-size: 12px !important;
        line-height: 1.5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_duration(d_str):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d_str or "")
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s


def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_num(n):
    if n >= 1000000:
        return f"{n/1000000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def get_viral_badge(score):
    if score < 100:
        return f'<div class="viral-badge lv-1">🏳️ 일반 ({score:.0f}%)</div>'
    elif score < 500:
        return f'<div class="viral-badge lv-2">🌿 양호 ({score:.0f}%)</div>'
    elif score < 1000:
        return f'<div class="viral-badge lv-3">💧 떡상 ({score:.0f}%)</div>'
    elif score < 5000:
        return f'<div class="viral-badge lv-4">🔮 대박 ({score:.0f}%)</div>'
    elif score < 10000:
        return f'<div class="viral-badge lv-5">🦁 초대박 ({score:.0f}%)</div>'
    else:
        return f'<div class="viral-badge lv-6">👑 신의 간택 ({score:.0f}%)</div>'


def get_published_after_rfc3339(option):
    if option == "all":
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    if option == "1h":
        delta = datetime.timedelta(hours=1)
    elif option == "24h":
        delta = datetime.timedelta(hours=24)
    elif option == "7d":
        delta = datetime.timedelta(days=7)
    elif option == "30d":
        delta = datetime.timedelta(days=30)
    elif option == "1y":
        delta = datetime.timedelta(days=365)
    else:
        return None
    return (now - delta).strftime("%Y-%m-%dT%H:%M:%SZ")


@st.cache_data(ttl=1800)
def fetch_youtube_v3_data(
    api_key, keyword, order, duration, pub_after_opt, region_opt
):
    youtube = build("youtube", "v3", developerKey=api_key)
    pub_after = get_published_after_rfc3339(pub_after_opt)

    video_items = []
    next_page_token = None
    pages_fetched = 0
    max_pages = 4

    while pages_fetched < max_pages:
        params = {
            "q": keyword,
            "part": "snippet",
            "type": "video",
            "maxResults": 50,
            "order": order,
        }
        # 지역 선택 파라미터 처리 (KR선택 시에만 regionCode 추가)
        if region_opt == "KR":
            params["regionCode"] = "KR"
        if duration != "any":
            params["videoDuration"] = duration
        if pub_after:
            params["publishedAfter"] = pub_after
        if next_page_token:
            params["pageToken"] = next_page_token

        res = youtube.search().list(**params).execute()
        items = res.get("items", [])
        if not items:
            break

        video_items.extend(items)
        next_page_token = res.get("nextPageToken")
        pages_fetched += 1
        if not next_page_token:
            break

    if not video_items:
        return []

    video_ids = [
        item["id"]["videoId"]
        for item in video_items
        if "videoId" in item["id"]
    ]
    video_details_map = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        v_res = (
            youtube.videos()
            .list(
                id=",".join(chunk), part="snippet,contentDetails,statistics"
            )
            .execute()
        )
        for item in v_res.get("items", []):
            video_details_map[item["id"]] = item

    channel_ids = list(
        set(
            item["snippet"]["channelId"]
            for item in video_items
            if "snippet" in item
        )
    )
    channel_map = {}

    for i in range(0, len(channel_ids), 50):
        chunk = channel_ids[i : i + 50]
        c_res = (
            youtube.channels()
            .list(id=",".join(chunk), part="statistics")
            .execute()
        )
        for c_item in c_res.get("items", []):
            subs = int(c_item["statistics"].get("subscriberCount", 0))
            channel_map[c_item["id"]] = subs if subs > 0 else 1

    results = []
    for item in video_items:
        v_id = item["id"].get("videoId")
        if not v_id or v_id not in video_details_map:
            continue
        v_detail = video_details_map[v_id]
        snip = item["snippet"]

        sub_count = channel_map.get(snip.get("channelId"), 1)
        view_count = int(v_detail.get("statistics", {}).get("viewCount", 0))
        viral_score = (
            (view_count / sub_count) * 100 if sub_count > 0 else 0.0
        )

        dur_sec = parse_duration(
            v_detail.get("contentDetails", {}).get("duration", "")
        )
        dur_str = format_duration(dur_sec)

        tags_list = v_detail.get("snippet", {}).get("tags", [])
        tags_str = ", ".join(tags_list) if tags_list else "없음"

        thumbnails = snip.get("thumbnails", {})
        thumb_url = (
            thumbnails.get("high", {}).get("url")
            or thumbnails.get("medium", {}).get("url")
            or ""
        )

        pub_date = snip.get("publishedAt", "")[:10]

        results.append({
            "id": v_id,
            "title": snip.get("title", ""),
            "channelTitle": snip.get("channelTitle", ""),
            "publishedAt": snip.get("publishedAt", ""),
            "publishedDate": pub_date,
            "thumbnail": thumb_url,
            "viewCount": view_count,
            "subCount": sub_count,
            "viralScore": viral_score,
            "durationStr": dur_str,
            "url": f"https://www.youtube.com/watch?v={v_id}",
            "tags": tags_str,
        })
    return results


# Header
st.title("🔥 YouTube Native + Insight V3.0")
st.caption("API Level Filtering | Zero Data Loss")

with st.expander("🔑 API Key 수동 설정 (기본 키 자동 적용 중)", expanded=False):
    custom_key = st.text_input("수동 API Key 입력", type="password")

api_key = custom_key.strip() if custom_key.strip() else DEFAULT_API_KEY

# Filters
st.subheader("🎯 검색 및 서버 필터 설정")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    api_date = st.selectbox(
        "📅 업로드 날짜 (API)",
        ["all", "1h", "24h", "7d", "30d", "1y"],
        format_func=lambda x: {
            "all": "전체 (All time)",
            "1h": "지난 1시간",
            "24h": "오늘 (24시간)",
            "7d": "이번 주 (7일)",
            "30d": "이번 달 (30일)",
            "1y": "올해 (1년)",
        }[x],
    )

with col_f2:
    api_duration = st.selectbox(
        "⏱️ 영상 길이 (API)",
        ["any", "short", "medium", "long"],
        format_func=lambda x: {
            "any": "전체 길이",
            "short": "4분 미만 (Short)",
            "medium": "4분 ~ 20분 (Medium)",
            "long": "20분 초과 (Long)",
        }[x],
    )

with col_f3:
    api_order = st.selectbox(
        "🎯 검색 정렬 기준 (API)",
        ["relevance", "viewCount", "date", "rating"],
        format_func=lambda x: {
            "relevance": "관련성 (기본)",
            "viewCount": "👁️ 조회수순",
            "date": "📅 최신순",
            "rating": "⭐ 평점순",
        }[x],
    )

with col_f4:
    api_region = st.selectbox(
        "🌐 국가/지역 필터 (API)",
        ["KR", "ALL"],
        format_func=lambda x: {
            "KR": "🇰🇷 한국 (KR)",
            "ALL": "🌐 전세계 (Global)",
        }[x],
        index=0,
    )

col_k, col_btn = st.columns([4, 1])
with col_k:
    keyword = st.text_input(
        "검색 키워드 입력", "쇼핑추천", label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🚀 Deep Search (200개)", use_container_width=True)

if search_clicked:
    with st.spinner("데이터 수집 중..."):
        try:
            raw_data = fetch_youtube_v3_data(
                api_key, keyword, api_order, api_duration, api_date, api_region
            )
            st.session_state["raw_data"] = raw_data
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# Display Results
if "raw_data" in st.session_state and st.session_state["raw_data"]:
    data = st.session_state["raw_data"]

    st.markdown("---")
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])

    with col_s1:
        sort_by = st.radio(
            "결과 재정렬",
            ["조회수순", "구독자순", "🔥 떡상지수순", "최신순"],
            horizontal=True,
        )
    with col_s2:
        sort_order = st.radio("정렬 순서", ["내림차순 (⬇️)", "오름차순 (⬆️)"], horizontal=True)
    with col_s3:
        st.write(f"**검색 결과:** `{len(data)}개`")

    is_desc = sort_order.startswith("내림차순")
    if sort_by == "조회수순":
        data = sorted(data, key=lambda x: x["viewCount"], reverse=is_desc)
    elif sort_by == "구독자순":
        data = sorted(data, key=lambda x: x["subCount"], reverse=is_desc)
    elif sort_by == "🔥 떡상지수순":
        data = sorted(data, key=lambda x: x["viralScore"], reverse=is_desc)
    elif sort_by == "최신순":
        data = sorted(data, key=lambda x: x["publishedAt"], reverse=is_desc)

    num_cols = 4
    for i in range(0, len(data), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(data):
                item = data[i + j]
                with cols[j]:
                    badge = get_viral_badge(item["viralScore"])
                    safe_title = html.escape(item["title"])
                    safe_ch = html.escape(item["channelTitle"])
                    multiplier = (
                        item["viralScore"] / 100.0 if item["viralScore"] else 0.0
                    )

                    prompt_text = (
                        f"너는 조회수 천만을 넘기는 최고의 유튜브 크리에이터야. 아래 영상을 벤치마킹해서 한국인 20대 미모의 여자 주인, 양쪽 귀만 커피색 털의 흰색 강아지, 왼쪽 눈은 파란색, 오른쪽 눈은 주황색의 오드아이와 모든 발끝이 흰색 털인 회색 새끼 고양이를 주인공으로 기획안을 써줘. (GPT/Gemini)\n\n"
                        f"[대상]\n"
                        f"제목: {item['title']}\n"
                        f"채널: {item['channelTitle']}\n"
                        f"길이: {item['durationStr']}\n"
                        f"성과: 구독자 대비 {multiplier:.1f}배 조회수\n"
                        f"태그: {item['tags']}\n\n"
                        f"[요청]\n"
                        f"1. 클릭을 부른 심리적 트리거 분석\n"
                        f"2. 내 주제에 맞춘 썸네일/제목 5개 추천\n"
                        f"3. 시청 지속 시간을 위한 대본 구조 설계"
                    )

                    card_html = (
                        f'<div class="card">'
                        f'<div class="thumb-box">'
                        f'<a href="{item["url"]}" target="_blank"><img src="{item["thumbnail"]}" class="thumb-img"></a>'
                        f'<span class="duration-badge">{item["durationStr"]}</span>'
                        f'</div>'
                        f'<div class="card-body">'
                        f'<div class="card-title" title="{safe_title}">{safe_title}</div>'
                        f'<div class="channel-info">📺 {safe_ch} • {item["publishedDate"]}</div>'
                        f'{badge}'
                        f'<div class="stats-grid">'
                        f'<div class="stat-row"><span>조회수</span><span class="stat-val">{format_num(item["viewCount"])}</span></div>'
                        f'<div class="stat-row"><span>구독자</span><span class="stat-val">{format_num(item["subCount"])}</span></div>'
                        f'<div class="stat-row"><span>기여도</span><span class="stat-val" style="color:#3ea6ff">{item["viralScore"]:,.0f}%</span></div>'
                        f'</div>'
                        f'</div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

                    with st.expander("🤖 AI 기획안 추출 (우측 상단 클릭 시 복사)"):
                        st.code(prompt_text, language="markdown")
