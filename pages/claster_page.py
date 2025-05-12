import streamlit as st
from db.db_session import get_session
from models.models import Comment, Tag
from sqlalchemy import select, func
from controllers.claster_controller import run_full_clustering


def render():
    st.title("Кластеры комментариев")

    n_clusters = st.number_input(
        "Количество кластеров", min_value=2, max_value=500, value=20, step=1)

    if st.button("Запустить кластеризацию комментариев"):
        with st.spinner("Кластеризация выполняется, подождите..."):
            run_full_clustering(n_clusters=n_clusters)
        st.success("Кластеризация завершена.")

    with get_session() as session:
        # Получаем список тэгов
        tags = session.execute(
            select(Tag.id, Tag.name).order_by(Tag.name)).all()
        tag_options = {name: tag_id for tag_id, name in tags}

    selected_tag_name = st.selectbox(
        "Фильтр по тэгу", ["Все тэги"] + list(tag_options.keys()))
    selected_tag_id = tag_options.get(selected_tag_name)

    with get_session() as session:
        # Получаем кластеры и количество комментариев в них
        cluster_counts_query = select(
            Comment.cluster,
            func.count().label("total_count"),
            func.count(Comment.tags).filter(Comment.tags.any(
                selected_tag_id) if selected_tag_id else True).label("tagged_count")
        ).where(Comment.cluster != None)

        if selected_tag_id:
            cluster_counts_query = cluster_counts_query.where(
                Comment.tags.any(selected_tag_id))

        cluster_counts_query = cluster_counts_query.group_by(
            Comment.cluster).order_by(Comment.cluster)
        cluster_stats = session.execute(cluster_counts_query).all()

        if not cluster_stats:
            st.warning("Кластеры не найдены по выбранному тэгу. Измени фильтр.")
            return

    # Выводим радио-кнопки с количеством комментариев
    cluster_options = {
        f"Кластер {row.cluster} (всего: {row.total_count}, с тэгом: {row.tagged_count})": row.cluster
        for row in cluster_stats
    }

    selected_cluster_label = st.radio(
        "Выбери кластер", list(cluster_options.keys()))
    selected_cluster = cluster_options[selected_cluster_label]

    with get_session() as session:
        # Загружаем комментарии по кластеру и тэгу
        query = select(Comment.text, Comment.author, Comment.published_time).where(
            Comment.cluster == selected_cluster)
        if selected_tag_id:
            query = query.where(Comment.tags.any(selected_tag_id))
        comments = session.execute(query.limit(100)).all()

    st.subheader(f"Показано 100 комментариев из кластера {selected_cluster}")
    st.dataframe([
        {
            "Текст": c.text,
            "Автор": c.author,
            "Опубликован": c.published_time.strftime("%Y-%m-%d") if c.published_time else ""
        }
        for c in comments
    ])
