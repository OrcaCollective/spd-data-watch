import logging

from flask import Flask

from app.config import config


def create_app(config_name="default"):
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config.from_object(config[config_name])

    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    logging.basicConfig(
        filename=app.config["LOGGING_DIR"] / "application.log",
        level=logging.INFO,
    )

    with app.app_context():
        from .models import db

        db.init_app(app)

        db.create_all()

        from .views import views

        app.register_blueprint(views)

        from app.lookup import find_name, find_serial

        app.jinja_env.globals.update(find_name=find_name, find_serial=find_serial)

        return app
