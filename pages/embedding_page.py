# embedding_page.py

import time
import streamlit as st
from controllers import embedding_controller


def render():
    st.title("Embedding Обработка Комментариев")

    if 'stop_signal' not in st.session_state:
        st.session_state['stop_signal'] = {"stop": False}
    if 'processing' not in st.session_state:
        st.session_state['processing'] = False
    if 'total_processed' not in st.session_state:
        st.session_state['total_processed'] = 0
    if 'remaining' not in st.session_state:
        st.session_state['remaining'] = 0

    processed_placeholder = st.empty()
    remaining_placeholder = st.empty()
    status_placeholder = st.empty()

    processed_placeholder.markdown(
        f"**Обработано:** {st.session_state['total_processed']}")
    remaining_placeholder.markdown(
        f"**Осталось:** {st.session_state['remaining']}")

    start_button = st.button("Запустить обработку эмбеддингов")
    stop_button = st.button("Остановить обработку")

    if start_button:
        st.session_state['stop_signal']['stop'] = False
        st.session_state['processing'] = True
        st.session_state['total_processed'] = 0
        st.session_state['remaining'] = 0
        deleted_comments = embedding_controller.clean_empty_comments()
        st.info(f"🗑️ Удалено пустых комментариев: {deleted_comments}")
        status_placeholder.info("🚀 Запущена обработка эмбеддингов...")
        print("🚀 Запущена обработка эмбеддингов...")

    if stop_button:
        st.session_state['stop_signal']['stop'] = True
        st.session_state['processing'] = False
        st.success("🛑 Остановка процесса!")
        print("🛑 Остановка процесса!")

    if st.session_state['processing']:
        processed, remaining = embedding_controller.process_small_batch(
            st.session_state['stop_signal'])
        st.session_state['total_processed'] += processed
        st.session_state['remaining'] = remaining

        processed_placeholder.markdown(
            f"**Обработано:** {st.session_state['total_processed']}")
        remaining_placeholder.markdown(
            f"**Осталось:** {st.session_state['remaining']}")
        print(
            f"🔄 Обработано: {st.session_state['total_processed']} | Осталось: {remaining}")

        if remaining == 0 or st.session_state['stop_signal']['stop']:
            if st.session_state['stop_signal']['stop']:
                status_placeholder.warning(
                    "🛑 Обработка остановлена пользователем.")
                print("🛑 Обработка остановлена пользователем.")
            else:
                status_placeholder.success(
                    "✅ Все эмбеддинги успешно обновлены!")
                print("✅ Все эмбеддинги успешно обновлены!")
            st.session_state['processing'] = False
        else:
            time.sleep(0.1)
            st.rerun()
