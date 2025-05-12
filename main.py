import streamlit as st
from pages import (
    home_page,
    queries_page,
    comments_page,
    channels_page,
    videos_page,
    search_page,
    parser_page,
    embedding_page,
    settings_page,
    claster_page
)

PAGES = {
    "Главная": home_page,
    "Запросы": queries_page,
    "Комментарии": comments_page,
    "Каналы": channels_page,
    "Видео": videos_page,
    "Поиск": search_page,
    "Парсер": parser_page,
    "Эмбединги": embedding_page,
    "Настройки": settings_page,
    "Кластеризация": claster_page
}

st.set_page_config(page_title="Комментарий Аналитика", layout="wide")
st.sidebar.title("Меню")
selection = st.sidebar.radio("Выбери раздел", list(PAGES.keys()))
st.session_state.selected_query_id = st.session_state.get(
    "selected_query_id", None)

page = PAGES[selection]
page.render()
