import streamlit as st
from controllers import queries_controller
from db.db_session import get_session


def render():
    st.header("\U0001F50D Поиск похожих комментариев")

    with get_session() as session:
        # --- Ввод нового запроса ---
        st.subheader("Создать новый запрос")
        query_text = st.text_input("Введите поисковый запрос")
        max_days = st.number_input(
            "Максимальный возраст комментариев (в днях)", min_value=1, max_value=365, value=30)
        top_n = st.number_input(
            "Количество наиболее похожих комментариев для записи", min_value=1, max_value=1000, value=100)

        if st.button("Найти похожие") and query_text:
            with st.spinner("Генерация эмбеддинга и поиск совпадений..."):
                embedding = queries_controller.generate_embedding(query_text)
                query_id = queries_controller.save_query(
                    session, query_text, embedding)
                match_count = queries_controller.find_and_save_similar(
                    session, query_id, embedding, max_days_old=max_days, limit=top_n)
                st.success(
                    f"Поиск завершен. Найдено {match_count} совпадений.")

        st.divider()

        # --- Удаление запросов ---
        st.subheader("История запросов")
        queries = queries_controller.get_queries(session)

        if queries:
            selected = []
            for q in queries:
                if st.checkbox(q.query_text, key=f"query_{q.id}"):
                    selected.append(q.id)

            if st.button("Удалить выбранные") and selected:
                deleted = queries_controller.delete_queries(session, selected)
                st.success(f"Удалено {deleted} запросов.")
                st.experimental_rerun()
        else:
            st.info("Список запросов пуст.")
