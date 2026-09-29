# Pydantic models for request and response validation
from pydantic import BaseModel

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