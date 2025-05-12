import streamlit as st
from datetime import datetime
from db.db_session import get_session
from models.models import Video, Channel
from controllers.parser_controller import save_comments_to_db
from sqlalchemy import and_


def render():
    st.title("🔍 Парсинг комментариев YouTube")

    status_placeholder = st.empty()
    progress_bar = st.empty()
    summary_placeholder = st.empty()
    details_placeholder = st.empty()

    with get_session() as db:
        st.subheader("⚖️ Фильтрация видео")

        col1, col2, col3 = st.columns(3)

        with col1:
            published_from = st.date_input("Опубликованы после", value=None)
            published_to = st.date_input("Опубликованы до", value=None)
        with col2:
            added_from = st.date_input("Добавлены после", value=None)
            added_to = st.date_input("Добавлены до", value=None)
        with col3:
            parsed_from = st.date_input("Последний парсинг после", value=None)
            parsed_to = st.date_input("Последний парсинг до", value=None)

        st.markdown("---")
        col4, col5 = st.columns([1, 2])

        with col4:
            show_unparsed = st.checkbox(
                "📋 Показать только непарсенные видео", value=False)

        with col5:
            start_parsing = st.button("⏰ Запустить парсинг выбранных видео")

        query = db.query(Video)

        if show_unparsed:
            query = query.filter(Video.last_parsed_at.is_(None))
        if published_from:
            query = query.filter(Video.published_time >= published_from)
        if published_to:
            query = query.filter(Video.published_time <= published_to)
        if added_from:
            query = query.filter(Video.added_at >= added_from)
        if added_to:
            query = query.filter(Video.added_at <= added_to)
        if parsed_from:
            query = query.filter(Video.last_parsed_at >= parsed_from)
        if parsed_to:
            query = query.filter(Video.last_parsed_at <= parsed_to)

        videos = query.all()

    if not videos:
        st.warning("Нет видео, подходящих под фильтр.")
        return

    st.subheader(f"📅 Выберите видео для парсинга (Доступно: {len(videos)})")

    video_selection = {}

    select_all = st.checkbox("Выбрать все", value=True)

    with get_session() as db:
        for video in videos:
            channel = db.query(Channel).filter_by(
                channel_id=video.channel_id).first()
            channel_name = channel.channel_name if channel and channel.channel_name else video.channel_id
            video_url = f"https://www.youtube.com/watch?v={video.video_id}"
            display_text = f"[{video.title or video.video_id}]({video_url}) — {channel_name}"
            checked = st.checkbox(
                display_text, value=select_all, key=video.video_id)
            video_selection[video.video_id] = checked

    selected_videos = [vid for vid,
                       selected in video_selection.items() if selected]

    st.markdown(f"**Выбрано {len(selected_videos)} видео**")

    if start_parsing:
        if not selected_videos:
            st.warning("Пожалуйста, выберите хотя бы одно видео.")
            return

        total_comments_added = 0
        total_videos = len(selected_videos)
        comments_per_video = {}

        status_placeholder.info("Запуск парсинга...")
        progress = progress_bar.progress(0)

        with st.spinner("Парсинг комментариев..."):
            with get_session() as db:
                for idx, video_id in enumerate(selected_videos):
                    status_placeholder.info(
                        f"▶️ Обрабатывается видео: {video_id}")

                    added = save_comments_to_db(video_id)
                    total_comments_added += added
                    comments_per_video[video_id] = added

                    db.query(Video).filter_by(video_id=video_id).update(
                        {"last_parsed_at": datetime.utcnow()})
                    db.commit()

                    status_placeholder.success(
                        f"✅ Видео {video_id} обработано. Добавлено комментариев: {added}")
                    progress.progress((idx + 1) / total_videos)

        summary_placeholder.success(
            f"✅ Парсинг завершен. Всего добавлено комментариев: {total_comments_added}")

        with details_placeholder.expander("📈 Детали по каждому видео"):
            for vid, result in comments_per_video.items():
                if isinstance(result, str):
                    st.write(f"Видео {vid}: {result}")
                else:
                    st.write(f"Видео {vid}: {result} комментариев добавлено")
