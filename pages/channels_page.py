import streamlit as st
import pandas as pd
from controllers import channels_controller as controller
from models.models import Channel


def render():
    st.title("Каналы YouTube")

    # 1. Форма добавления канала
    st.subheader("Добавить YouTube канал по URL")
    with st.form("add_channel_form"):
        url = st.text_input(
            "Вставьте ссылку на канал (формат: https://www.youtube.com/@channel/videos)")
        submitted = st.form_submit_button("Добавить канал")
        if submitted and url:
            with st.spinner("Добавление канала..."):
                success = controller.add_channel_from_url(url)
                if success:
                    st.success("Канал успешно добавлен.")
                else:
                    st.warning("Канал уже существует или произошла ошибка.")

    # 2. Получение списка каналов
    channels = controller.get_all_channels()

    # 3. Отображение таблицы с выбором
    st.subheader("Список каналов")
    selected_ids = []
    if channels:
        data = [
            {
                "ID": c.channel_id,
                "Название": c.channel_name,
                "Дата создания": c.created_at.strftime("%Y-%m-%d %H:%M")
            } for c in channels
        ]
        df = pd.DataFrame(data)
        for index, row in df.iterrows():
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                selected = st.checkbox(
                    "Выбрать", key=f"select_{row['ID']}", label_visibility="collapsed")
            with col2:
                st.write(
                    f"**{row['Название']}** — `{row['ID']}`  (создан: {row['Дата создания']})")
            if selected:
                selected_ids.append(row["ID"])
    else:
        st.info("Каналы отсутствуют. Добавьте новый.")

    # 4. Удаление
    if selected_ids:
        if st.button(f"Удалить выбранные ({len(selected_ids)}) канала(ов)", type="primary"):
            controller.delete_channels(selected_ids)
            st.success("Выбранные каналы удалены.")
            st.experimental_rerun()
