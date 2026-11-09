import pytest

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


def add_course(app, student_id, grade="B"):
    with app.app_context():
        course = CompletedCourse(
            student_id=student_id,
            course_identifier="CS101",
            course_name="Introduction to Computing",
            credit_hours=3,
            earned_grade=grade,
        )
        db.session.add(course)
        db.session.commit()
        return course.id


def test_student_can_select_completed_course_to_edit_grade(client, app):
    student_id = create_logged_in_student(client, app)
    course_id = add_course(app, student_id)

    response = client.get("/completed-courses")

    assert response.status_code == 200
    assert b"Edit grade" in response.data

    response = client.get(f"/completed-courses/{course_id}/edit")

    assert response.status_code == 200
    assert b"Edit grade for CS101" in response.data
    assert b'name="earned_grade"' in response.data


@pytest.mark.parametrize(
    ("grade", "expected_gpa"),
    [
        ("A", "4.00"),
        ("B", "3.00"),
        ("C", "2.00"),
        ("D", "1.00"),
        ("F", "0.00"),
    ],
)
def test_grade_update_accepts_valid_grade_and_recalculates_gpa(
    client, app, grade, expected_gpa
):
    student_id = create_logged_in_student(client, app)
    course_id = add_course(app, student_id)

    response = client.post(
        f"/completed-courses/{course_id}/edit",
        data={"earned_grade": grade},
    )

    assert response.status_code == 302
    with app.app_context():
        course = db.session.get(CompletedCourse, course_id)
        assert course.earned_grade == grade

    response = client.get("/completed-courses")

    assert f"Grade: {grade}".encode() in response.data
    assert f"Current GPA: {expected_gpa}".encode() in response.data


@pytest.mark.parametrize("grade", ["A+", ""])
def test_grade_update_rejects_invalid_grade_without_changing_course(
    client, app, grade
):
    student_id = create_logged_in_student(client, app)
    course_id = add_course(app, student_id)

    response = client.post(
        f"/completed-courses/{course_id}/edit",
        data={"earned_grade": grade},
    )

    assert response.status_code == 400
    assert b"Grade must be one of A, B, C, D, or F." in response.data
    with app.app_context():
        course = db.session.get(CompletedCourse, course_id)
        assert course.earned_grade == "B"


def test_grade_update_requires_authentication(client):
    response = client.post(
        "/completed-courses/1/edit",
        data={"earned_grade": "A"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
