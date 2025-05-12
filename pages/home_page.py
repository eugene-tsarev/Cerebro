"""
Каркас модуля home_page для Streamlit-приложения.

Теперь весь код перенесён в **pages/home_page.py**, разделение на views/pages убрано.
Контроллер переименован в **controllers/home_controller.py**.
"""

# ============================================================================
# controllers/home_controller.py
# ============================================================================
"""Контроллер домашней страницы — использует get_session()."""

import streamlit as st
import os
from db.db_session import get_session
from sqlalchemy import func, select
from controllers import home_controller as ctrl
from models.models import (
    Comment,
    Channel,
    Video,
    SearchQuery,
    MatchedComment,
)
import platform
import signal


def _aggregate_counts(session):
    """Возвращает все KPI — по одному SQL-запросу на метрику."""
    total_comments = session.scalar(select(func.count(Comment.id)))
    total_videos = session.scalar(select(func.count(Video.id)))
    total_channels = session.scalar(select(func.count(Channel.id)))
    total_queries = session.scalar(select(func.count(SearchQuery.id)))
    total_matches = session.scalar(select(func.count(MatchedComment.id)))
    latest_comment_date = session.scalar(
        select(func.max(Comment.published_time)))

    return (
        total_comments,
        total_videos,
        total_channels,
        total_queries,
        total_matches,
        latest_comment_date,
    )


def get_global_stats():
    """Агрегирует показатели для дашборда."""
    with get_session() as session:
        return dict(zip(
            ["total_comments", "total_videos", "total_channels",
             "total_queries", "total_matches", "latest_comment_date"],
            _aggregate_counts(session)
        ))

# ============================================================================
# pages/home_page.py
# ============================================================================


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_stats():
    """Кэшируем запрос в БД на 60 секунд."""
    return ctrl.get_global_stats()


def render():
    """Главная страница приложения — с KPI и кнопкой выключения."""

    st.title("📊 Дашборд аналитики комментариев YouTube")
    stats = _fetch_stats()

    # KPI-панель -------------------------------------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💬 Комментарии", f"{stats['total_comments']:,}")
    col2.metric("🎥 Видео", f"{stats['total_videos']:,}")
    col3.metric("📺 Каналы", f"{stats['total_channels']:,}")
    col4.metric("🔍 Запросы", f"{stats['total_queries']:,}")
    col5.metric("🔗 Матчи", f"{stats['total_matches']:,}")

    if stats["latest_comment_date"]:
        st.caption(
            f"Последний комментарий спарсен **{stats['latest_comment_date']:%d %b %Y}**")

    st.divider()

    # Блок управления ------------------------------------------------------
    st.subheader("🛠️ Управление")

    # Кнопка выключения
    if st.button("🚪 Выключить приложение", type="secondary", key="shutdown-btn-page"):
        st.write("Приложение останавливается…")
        if platform.system() == "Windows":
            os._exit(0)
        else:
            os.kill(os.getpid(), signal.SIGTERM)

    # Кнопка перезапуска страницы
    if st.button("🔄 Перезагрузить страницу", key="reload-btn"):
        st.rerun()

    # Кнопка очистки кэша и перезапуска
    if st.button("🧹 Очистить кэш и перезапустить", key="clear-cache-btn"):
        st.cache_data.clear()
        st.rerun()


# Для совместимости с запуском через Streamlit

if __name__ == "__main__":
    render()
