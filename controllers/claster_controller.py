# controllers/claster_controller.py
import numpy as np
from sklearn.cluster import MiniBatchKMeans
from sqlalchemy import select
from models.models import Comment
from db.db_session import get_session
from tqdm import tqdm  # необязательно, но удобно в dev


def get_comment_embeddings(batch_size=10000):
    """Генератор батчей эмбедингов и id комментариев"""
    with get_session() as session:
        offset = 0
        while True:
            results = (
                session.execute(
                    select(Comment.id, Comment.embedding)
                    .where(Comment.embedding != None)
                    .offset(offset)
                    .limit(batch_size)
                )
                .all()
            )

            if not results:
                break

            ids, embeddings = zip(*results)
            yield list(ids), np.array(embeddings)
            offset += batch_size


def fit_kmeans_on_all_embeddings(n_clusters=20, batch_size=10000):
    """Обучает кластеризатор на всех эмбедингах"""
    kmeans = MiniBatchKMeans(n_clusters=n_clusters,
                             random_state=42, batch_size=batch_size)

    for _, embeddings in tqdm(get_comment_embeddings(batch_size), desc="Fitting"):
        kmeans.partial_fit(embeddings)

    return kmeans


def assign_clusters_and_save(kmeans_model, batch_size=10000):
    """Присваивает кластеры и обновляет таблицу"""
    with get_session() as session:
        for ids, embeddings in tqdm(get_comment_embeddings(batch_size), desc="Saving"):
            cluster_labels = kmeans_model.predict(embeddings)
            for comment_id, cluster in zip(ids, cluster_labels):
                session.query(Comment).filter(Comment.id == comment_id).update(
                    {Comment.cluster: int(cluster)}
                )
            session.commit()


def run_full_clustering(n_clusters=20, batch_size=10000):
    """Выполнить полную кластеризацию"""
    kmeans = fit_kmeans_on_all_embeddings(n_clusters, batch_size)
    assign_clusters_and_save(kmeans, batch_size)
