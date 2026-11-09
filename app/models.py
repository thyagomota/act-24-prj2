from werkzeug.security import check_password_hash, generate_password_hash

from app import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """Store a secure hash of the student's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Return whether the supplied password matches this account."""
        return check_password_hash(self.password_hash, password)


class CompletedCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    course_identifier = db.Column(db.String(80), nullable=False)
    course_name = db.Column(db.String(160), nullable=False)
    credit_hours = db.Column(db.Integer, nullable=False)
    earned_grade = db.Column(db.String(2), nullable=False)
