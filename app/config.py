import os
from datetime import timedelta
from pathlib import Path


_basedir = Path(__file__).parent.absolute()


class BaseConfig:
    SQLITE_DB_DIR = os.environ.get("SQLITE_DB_DIR", _basedir.parent / ".data")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LOGGING_DIR = Path(os.environ.get("LOGGING_DIR", ".data"))

    REFRESH_INTERVAL = timedelta(hours=1)
    RETRY_INTERVAL = timedelta(minutes=10)

    ITEMS_PER_PAGE = 25

    ROSTER_CSV_URL = os.environ["ROSTER_CSV_URL"]
    UID_CSV_URL = os.environ["UID_CSV_URL"]


class TestConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    REFRESH_INTERVAL = timedelta(hours=1)
    RETRY_INTERVAL = timedelta(minutes=10)


config = {
    "development": BaseConfig,
    "production": BaseConfig,
    "testing": TestConfig,
}
config["default"] = config.get(os.environ.get("FLASK_ENV", ""), BaseConfig)
