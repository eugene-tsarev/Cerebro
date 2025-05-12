import streamlit as st
from datetime import date
from sqlalchemy.orm import Session
from typing import List

from controllers.videos_controller import parse_videos
from db.db_session import get_session
from models.models import Channel, Video


def select_channels(channels: List[Channel]) -> List[str]:
    channel_options = {
        f"{ch.channel_name} ({ch.channel_id})": ch.channel_id
        for ch in channels if ch.channel_name
    }
    selected_labels = st.multiselect(
        "Выберите каналы:", list(channel_options.keys()))
    return [channel_options[label] for label in selected_labels]


def select_date() -> date:
    return st.date_input("Видео не старше даты:", value=date(2024, 1, 1))


def show_parse_button() -> bool:
    return st.button("Запустить парсинг")


def show_results(videos: List[Video]):
    if not videos:
        st.info("Новых видео не найдено по заданным параметрам.")
        return

    st.success(f"Добавлено {len(videos)} новых видео")
    st.dataframe([
        {
            "video_id": v.video_id,
            "title": v.title,
            "published_time": v.published_time,
            "channel_id": v.channel_id,
        }
        for v in videos
    ])


def render():
    st.title("Парсинг видео с YouTube")

    with get_session() as session:
        channels = session.query(Channel).all()

        selected_channels = select_channels(channels)
        published_after = select_date()

        col1, col2 = st.columns(2)

        with col1:
            run_parse = show_parse_button()
        with col2:
            show_existing = st.button("Показать видео")

        if run_parse and selected_channels:
            with st.spinner("Парсинг видео..."):
                new_videos = parse_videos(
                    selected_channels, published_after, session)
            show_results(new_videos)

        if show_existing and selected_channels:
            videos = session.query(Video).filter(
                Video.channel_id.in_(selected_channels),
                Video.published_time >= published_after
            ).all()

            formatted = [
                {
                    "title": v.title,
                    "published_time": v.published_time,
                    "last_parsed_at": v.last_parsed_at if v.last_parsed_at else "новое"
                }
                for v in videos
            ]

            st.subheader("Видео из базы данных")
            st.dataframe(formatted)
