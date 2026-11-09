from app import db
from app.models import CompletedCourse, Student


def create_logged_in_student(client, app):
    client.post(
        "/register",
        data={
            "student_id": "S12345",
            "full_name": "A Student",
            "email": "student@example.edu",
            "password": "securepass",
        },
    )
    client.post(
        "/login",
        data={"email": "student@example.edu", "password": "securepass"},
    )
    with app.app_context():
        return Student.query.filter_by(email="student@example.edu").one().id


def test_completed_courses_requires_authentication(client):
    response = client.get("/completed-courses")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_completed_courses_displays_course_details_for_logged_in_student(
    client, app
):
    student_id = create_logged_in_student(client, app)
    with app.app_context():
        db.session.add(
            CompletedCourse(
                student_id=student_id,
                course_identifier="CS101",
                course_name="Introduction to Computing",
                credit_hours=3,
                earned_grade="A",
            )
        )
        db.session.add(
            CompletedCourse(
                student_id=student_id,
                course_identifier="MATH202",
                course_name="Discrete Mathematics",
                credit_hours=4,
                earned_grade="B+",
            )
        )
        db.session.commit()

    response = client.get("/completed-courses")

    assert response.status_code == 200
    assert b"CS101" in response.data
    assert b"Introduction to Computing" in response.data
    assert b"3 credit hours" in response.data
    assert b"Grade: A" in response.data
    assert b"MATH202" in response.data
    assert b"Discrete Mathematics" in response.data
    assert b"4 credit hours" in response.data
    assert b"Grade: B+" in response.data


def test_completed_courses_displays_empty_message(client, app):
    create_logged_in_student(client, app)

    response = client.get("/completed-courses")

    assert response.status_code == 200
    assert b"You have no completed courses." in response.data
