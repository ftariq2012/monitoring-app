from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy import Boolean, String, text, select
from database import engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


# Pydantic models for request and response validation
class Task(BaseModel):
    id: int
    title: str
    completed: bool

class TaskCreate(BaseModel):
    title: str
    completed: bool


# ORM Base
class Base(DeclarativeBase):
    pass

# ORM model mapping for the tasks table
class TaskDB(Base):
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Read all tasks
@app.get("/tasks") 
async def get_tasks():
    with Session(engine) as session:
        statement = select(TaskDB)
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
        return Task(id=row[0], title=row[1], completed=row[2])

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
