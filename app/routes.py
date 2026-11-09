import re
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import CompletedCourse, Student

bp = Blueprint("main", __name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GRADE_POINTS = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}


def _registration_error(student_id, full_name, email, password):
    """Return a validation message, or None when registration data is valid."""
    if not student_id or not full_name or not email or not password:
        return "All fields are required."
    if not EMAIL_PATTERN.fullmatch(email):
        return "Enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    return None


def login_required(view):
    """Redirect visitors to the login page unless they have an active session."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to access that page.", "error")
            return redirect(url_for("main.login"))
        return view(*args, **kwargs)

    return wrapped_view


def _calculate_gpa(courses):
    """Return the credit-hour-weighted GPA, or None when it is unavailable."""
    total_credit_hours = 0
    total_grade_points = 0

    for course in courses:
        grade = course.earned_grade.strip().upper()
        grade_points = GRADE_POINTS.get(grade[:1])
        if grade_points is None:
            return None
        total_credit_hours += course.credit_hours
        total_grade_points += grade_points * course.credit_hours

    if total_credit_hours <= 0:
        return None
    return total_grade_points / total_credit_hours


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    student_id = request.form.get("student_id", "").strip()
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    error = _registration_error(student_id, full_name, email, password)
    if error:
        flash(error, "error")
        return render_template("register.html"), 400

    duplicate = Student.query.filter(
        or_(Student.student_id == student_id, Student.email == email)
    ).first()
    if duplicate:
        flash("An account with that student ID or email already exists.", "error")
        return render_template("register.html"), 400

    student = Student(
        student_id=student_id,
        full_name=full_name,
        email=email,
    )
    student.set_password(password)
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("An account with that student ID or email already exists.", "error")
        return render_template("register.html"), 400

    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("main.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("login.html"), 400

    student = Student.query.filter_by(email=email).first()
    if student is None or not student.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template("login.html"), 400

    session.clear()
    session["student_id"] = student.id
    flash("Login successful.", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/dashboard")
@login_required
def dashboard():
    student = db.session.get(Student, session["student_id"])
    if student is None:
        session.clear()
        flash("Please log in to access that page.", "error")
        return redirect(url_for("main.login"))
    return render_template("dashboard.html", student=student)


@bp.route("/completed-courses")
@login_required
def completed_courses():
    courses = CompletedCourse.query.filter_by(
        student_id=session["student_id"]
    ).all()
    current_gpa = _calculate_gpa(courses)
    return render_template(
        "completed_courses.html", courses=courses, current_gpa=current_gpa
    )


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.login"))
