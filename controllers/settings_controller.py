from db.db_session import get_session
from models.models import Tag
from sqlalchemy.exc import SQLAlchemyError


def add_tag(name: str, description: str) -> tuple[bool, str]:
    if not name:
        return False, "Введите название тэга."

    try:
        with get_session() as session:
            existing = session.query(Tag).filter_by(name=name).first()
            if existing:
                return False, f"Тэг с названием '{name}' уже существует."

            new_tag = Tag(name=name, description=description)
            session.add(new_tag)
            session.commit()
            return True, f"Тэг '{name}' добавлен успешно."
    except SQLAlchemyError as e:
        return False, f"Ошибка при добавлении тэга: {str(e)}"


def get_all_tags() -> list[Tag]:
    with get_session() as session:
        return session.query(Tag).order_by(Tag.name).all()
