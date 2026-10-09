import os
import pytest

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, URL, text

from app.main import app
from app.routers import users, tasks


load_dotenv()

# Connect to TEST database
test_url = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=os.getenv("DB_PASSWORD"),
    host="localhost",
    port=5432,
    database="task_manager_test"
)

test_engine = create_engine(test_url)

# Make the routers use the test database instead of the real database
users.engine = test_engine
tasks.engine = test_engine

client = TestClient(app)


# Clear test data before every test
@pytest.fixture(autouse=True)
def clear_database():
    with test_engine.begin() as connection:
        connection.execute(text("DELETE FROM tasks"))
        connection.execute(text("DELETE FROM users"))

    yield


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_user():
    response = client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_duplicate_user():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }

    first_response = client.post("/users/", json=user_data)
    second_response = client.post("/users/", json=user_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409

def test_login_success():
    # First create a user
    client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    # Then log in with the correct password
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    # First create a user
    client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    # Try logging in with the wrong password
    response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_tasks_without_token():
    response = client.get("/tasks/")

    assert response.status_code == 401


def test_tasks_with_valid_token():
    # Create user
    client.post(
        "/users/",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )

    # Login and get token
    login_response = client.post(
        "/users/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )

    token = login_response.json()["access_token"]

    # Send token with request
    response = client.get(
        "/tasks/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

def test_user_cannot_read_another_users_task():
    # Create User A
    client.post(
        "/users/",
        json={
            "username": "usera",
            "email": "usera@example.com",
            "password": "password123"
        }
    )

    # Login as User A
    login_a = client.post(
        "/users/login",
        json={
            "username": "usera",
            "password": "password123"
        }
    )

    token_a = login_a.json()["access_token"]

    # User A creates a task
    task_response = client.post(
        "/tasks/",
        json={
            "title": "User A task",
            "completed": False
        },
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    task_id = task_response.json()["id"]

    # Create User B
    client.post(
        "/users/",
        json={
            "username": "userb",
            "email": "userb@example.com",
            "password": "password123"
        }
    )

    # Login as User B
    login_b = client.post(
        "/users/login",
        json={
            "username": "userb",
            "password": "password123"
        }
    )

    token_b = login_b.json()["access_token"]

    # User B tries to read User A's task
    response = client.get(
        f"/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_task():
    # Create + login User A
    client.post(
        "/users/",
        json={
            "username": "usera",
            "email": "usera@example.com",
            "password": "password123"
        }
    )

    login_a = client.post(
        "/users/login",
        json={
            "username": "usera",
            "password": "password123"
        }
    )

    token_a = login_a.json()["access_token"]

    # User A creates a task
    task_response = client.post(
        "/tasks/",
        json={
            "title": "User A task",
            "completed": False
        },
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    task_id = task_response.json()["id"]

    # Create + login User B
    client.post(
        "/users/",
        json={
            "username": "userb",
            "email": "userb@example.com",
            "password": "password123"
        }
    )

    login_b = client.post(
        "/users/login",
        json={
            "username": "userb",
            "password": "password123"
        }
    )

    token_b = login_b.json()["access_token"]

    # User B tries to update User A's task
    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Hacked task",
            "completed": True
        },
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_task():
    # Create + login User A
    client.post(
        "/users/",
        json={
            "username": "usera",
            "email": "usera@example.com",
            "password": "password123"
        }
    )

    login_a = client.post(
        "/users/login",
        json={
            "username": "usera",
            "password": "password123"
        }
    )

    token_a = login_a.json()["access_token"]

    # User A creates a task
    task_response = client.post(
        "/tasks/",
        json={
            "title": "User A task",
            "completed": False
        },
        headers={
            "Authorization": f"Bearer {token_a}"
        }
    )

    task_id = task_response.json()["id"]

    # Create + login User B
    client.post(
        "/users/",
        json={
            "username": "userb",
            "email": "userb@example.com",
            "password": "password123"
        }
    )

    login_b = client.post(
        "/users/login",
        json={
            "username": "userb",
            "password": "password123"
        }
    )

    token_b = login_b.json()["access_token"]

    # User B tries to delete User A's task
    response = client.delete(
        f"/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token_b}"
        }
    )

    assert response.status_code == 404