from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database.connection import get_session  # Correct import
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.crud.todo import (
    create_todo, get_todos, get_todo_by_id, update_todo, delete_todo
)

router = APIRouter()

@router.post("/todos/", response_model=Todo)
def create_todo_endpoint(todo: TodoCreate, session: Session = Depends(get_session)):
    db_todo = Todo(**todo.dict())
    return create_todo(session, db_todo)

@router.get("/todos/", response_model=list[Todo])
def read_todos(session: Session = Depends(get_session)):
    return get_todos(session)

@router.get("/todos/{todo_id}", response_model=Todo)
def read_todo(todo_id: int, session: Session = Depends(get_session)):
    todo = get_todo_by_id(session, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.put("/todos/{todo_id}", response_model=Todo)
def update_todo_endpoint(todo_id: int, todo: TodoUpdate, session: Session = Depends(get_session)):
    db_todo = update_todo(session, todo_id, todo.dict(exclude_unset=True))
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@router.delete("/todos/{todo_id}")
def delete_todo_endpoint(todo_id: int, session: Session = Depends(get_session)):
    db_todo = delete_todo(session, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted successfully"}