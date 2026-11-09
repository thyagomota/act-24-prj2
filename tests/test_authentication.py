from app.models import Student


def register_student(client):
    return client.post(
        "/register",
        data={
            "student_id": "S12345",
            "full_name": "A Student",
            "email": "student@example.edu",
            "password": "securepass",
        },
    )


def test_valid_login_grants_access_to_dashboard(client):
    register_student(client)

    response = client.post(
        "/login",
        data={"email": "student@example.edu", "password": "securepass"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as browser_session:
        assert "student_id" in browser_session

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Welcome, A Student" in response.data


def test_invalid_login_displays_error_and_does_not_grant_access(client):
    register_student(client)

    response = client.post(
        "/login",
        data={"email": "student@example.edu", "password": "incorrect"},
    )

    assert response.status_code == 400
    assert b"Invalid email or password." in response.data
    with client.session_transaction() as browser_session:
        assert "student_id" not in browser_session


def test_logout_ends_access_to_protected_dashboard(client, app):
    register_student(client)
    client.post(
        "/login",
        data={"email": "student@example.edu", "password": "securepass"},
    )

    response = client.post("/logout")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as browser_session:
        assert "student_id" not in browser_session

    response = client.get("/login")
    assert b"You have been logged out." in response.data

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with app.app_context():
        assert Student.query.count() == 1
