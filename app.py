import pandas as pd
from googleapiclient.discovery import build
import streamlit as st

st.set_page_config(page_title="무료 유튜브 주제 분석기", layout="wide")
st.title("📊 무료 유튜브 데이터 분석 도구")

# 사이드바 입력창
api_key = st.sidebar.text_input("YouTube API Key 입력", type="password")
keyword = st.text_input("분석할 주제/키워드 입력", "쇼핑추천")
max_results = st.slider("수집할 영상 개수", 5, 50, 10)


# 1시간(3600초) 동안 동일 키워드 검색 결과를 저장하여 API 호출을 방지합니다.
@st.cache_data(ttl=3600)
def fetch_youtube_data(key: str, query: str, count: int):
    youtube = build("youtube", "v3", developerKey=key)

    search_response = (
        youtube.search()
        .list(
            q=query,
            part="id,snippet",
            maxResults=count,
            type="video",
            order="viewCount",
        )
        .execute()
    )

    video_ids = [
        item["id"]["videoId"] for item in search_response.get("items", [])
    ]
    if not video_ids:
        return pd.DataFrame()

    video_response = (
        youtube.videos()
        .list(id=",".join(video_ids), part="snippet,statistics")
        .execute()
    )

    data = []
    for item in video_response.get("items", []):
        stats = item["statistics"]
        snippet = item["snippet"]
        data.append({
            "제목": snippet["title"],
            "채널명": snippet["channelTitle"],
            "조회수": int(stats.get("viewCount", 0)),
            "좋아요 수": int(stats.get("likeCount", 0)),
            "댓글 수": int(stats.get("commentCount", 0)),
            "게시일": snippet["publishedAt"][:10],
            "URL": f"https://www.youtube.com/watch?v={item['id']}",
        })
    return pd.DataFrame(data)


if st.button("데이터 수집 및 분석 시작"):
    if not api_key:
        st.error("왼쪽 사이드바에 API 키를 입력해 주세요.")
    else:
        try:
            df = fetch_youtube_data(api_key, keyword, max_results)

            if not df.empty:
                st.subheader("📋 분석 결과 (1시간 동안 캐시 저장)")
                st.dataframe(df, use_container_width=True)

                st.subheader("📈 조회수 상위 차트")
                st.bar_chart(data=df, x="제목", y="조회수")
            else:
                st.warning("검색 결과가 없습니다.")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
