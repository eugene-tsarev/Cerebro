# controllers/comments_controller.py
from sqlalchemy.orm import Session
from db.db_session import get_session
from models.models import SearchQuery, MatchedComment, Comment, Tag
from sqlalchemy import select, join, desc, asc
from sqlalchemy.dialects.postgresql import array


def get_search_queries():
    with get_session() as session:
        queries = session.scalars(select(SearchQuery.query_text)).all()
        return queries


def get_matched_comments(query_text: str, sort_by: str):
    with get_session() as session:
        query = session.scalar(select(SearchQuery).where(
            SearchQuery.query_text == query_text))
        if not query:
            return []

        stmt = (
            select(Comment.text,
                   Comment.cid,
                   Comment.video_id,
                   Comment.published_time,
                   Comment.author,
                   MatchedComment.similarity_score)
            .select_from(join(MatchedComment, Comment, MatchedComment.comment_id == Comment.id))
            .where(MatchedComment.query_id == query.id)
        )

        if sort_by == "По совпадению":
            stmt = stmt.order_by(desc(MatchedComment.similarity_score))
        elif sort_by == "По дате публикации":
            stmt = stmt.order_by(desc(Comment.published_time))

        results = session.execute(stmt).all()

        return [
            {
                "text": r.text,
                "similarity_score": r.similarity_score,
                "youtube_url": f"https://www.youtube.com/watch?v={r.video_id}&lc={r.cid}",
                "published_time": r.published_time,
                "cid": r.cid,
                "author": r.author,
                "youtube_link": f"https://www.youtube.com/watch?v={r.video_id}&lc={r.cid}"
            }
            for r in results
        ]


def update_comment_rating(query_text: str, cid: str, rating: int):
    with get_session() as session:
        query = session.scalar(select(SearchQuery).where(
            SearchQuery.query_text == query_text))
        comment = session.scalar(select(Comment).where(Comment.cid == cid))
        if not query or not comment:
            return

        matched = session.scalar(
            select(MatchedComment).where(
                MatchedComment.query_id == query.id,
                MatchedComment.comment_id == comment.id
            )
        )
        if matched:
            matched.rating = rating
            session.commit()


def get_comments_by_author(author: str):
    with get_session() as session:
        stmt = (
            select(Comment.text,
                   Comment.cid,
                   Comment.video_id,
                   Comment.published_time)
            .where(Comment.author == author)
            .order_by(desc(Comment.published_time))
        )
        results = session.execute(stmt).all()

        return [
            {
                "text": r.text,
                "youtube_url": f"https://www.youtube.com/watch?v={r.video_id}&lc={r.cid}",
                "published_time": r.published_time,
            }
            for r in results
        ]


def get_all_tags():
    with get_session() as session:
        stmt = select(Tag.id, Tag.name, Tag.description).order_by(Tag.name)
        tags = session.execute(stmt).all()
        return [
            {"id": tag.id, "name": tag.name, "description": tag.description}
            for tag in tags
        ]


def update_comment_tags(cid: str, tag_ids: list[int]):
    with get_session() as session:
        comment = session.scalar(select(Comment).where(Comment.cid == cid))
        if comment:
            comment.tags = tag_ids
            session.commit()


def get_tags_for_comment(cid: str):
    with get_session() as session:
        comment = session.scalar(select(Comment).where(Comment.cid == cid))
        if comment and comment.tags:
            return comment.tags
        return []
