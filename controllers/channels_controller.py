from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.models import Channel
from db.db_session import get_session, Base
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- YouTube API fetch ---
def fetch_channel_info_from_url(url: str) -> Dict[str, Any]:
    """
    Получение информации о канале YouTube по URL с @handle.
    Использует поиск через YouTube Data API v3.
    """
    if not url.startswith("https://www.youtube.com/@"):
        raise ValueError("URL должен начинаться с https://www.youtube.com/@")

    handle = url.split("@")[-1].split("/")[0]

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    search_response = youtube.search().list(
        q=f"@{handle}",
        type="channel",
        part="id,snippet",
        maxResults=1
    ).execute()

    if not search_response.get("items"):
        raise ValueError("Канал не найден по указанному handle")

    item = search_response["items"][0]
    channel_id = item["snippet"]["channelId"]
    channel_name = item["snippet"]["title"]

    # Получаем дополнительную инфу о канале
    channel_response = youtube.channels().list(
        id=channel_id,
        part="snippet"
    ).execute()

    published_at = channel_response["items"][0]["snippet"].get("publishedAt", datetime.now().isoformat())

    return {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "created_at": datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    }

# --- Controllers ---
def add_channel_from_url(url: str) -> bool:
    try:
        channel_data = fetch_channel_info_from_url(url)
        with get_session() as db:
            # Проверка на дубликаты
            exists = db.query(Channel).filter_by(channel_id=channel_data["channel_id"]).first()
            if exists:
                return False

            new_channel = Channel(
                channel_id=channel_data["channel_id"],
                channel_name=channel_data["channel_name"],
                created_at=channel_data["created_at"]
            )
            db.add(new_channel)
            db.commit()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении канала: {e}")
        return False

def get_all_channels() -> List[Channel]:
    with get_session() as db:
        return db.query(Channel).order_by(Channel.created_at.desc()).all()

def delete_channels(channel_ids: List[str]) -> None:
    with get_session() as db:
        db.query(Channel).filter(Channel.channel_id.in_(channel_ids)).delete(synchronize_session=False)
        db.commit()
