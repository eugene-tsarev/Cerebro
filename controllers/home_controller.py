# controllers/home_page.py
# ============================================================================
"""Контроллер домашней страницы — использует get_session().

Исправили предупреждение *SAWarning: cartesian product*:
теперь каждую метрику выбираем отдельным запросом через `Session.scalar()`.
Это надёжно и даёт корректные числа без лишних JOIN‑ов.
"""

from sqlalchemy import func, select
from db.db_session import get_session

from models.models import (
    Comment,
    Channel,
    Video,
    SearchQuery,
    MatchedComment,
)


def _aggregate_counts(session):
    """Возвращает все KPI — по одному SQL‑запросу на метрику."""

    total_comments = session.scalar(select(func.count(Comment.id)))
    total_videos = session.scalar(select(func.count(Video.id)))
    total_channels = session.scalar(select(func.count(Channel.id)))
    total_queries = session.scalar(select(func.count(SearchQuery.id)))
    total_matches = session.scalar(select(func.count(MatchedComment.id)))
    latest_comment_date = session.scalar(select(func.max(Comment.published_time)))

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
        (
            total_comments,
            total_videos,
            total_channels,
            total_queries,
            total_matches,
            latest_comment_date,
        ) = _aggregate_counts(session)

    return {
        "total_comments": total_comments or 0,
        "total_videos": total_videos or 0,
        "total_channels": total_channels or 0,
        "total_queries": total_queries or 0,
        "total_matches": total_matches or 0,
        "latest_comment_date": latest_comment_date,
    }

# ============================================================================
"""Контроллер домашней страницы — использует get_session()."""
