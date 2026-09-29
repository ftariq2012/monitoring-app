from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy import Boolean, String, text, select, Text
from database import engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

# Pydantic models for request and response validation
class Task(BaseModel):
    id: int
    title: str
    completed: bool

class TaskCreate(BaseModel):
    title: str
    completed: bool

class User(BaseModel):
    id: int
    username: str
    email: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# ORM Base
class Base(DeclarativeBase):
    pass

# ORM model mapping for the tasks table
class TaskDB(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column()

# ORM model mapping for the users table
class UserDB(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(Text)


app = FastAPI()
password_hasher = PasswordHash.recommended()
JWT_SECRET = os.getenv("JWT_SECRET")
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        return int(user_id)

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Read all tasks
@app.get("/tasks") 
async def get_tasks(current_user_id: int = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(TaskDB).where(TaskDB.user_id == current_user_id)
        result = session.scalars(statement)
        tasks = result.all()
    return [Task(id=task.id, title=task.title, completed=task.completed) for task in tasks]

# Read a single task
@app.get("/tasks/{task_id}") 
async def get_task(task_id: int):
    with Session(engine) as session:
        result = session.get(TaskDB, task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return Task(id=result.id, title=result.title, completed=result.completed)
    

# Create a new task
@app.post("/tasks", status_code=201) 
async def add_tasks(task: TaskCreate):
    with engine.begin() as connection:
        result = connection.execute(text("""
                                INSERT INTO tasks (title, completed) 
                                VALUES (:title, :completed)
                                RETURNING id, title, completed
                                """), 
                                {
                                    "title": task.title, 
                                    "completed": task.completed
                                    }
                         )
        row = result.fetchone()
        if row is None:
            raise HTTPException(status_code=500, detail="Task creation failed")
        return Task(
            id=row[0],
            title=row[1],
            completed=row[2]
        )

# Update a task
@app.put("/tasks/{task_id}") 
async def update_task(task_id: int, updated_task: TaskCreate):
    with engine.begin() as connection:
        result = connection.execute(text("""
                                        UPDATE tasks 
                                        SET title = :title, completed = :completed 
                                        WHERE id = :id
                                        """), 
                                        {
                                            "title": updated_task.title, 
                                            "completed": updated_task.completed, 
                                            "id": task_id
                                        }
                         )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated successfully"}

# Delete a task
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    with engine.begin() as connection:
        result = connection.execute(text("""
                                        DELETE FROM tasks 
                                        WHERE id = :id
                                        """), 
                                        {"id": task_id}
                         )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# Create a user
@app.post("/users", status_code=201, response_model=User)
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
@app.get("/users")
async def get_users():
    with Session(engine) as session:
        statement = select(UserDB)
        result = session.scalars(statement)
        users = result.all()
    return [User(id=user.id, username=user.username, email=user.email) for user in users]

# Read a single user
@app.get("/users/{username}") 
async def get_user(username: str):
    with Session(engine) as session:
        statement = select(UserDB).where(UserDB.username == username)
        result = session.scalar(statement)
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        return User(id=result.id, username=result.username, email=result.email)

# Login a user
@app.post("/login")
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

# NEXT TIME:
# Current status:
# - User registration works
# - Password hashing works
# - Login works
# - JWT token creation works
# - get_current_user() can decode the JWT and return the logged-in user's ID
# - GET /tasks is protected and only returns tasks matching the logged-in user's user_id
#
# Still needs to be changed:
# 1. POST /tasks:
#    - Add Depends(get_current_user)
#    - Save current_user_id into the task's user_id column
#
# 2. GET /tasks/{task_id}:
#    - Add Depends(get_current_user)
#    - Only return the task if task.id AND task.user_id match
#
# 3. PUT /tasks/{task_id}:
#    - Add Depends(get_current_user)
#    - Only update the task if it belongs to the logged-in user
#
# 4. DELETE /tasks/{task_id}:
#    - Add Depends(get_current_user)
#    - Only delete the task if it belongs to the logged-in user
#
# IMPORTANT:
# Right now POST /tasks does NOT save user_id.
# This means newly created tasks may have user_id = NULL and will NOT show up
# in GET /tasks, because GET /tasks filters by the logged-in user's user_id.
#
# Goal:
# Every task should belong to one user, and users should only be able
# to view/change/delete their own tasks.