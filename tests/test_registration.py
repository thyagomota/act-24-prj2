from app.models import Student


def registration_form(**overrides):
    form = {
        "student_id": "S12345",
        "full_name": "A Student",
        "email": "student@example.edu",
        "password": "securepass",
    }
    form.update(overrides)
    return form


def test_registration_creates_account_and_student_can_log_in(client, app):
    response = client.post("/register", data=registration_form())

    assert response.status_code == 302
    with app.app_context():
        student = Student.query.one()
        assert student.student_id == "S12345"
        assert student.full_name == "A Student"
        assert student.email == "student@example.edu"
        student_record_id = student.id

    response = client.post(
        "/login",
        data={"email": "student@example.edu", "password": "securepass"},
    )

    assert response.status_code == 302
    with client.session_transaction() as browser_session:
        assert browser_session["student_id"] == student_record_id


def test_registration_rejects_missing_field_without_creating_account(client, app):
    form = registration_form()
    del form["full_name"]

    response = client.post("/register", data=form)

    assert response.status_code == 400
    assert b"All fields are required." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_malformed_email_without_creating_account(client, app):
    response = client.post("/register", data=registration_form(email="not-an-email"))

    assert response.status_code == 400
    assert b"Enter a valid email address." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_short_password_without_creating_account(client, app):
    response = client.post("/register", data=registration_form(password="short"))

    assert response.status_code == 400
    assert b"Password must be at least 8 characters long." in response.data
    with app.app_context():
        assert Student.query.count() == 0


def test_registration_rejects_duplicate_student_id(client, app):
    client.post("/register", data=registration_form())

    response = client.post(
        "/register",
        data=registration_form(email="other@example.edu"),
    )

    assert response.status_code == 400
    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_rejects_duplicate_email(client, app):
    client.post("/register", data=registration_form())

    response = client.post(
        "/register",
        data=registration_form(student_id="S67890"),
    )

    assert response.status_code == 400
    assert b"student ID or email already exists" in response.data
    with app.app_context():
        assert Student.query.count() == 1


def test_registration_stores_password_hash_not_plaintext(client, app):
    client.post("/register", data=registration_form())

    with app.app_context():
        student = Student.query.one()
        assert student.password_hash != "securepass"
        assert student.check_password("securepass")
        assert not student.check_password("wrongpass")


def test_login_rejects_incorrect_password(client, app):
    client.post("/register", data=registration_form())

    response = client.post(
        "/login",
        data={"email": "student@example.edu", "password": "incorrect"},
    )

    assert response.status_code == 400
    assert b"Invalid email or password." in response.data
    with client.session_transaction() as browser_session:
        assert "student_id" not in browser_session
