from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models import TaskDB
from app.schemas import Task, TaskCreate
from app.auth import get_current_user

router = APIRouter(prefix="/tasks")

# Read all tasks
@router.get("/") 
async def get_tasks(current_user_id: int = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(TaskDB).where(TaskDB.user_id == current_user_id)
        result = session.scalars(statement)
        tasks = result.all()
    return [Task(id=task.id, title=task.title, completed=task.completed) for task in tasks]

# Read a single task
@router.get("/{task_id}") 
async def get_task(task_id: int):
    with Session(engine) as session:
        result = session.get(TaskDB, task_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return Task(id=result.id, title=result.title, completed=result.completed)
    

# Create a new task
@router.post("/", status_code=201) 
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
@router.put("/{task_id}") 
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
@router.delete("/{task_id}")
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
