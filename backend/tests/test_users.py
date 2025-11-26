
def test_signup_success(client):
    response = client.post(
        "/users/signup",
        json={
            "email": "test@example.com",
            "password": "secret123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data


def test_signup_existing_email(client):
    # First signup
    client.post(
        "/users/signup",
        json={
            "email": "abc@example.com",
            "password": "pwd12345",
            "full_name": "User A"
        }
    )

    # Try again with same email
    response = client.post(
        "/users/signup",
        json={
            "email": "abc@example.com",
            "password": "pwd12345",
            "full_name": "User A"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success(client):
    # Create user first
    client.post(
        "/users/signup",
        json={
            "email": "login@example.com",
            "password": "mypassword",
            "full_name": "Login User"
        }
    )

    response = client.post(
        "/users/login",
        json={
            "email": "login@example.com",
            "password": "mypassword"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    # Create user
    client.post(
        "/users/signup",
        json={
            "email": "wrongpass@example.com",
            "password": "correctpass",
            "full_name": "User Wrong"
        }
    )

    # Wrong password
    response = client.post(
        "/users/login",
        json={
            "email": "wrongpass@example.com",
            "password": "incorrect"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
