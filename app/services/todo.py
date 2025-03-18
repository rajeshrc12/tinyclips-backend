from sqlmodel import Session, select
from app.models.todo import Todo

def create_todo(session: Session, todo: Todo):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

def get_todos(session: Session):
    return session.exec(select(Todo)).all()

def get_todo_by_id(session: Session, todo_id: int):
    return session.get(Todo, todo_id)

def update_todo(session: Session, todo_id: int, todo_data: dict):
    todo = session.get(Todo, todo_id)
    if todo:
        for key, value in todo_data.items():
            setattr(todo, key, value)
        session.commit()
        session.refresh(todo)
    return todo

def delete_todo(session: Session, todo_id: int):
    todo = session.get(Todo, todo_id)
    if todo:
        session.delete(todo)
        session.commit()
    return todo