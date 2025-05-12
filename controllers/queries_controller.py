import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from sqlalchemy import select, delete, func, cast
from sqlalchemy.orm import Session
from openai import OpenAI
from pgvector.sqlalchemy import Vector

from db.db_session import get_session
from models.models import SearchQuery, Comment, MatchedComment

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def save_query(session: Session, query_text: str, embedding: list[float]) -> int:
    existing = session.execute(
        select(SearchQuery).where(SearchQuery.query_text == query_text)
    ).scalar_one_or_none()

    if existing:
        return existing.id

    query = SearchQuery(query_text=query_text, embedding=embedding)
    session.add(query)
    session.commit()
    session.refresh(query)
    return query.id


def find_and_save_similar(session: Session, query_id: int, embedding: list[float], max_days_old: int, limit: int = 1000) -> int:
    cutoff_date = datetime.utcnow().date() - timedelta(days=max_days_old)

    results = session.execute(
        select(
            Comment.id,
            func.cosine_distance(Comment.embedding, cast(embedding, Vector)).label("distance")
        )
        .where(Comment.published_time >= cutoff_date)
        .order_by("distance")
    ).all()

    # выбираем top-N самых близких (низкое расстояние → высокая схожесть)
    top_matches = results[:limit]

    for comment_id, distance in top_matches:
        match = MatchedComment(
            query_id=query_id,
            comment_id=comment_id,
            similarity_score=1 - distance
        )
        session.add(match)

    session.commit()
    return len(top_matches)


def get_queries(session: Session):
    return session.execute(select(SearchQuery).order_by(SearchQuery.id.desc())).scalars().all()


def delete_queries(session: Session, ids: list[int]) -> int:
    if not ids:
        return 0

    session.execute(delete(MatchedComment).where(MatchedComment.query_id.in_(ids)))
    result = session.execute(delete(SearchQuery).where(SearchQuery.id.in_(ids)))
    session.commit()
    return result.rowcount
