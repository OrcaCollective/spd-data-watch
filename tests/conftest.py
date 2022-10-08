import pytest

from app.app import create_app
from app.models import db as _db


@pytest.fixture
def flask():
    app = create_app("testing")
    app.config["WTF_CSRF_ENABLED"] = False

    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    return app


@pytest.fixture
def db(flask):
    def teardown():
        _db.drop_all()

    _db.app = flask
    _db.create_all()
    return _db
