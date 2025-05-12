import os
from datetime import datetime
from typing import List

from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from models.models import Video
from db.db_session import get_session
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def parse_videos(selected_channels: List[str], published_after, session: Session = None) -> List[Video]:
    if session is None:
        session = get_session()

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)
    new_videos = []

    for channel_id in selected_channels:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            publishedAfter=published_after.isoformat() + "T00:00:00Z",
            maxResults=50,
            type="video"
        )

        response = request.execute()

        for item in response.get("items", []):
            video_id = item["id"]["videoId"]

            # Проверка на существование
            exists = session.query(Video).filter_by(video_id=video_id).first()
            if exists:
                continue

            snippet = item["snippet"]

            video = Video(
                video_id=video_id,
                channel_id=channel_id,
                title=snippet.get("title"),
                published_time=datetime.strptime(snippet.get("publishedAt"), "%Y-%m-%dT%H:%M:%SZ"),
                added_at=datetime.utcnow(),
                last_parsed_at=None,
            )

            session.add(video)
            new_videos.append(video)

    session.commit()
    return new_videos
