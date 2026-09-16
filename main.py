from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy import create_engine, URL
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost",
    port=5432,
    database="task_manager"
)

engine = create_engine(url)

class Task(BaseModel):
    id: int
    title: str
    completed: bool

class TaskCreate(BaseModel):
    title: str
    completed: bool

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Read all tasks
@app.get("/tasks") 
async def get_tasks():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM tasks"))
        tasks = []
        for row in result: 
            tasks.append(Task(id=row[0], title=row[1], completed=row[2]))
    return tasks

# Read a single task
@app.get("/tasks/{task_id}") 
async def get_task(task_id: int):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM tasks WHERE id = :id"), {"id": task_id})
        for row in result:
            return Task(id=row[0], title=row[1], completed=row[2])
    raise HTTPException(status_code=404, detail="Task not found")
    

# Create a new task
@app.post("/tasks", status_code=201) 
async def add_tasks(task: TaskCreate):
    with engine.begin() as connection:
        connection.execute(text("""
                                INSERT INTO tasks (title, completed) 
                                VALUES (:title, :completed)
                                """), 
                                {
                                    "title": task.title, 
                                    "completed": task.completed
                                    }
                         )
        return {"message": "Task created successfully"}

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
