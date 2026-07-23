import datetime
import re
import html
import pandas as pd
from googleapiclient.discovery import build
import streamlit as st

# 1. 고정 기본 API 키 설정
DEFAULT_API_KEY = "AIzaSyCG8MzQ9rkN6WXGAyWJNP2xN27iHZjZPEg"

# 페이지 기본 설정
st.set_page_config(
    page_title="YouTube Native + High-End Insight Ver 3.0",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. HTML Ver 3.0 전용 다크 테마 및 애니메이션 CSS 적용
st.markdown(
    """
    <style>
    :root {
        --bg-color: #121212;
        --card-bg: #1e1e1e;
        --panel-bg: #252525;
        --text-main: #ffffff;
        --text-sub: #a0a0a0;
        --accent-color: #3ea6ff;
        --border-color: #333;
        --ai-btn-bg: linear-gradient(135deg, #7c3aed, #a855f7);
        
        --lv1-color: #424242;
        --lv2-color: #2e7d32;
        --lv3-color: #1565c0;
        --lv4-color: #6a1b9a;
        --lv5-color: #e65100;
        --lv6-bg: linear-gradient(135deg, #d50000, #ff1744, #ff5252);
    }

    .stApp {
        background-color: var(--bg-color);
        color: var(--text-main);
    }

    /* 카드 그리드 레이아웃 */
    .card-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    .card {
        background: var(--card-bg);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color);
        display: flex;
        flex-direction: column;
        position: relative;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .thumb-box {
        position: relative;
        overflow: hidden;
    }
    .thumb-img {
        width: 100%;
        aspect-ratio: 16/9;
        object-fit: cover;
        transition: 0.3s;
    }
    .card:hover .thumb-img {
        transform: scale(1.05);
    }
    .duration-badge {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(0,0,0,0.85);
        color: #fff;
        padding: 3px 6px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .card-body {
        padding: 16px;
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .card-title {
        font-size: 15px;
        font-weight: 700;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        color: #fff;
        height: 42px;
    }
    .channel-info {
        font-size: 12px;
        color: var(--text-sub);
    }
    .stats-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        background: #111;
        padding: 12px;
        border-radius: 8px;
        font-size: 12px;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
    }
    .stat-val {
        font-weight: 700;
        color: #eee;
    }

    /* 6단계 떡상 지수 배지 */
    .viral-badge {
        text-align: center;
        padding: 6px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 13px;
        color: #fff;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }
    .lv-1 { background: var(--lv1-color); color: #aaa; border: 1px solid #555; }
    .lv-2 { background: var(--lv2-color); }
    .lv-3 { background: var(--lv3-color); }
    .lv-4 { background: var(--lv4-color); }
    .lv-5 { background: var(--lv5-color); }
    .lv-6 { 
        background: var(--lv6-bg); 
        box-shadow: 0 0 15px rgba(255, 23, 68, 0.6); 
        animation: godMode 2s infinite alternate; 
    }
    @keyframes godMode { 
        0% { box-shadow: 0 0 10px rgba(255, 23, 68, 0.6); transform: scale(1); } 
        100% { box-shadow: 0 0 22px rgba(255, 23, 68, 1); transform: scale(1.02); } 
    }
    </style>
""",
    unsafe_allow_html=True,
)


# 유틸리티 함수 정의
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
        return f'<div class="viral-badge lv-2">🌿 우수 ({score:.0f}%)</div>'
    elif score < 1000:
        return f'<div class="viral-badge lv-3">💧 떡상 ({score:.0f}%)</div>'
    elif score < 5000:
        return f'<div class="viral-badge lv-4">🔮 대박 ({score:.0f}%)</div>'
    elif score < 10000:
        return f'<div class="viral-badge lv-5">🦁 초대박 ({score:.0f}%)</div>'
    else:
        return f'<div class="viral-badge lv-6">👑 신의 간택 (100배+) ({score:.0f}%)</div>'


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


# 유튜브 API 수집 함수 (Deep Search 200개 수집)
@st.cache_data(ttl=1800)
def fetch_youtube_v3_data(api_key, keyword, order, duration, pub_after_opt):
    youtube = build("youtube", "v3", developerKey=api_key)
    pub_after = get_published_after_rfc3339(pub_after_opt)

    video_items = []
    next_page_token = None
    pages_fetched = 0
    max_pages = 4  # 50개 * 4페이지 = 최대 200개

    while pages_fetched < max_pages:
        params = {
            "q": keyword,
            "part": "snippet",
            "type": "video",
            "maxResults": 50,
            "regionCode": "KR",
            "order": order,
        }
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

    # 상세 비디오 정보 조회
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

    # 채널 구독자 수 조회
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

    # 데이터 병합 및 떡상 지수 산출
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


# --- Header 영역 ---
st.markdown(
    "<h1>🔥 YouTube Native + Insight V3.0</h1>", unsafe_allow_html=True
)
st.caption("API Level Filtering | Zero Data Loss")

# API Key 수동 설정 확장 영역
with st.expander("🔑 API Key 수동 설정 (기본 키 자동 사용 중)", expanded=False):
    custom_key = st.text_input(
        "수동 API Key 입력",
        type="password",
        help="입력하지 않으면 고정 기본 키가 사용됩니다.",
    )

api_key = custom_key.strip() if custom_key.strip() else DEFAULT_API_KEY

# --- Native Filters 영역 ---
st.markdown("### 🎯 검색 및 서버 필터 설정")
col_f1, col_f2, col_f3 = st.columns(3)

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
        index=0,
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
        index=0,
    )

with col_f3:
    api_order = st.selectbox(
        "🎯 검색 정렬 기준 (API)",
        ["relevance", "viewCount", "date", "rating"],
        format_func=lambda x: {
            "relevance": "관련성 (기본)",
            "viewCount": "👁️ 조회수순 (인기)",
            "date": "📅 최신순 (Date)",
            "rating": "⭐ 평점순",
        }[x],
        index=0,
    )

col_k, col_btn = st.columns([4, 1])
with col_k:
    keyword = st.text_input(
        "메인 키워드 입력", "쇼핑추천", label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🚀 Deep Search (200개)", use_container_width=True)

if search_clicked:
    with st.spinner("유튜브 서버에서 필터링된 데이터를 수집 중입니다..."):
        try:
            raw_data = fetch_youtube_v3_data(
                api_key, keyword, api_order, api_duration, api_date
            )
            st.session_state["raw_data"] = raw_data
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# --- 결과 및 클라이언트 정렬 영역 ---
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
        st.write("")
        st.write(f"**검색 결과:** `{len(data)}개`")

    # 정렬 실행
    is_desc = sort_order.startswith("내림차순")
    if sort_by == "조회수순":
        data = sorted(data, key=lambda x: x["viewCount"], reverse=is_desc)
    elif sort_by == "구독자순":
        data = sorted(data, key=lambda x: x["subCount"], reverse=is_desc)
    elif sort_by == "🔥 떡상지수순":
        data = sorted(data, key=lambda x: x["viralScore"], reverse=is_desc)
    elif sort_by == "최신순":
        data = sorted(data, key=lambda x: x["publishedAt"], reverse=is_desc)

    # HTML 카드 렌더링
    cards_html = '<div class="card-container">'
    for item in data:
        badge = get_viral_badge(item["viralScore"])
        safe_title = html.escape(item["title"])
        safe_ch = html.escape(item["channelTitle"])

        cards_html += f"""
        <div class="card">
            <div class="thumb-box">
                <a href="{item['url']}" target="_blank">
                    <img src="{item['thumbnail']}" class="thumb-img">
                </a>
                <span class="duration-badge">{item['durationStr']}</span>
            </div>
            <div class="card-body">
                <div class="card-title" title="{safe_title}">{safe_title}</div>
                <div class="channel-info">📺 {safe_ch} • {item['publishedDate']}</div>
                {badge}
                <div class="stats-grid">
                    <div class="stat-row"><span>조회수</span><span class="stat-val">{format_num(item['viewCount'])}</span></div>
                    <div class="stat-row"><span>구독자</span><span class="stat-val">{format_num(item['subCount'])}</span></div>
                    <div class="stat-row"><span>기여도</span><span class="stat-val" style="color:#3ea6ff">{item['viralScore']:,.0f}%</span></div>
                </div>
            </div>
        </div>
        """
    cards_html += "</div>"

    st.markdown(cards_html, unsafe_allow_html=True)

    # AI 기획 프롬프트 추출 섹션
    st.markdown("---")
    st.markdown("### 🤖 AI 기획안 프롬프트 추출")

    video_titles = [
        f"[{i+1}] {item['title']} ({item['channelTitle']})"
        for i, item in enumerate(data)
    ]
    selected_idx = st.selectbox("프롬프트를 생성할 영상 선택", range(len(data)), format_func=lambda x: video_titles[x])

    sel_item = data[selected_idx]
    multiplier = (
        sel_item["viralScore"] / 100.0 if sel_item["viralScore"] else 0.0
    )

    ai_prompt = f"""나는 유튜브 크리에이터야. 아래 영상을 벤치마킹해서 기획안을 써줘. (GPT/Gemini)

[대상]
제목: {sel_item['title']}
채널: {sel_item['channelTitle']}
길이: {sel_item['durationStr']}
성과: 구독자 대비 {multiplier:.1f}배 조회수
태그: {sel_item['tags']}

[요청]
1. 클릭을 부른 심리적 트리거 분석
2. 내 주제에 맞춘 썸네일/제목 5개 추천
3. 시청 지속 시간을 위한 대본 구조 설계"""

    st.code(ai_prompt, language="markdown")
    st.caption("우측 상단 복사 버튼을 눌러 ChatGPT 또는 Gemini에 바로 사용할 수 있습니다.")
