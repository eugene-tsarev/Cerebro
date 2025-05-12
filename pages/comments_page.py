# pages/comments_page.py
import streamlit as st
from collections import defaultdict
from controllers import comments_controller


def render():
    st.title("Комментарии по запросу")

    queries = comments_controller.get_search_queries()
    if not queries:
        st.warning("Нет доступных запросов.")
        return

    query_text = st.selectbox("Выберите поисковый запрос", queries)
    sort_by = st.radio("Сортировать по", [
                       "По совпадению", "По дате публикации", "По количеству комментариев автора"])

    comments = comments_controller.get_matched_comments(
        query_text, sort_by if sort_by != "По количеству комментариев автора" else "По совпадению")
    all_tags = comments_controller.get_all_tags()

    # Собираем счётчики комментариев по авторам
    author_comment_counts = defaultdict(int)
    author_comments_cache = {}
    for comment in comments:
        author = comment['author']
        if author not in author_comments_cache:
            author_comments_cache[author] = comments_controller.get_comments_by_author(
                author)
        author_comment_counts[author] = len(author_comments_cache[author])

    # Дополняем комментарии количеством
    for comment in comments:
        comment['author_comment_count'] = author_comment_counts[comment['author']]

    # Сортировка по количеству комментариев автора
    if sort_by == "По количеству комментариев автора":
        comments = sorted(
            comments, key=lambda c: c['author_comment_count'], reverse=True)

    st.subheader(f"Найдено комментариев: {len(comments)}")

    for comment in comments:
        st.markdown("---")
        st.markdown(f"**Комментарий:** {comment['text']}")

        info_line = (
            f"Сходство: {comment['similarity_score']:.3f} | "
            f"Дата публикации: {comment['published_time']} | "
            f"Комментариев от автора: {comment['author_comment_count']} | "
            f"Автор: {comment['author']} | "
            f"[YouTube]({comment['youtube_link']})"
        )
        st.markdown(info_line)

        rating_key = f"rating_{comment['cid']}"
        selected_rating = st.selectbox(
            "Оценка:",
            options=[1, 2, 3, 4, 5],
            index=0,
            key=rating_key
        )
        comments_controller.update_comment_rating(
            query_text, comment['cid'], selected_rating)

        tag_key = f"tags_{comment['cid']}"
        tag_options = {tag['name']: tag['id'] for tag in all_tags}
        selected_tag_ids = comments_controller.get_tags_for_comment(
            comment['cid'])
        selected_tag_names = [tag['name']
                              for tag in all_tags if tag['id'] in selected_tag_ids]

        new_tag_names = st.multiselect(
            "Теги:",
            options=list(tag_options.keys()),
            default=selected_tag_names,
            key=tag_key
        )
        new_tag_ids = [tag_options[name] for name in new_tag_names]
        comments_controller.update_comment_tags(comment['cid'], new_tag_ids)

        toggle_key = f"show_author_{comment['cid']}"
        if st.toggle("Показать все комментарии автора", key=toggle_key):
            st.markdown(f"**Другие комментарии автора {comment['author']}:**")
            author_comments = author_comments_cache[comment['author']]
            for ac in author_comments:
                st.markdown(
                    f"- {ac['text']} \n [YouTube]({ac['youtube_url']}) \n *(Опубликовано: {ac['published_time']})*")
