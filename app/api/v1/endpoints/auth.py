from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database.connection import get_session  # Correct import
from app.schemas.auth import UserCreate, UserLogin
from app.services.auth import register_user, login_user

router = APIRouter()

@router.post("/register")
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    return register_user(session,user_data)

@router.post("/login")
def login(user_data: UserLogin, session: Session = Depends(get_session)):
    return login_user(session,user_data)