# embedding_controller.py

import os
import time
import openai
from dotenv import load_dotenv
from typing import List, Tuple, Generator
from sqlalchemy.orm import Session
from db.db_session import get_session
from models.models import Comment
from openai import OpenAIError

# Загрузка API ключа
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Константы
MODEL_NAME = "text-embedding-ada-002"
TOKEN_LIMIT = 8192
COMMENTS_PER_BATCH = 1000
MAX_TEXTS_PER_REQUEST = 100

# Приблизительная оценка токенов


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def fetch_unembedded_comments(session: Session, limit: int) -> List[Comment]:
    return session.query(Comment).filter(Comment.embedding == None).limit(limit).all()


def split_into_batches(texts: List[str], batch_size: int) -> Generator[List[str], None, None]:
    for i in range(0, len(texts), batch_size):
        yield texts[i:i + batch_size]


def get_embeddings_from_openai(texts: List[str]) -> List[List[float]]:
    cleaned_texts = [text for text in texts if text and isinstance(
        text, str) and text.strip()]
    if not cleaned_texts:
        return []

    try:
        response = openai_client.embeddings.create(
            input=cleaned_texts,
            model=MODEL_NAME
        )
        embeddings = [item.embedding for item in response.data]
        return embeddings
    except OpenAIError as e:
        print(f"❌ Ошибка OpenAI API: {e}")
        raise


def save_embeddings(session: Session, comments: List[Comment], embeddings: List[List[float]]):
    for comment, embedding in zip(comments, embeddings):
        comment.embedding = embedding
    session.commit()


def process_small_batch(stop_signal: dict) -> Tuple[int, int]:
    total_processed = 0

    with get_session() as session:
        if stop_signal.get("stop", False):
            remaining = session.query(Comment).filter(
                Comment.embedding == None).count()
            return 0, remaining

        comments = fetch_unembedded_comments(session, COMMENTS_PER_BATCH)
        if not comments:
            return 0, 0

        valid_comments = [c for c in comments if c.text and isinstance(
            c.text, str) and c.text.strip()]
        if not valid_comments:
            return 0, session.query(Comment).filter(Comment.embedding == None).count()

        comment_texts = [comment.text for comment in valid_comments]
        comment_batches = list(split_into_batches(
            comment_texts, MAX_TEXTS_PER_REQUEST))
        comment_obj_batches = list(split_into_batches(
            valid_comments, MAX_TEXTS_PER_REQUEST))

        if comment_batches:
            text_batch = comment_batches[0]
            obj_batch = comment_obj_batches[0]
            try:
                embeddings = get_embeddings_from_openai(text_batch)
                if embeddings:
                    save_embeddings(session, obj_batch, embeddings)
                    total_processed += len(embeddings)
                time.sleep(1)
            except OpenAIError as api_error:
                print(f"❌ OpenAI API ошибка: {api_error}")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Непредвиденная ошибка: {e}")
                time.sleep(5)

    remaining = 0
    with get_session() as session:
        remaining = session.query(Comment).filter(
            Comment.embedding == None).count()

    return total_processed, remaining


def clean_empty_comments() -> int:
    deleted_count = 0
    with get_session() as session:
        comments = session.query(Comment).filter(
            (Comment.text == None) | (Comment.text == '') | (
                Comment.text.op('~')(r'^\s*$'))
        ).all()

        for comment in comments:
            print(f"🗑️ Удаляю пустой комментарий id={comment.id}")
            session.delete(comment)
            deleted_count += 1

        session.commit()

    return deleted_count
