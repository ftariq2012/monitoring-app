from fastapi import FastAPI
from pydantic import BaseModel

class Task(BaseModel):
    id: int
    title: str
    completed: bool

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

tasks = [
    Task(id=1, title="Learn FastAPI", completed=False),
    Task(id=2, title="Do LeetCode", completed=True)
]

@app.get("/tasks")
async def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    return {"error": "Task not found"}

@app.post("/tasks")
async def add_tasks(task: Task):
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, updated_task: Task):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks[i] = updated_task
            return updated_task
    return {"error": "Task not found"}

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            deleted_task = tasks.pop(i)
            return deleted_task
    return {"error": "Task not found"}
