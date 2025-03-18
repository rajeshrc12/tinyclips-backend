from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Depends
from sqlmodel import Session
from app.models.auth import User
from app.schemas.auth import UserCreate, UserLogin
from app.utils.hash import hash_password, verify_password
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from app.config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def register_user(session: Session,user_data: UserCreate):
    new_user = User(**user_data.dict())
    new_user.password = hash_password(user_data.password)
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return {"message": "User registered successfully"}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")

def login_user(session: Session,user_data: UserLogin):
    user = session.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token(data={"email": user_data.email})
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict):
    to_encode = data.copy()
    if JWT_ACCESS_TOKEN_EXPIRE_MINUTES:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"email": email}
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")