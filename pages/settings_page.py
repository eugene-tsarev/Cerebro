import streamlit as st
from controllers import settings_controller


def render():
    st.title("Настройки")

    st.header("Добавление тэгов")

    # Ввод нового тэга через форму
    with st.form("add_tag_form"):
        tag_name = st.text_input("Название тэга")
        tag_description = st.text_area("Описание тэга", height=100)
        submitted = st.form_submit_button("Добавить тэг")

        if submitted:
            success, message = settings_controller.add_tag(
                tag_name, tag_description)
            if success:
                st.success(message)
            else:
                st.error(message)

    # Отображение текущих тэгов
    st.subheader("Существующие тэги")
    tags = settings_controller.get_all_tags()
    if tags:
        for tag in tags:
            st.markdown(
                f"- **{tag.name}** — {tag.description or 'Без описания'}")
    else:
        st.info("Тэги пока не добавлены.")
