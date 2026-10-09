from fastapi import FastAPI
from app.database import engine
from app.models import Base
from app.routers import tasks, users

#Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(tasks.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}