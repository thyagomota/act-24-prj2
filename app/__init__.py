import secrets

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI="sqlite:///app.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    from app.routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
