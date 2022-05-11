from datetime import timedelta
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
  SQLITE_DB_DIR = os.path.join(basedir, "../.data")
  SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "db.sqlite3")
  SQLALCHEMY_TRACK_MODIFICATIONS = False
  
  REFRESH_INTERVAL = timedelta(hours=1)
  RETRY_INTERVAL = timedelta(minutes=10)
  
  ITEMS_PER_PAGE = 25
  
  ROSTER_CSV_URL = os.environ['ROSTER_CSV_URL']
  UID_CSV_URL = os.environ['UID_CSV_URL']