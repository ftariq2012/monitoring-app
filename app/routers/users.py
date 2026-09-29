from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import jwt
from datetime import datetime, timedelta, timezone

from app.database import engine
from app.models import UserDB
from app.schemas import User, UserCreate, UserLogin
from app.auth import password_hasher, JWT_SECRET, security, get_current_user


router = APIRouter(prefix="/users")

# Create a user
@router.post("/", status_code=201, response_model=User)
async def create_user(user: UserCreate):
    with Session(engine) as session:
        new_user = UserDB(
            username=user.username,
            email=user.email,
            password_hash=password_hasher.hash(user.password)
        )
        try:
            session.add(new_user)
            session.commit()
        except IntegrityError:
            session.rollback()

            raise HTTPException(
                status_code=409,
                detail="Username or email already exists"
            )
        
        session.refresh(new_user)
        return User(id=new_user.id, username=new_user.username, email=new_user.email)

# Read all users
@router.get("/")
async def get_users():
    with Session(engine) as session:
        statement = select(UserDB)
        result = session.scalars(statement)
        users = result.all()
    return [User(id=user.id, username=user.username, email=user.email) for user in users]

# Read a single user
@router.get("/{username}") 
async def get_user(username: str):
    with Session(engine) as session:
        statement = select(UserDB).where(UserDB.username == username)
        result = session.scalar(statement)
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        return User(id=result.id, username=result.username, email=result.email)

# Login a user
@router.post("/login")
async def login_user(user: UserLogin):
    with Session(engine) as session:
        statement = select(UserDB).where(UserDB.username == user.username)
        result = session.scalar(statement)
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        verify_password = password_hasher.verify(user.password, result.password_hash)
        if verify_password:
            payload = {
                "sub": str(result.id),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            }
            token = jwt.encode(
                payload,
                JWT_SECRET,
                algorithm="HS256"
            )
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(
                            status_code=401,
                            detail="Invalid username or password"
                        )
