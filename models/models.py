# models.py
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Date, Boolean, DateTime, UniqueConstraint, ARRAY
from datetime import datetime, date
from pgvector.sqlalchemy import Vector
from db.db_session import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Уникальный ID комментария
    cid = Column(String, unique=True, nullable=False)
    text = Column(String, nullable=False)              # Текст комментария
    mention = Column(String, nullable=True)            #
    author = Column(String, nullable=False)            # Автор комментария
    channel = Column(String, nullable=False)           # Название канала автора
    # Канал, на котором видео (под которым оставлен комментарий)
    video_channel_url = Column(String, nullable=False)
    video_id = Column(String, nullable=False)          # ID видео
    published_time = Column(Date, nullable=False)  # время публикации
    edited = Column(Boolean, nullable=False,
                    default=False)        # Исправлен комментарий или нет
    votes = Column(Integer, default=0)                 # Количество лайков
    tags = Column(ARRAY(Integer), nullable=True)   # Тэги
    embedding = Column(Vector(1536), nullable=True)   # Эмбеддинг комментария
    cluster = Column(Integer, nullable=True)  # поле для кластеризации
    __table_args__ = (UniqueConstraint("cid", name="uq_comment_cid"),)


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Текст поискового запроса
    query_text = Column(String, nullable=False, unique=True)
    # Эмбеддинг запроса
    embedding = Column(Vector(1536), nullable=False)


class MatchedComment(Base):
    __tablename__ = "matched_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ID из search_queries
    query_id = Column(Integer, nullable=False)
    comment_id = Column(Integer, nullable=False)               # ID из comments
    # Косинусное сходство
    similarity_score = Column(Float, nullable=False)
    # Моя оценка комментарию
    rating = Column(Integer, nullable=True)
    __table_args__ = (UniqueConstraint(
        "query_id", "comment_id", name="uq_query_comment"),)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, unique=True, nullable=False)
    channel_name = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("channel_id", name="uq_channel_id"),)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String, unique=True, nullable=False)
    channel_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    published_time = Column(DateTime, nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Дата последнего парсинга
    last_parsed_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("video_id", name="uq_video_id"),)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
