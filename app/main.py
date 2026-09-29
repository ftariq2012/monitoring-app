from fastapi import FastAPI

from app.routers import tasks, users

app = FastAPI()

app.include_router(tasks.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


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