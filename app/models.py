import enum

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class UpdateType(enum.Enum):
    CCS_PUBLISHED = "Closed Case Summary Published"
    COMPLAINT_FILED = "Complaint Filed"
    INVESTIGATION_CLOSED = "Investigation Closed"


class Update(db.Model):
    __tablename__ = "updates"

    id = db.Column(db.Integer, nullable=False, primary_key=True)

    create_date = db.Column(db.DateTime, nullable=False)  # time of refresh
    event_date = db.Column(
        db.DateTime, nullable=False
    )  # time event happened (posted date etc)

    type = db.Column(db.Enum(UpdateType), nullable=False)
    officers = db.Column(db.JSON, nullable=False)  # Normalize as JSON
    allegations = db.Column(
        db.JSON, nullable=True
    )  # New complaints may not always have allegations
    url = db.Column(db.String, nullable=True)

    case_num = db.Column(db.String, nullable=False)
    disposition = db.Column(db.String, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "create_date": self.create_date,
            "event_date": self.event_date,
            "type": self.type.name,
            "officers": self.officers,
            "allegations": self.allegations,
            "url": self.url,
            "case_num": self.case_num,
            "disposition": self.disposition,
        }


class RefreshStatus(enum.Enum):
    STARTED = "Started"
    COMPLETED = "Completed"
    FAILED = "Failed"


class Refresh(db.Model):
    __tablename__ = "refreshes"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    status = db.Column(db.Enum(RefreshStatus), nullable=False)
    updates = db.Column(db.Integer, nullable=False, default=0)

    # Used to determine whether an update is needed
    refresh_date = db.Column(db.DateTime, nullable=False)

    # Latest event date seen for update type. Used in updater query to determine date after which to search for new entries
    closed_case_summary_last_updated = db.Column(db.DateTime, nullable=True)
    complaint_filed_last_updated = db.Column(db.DateTime, nullable=True)
    investigation_closed_last_updated = db.Column(db.DateTime, nullable=True)

    @staticmethod
    def last_refresh():
        return (
            Refresh.query.order_by(Refresh.refresh_date.desc()).limit(1).one_or_none()
        )

    @staticmethod
    def last_completed_refresh():
        return (
            Refresh.query.filter_by(status=RefreshStatus.COMPLETED)
            .order_by(Refresh.refresh_date.desc())
            .limit(1)
            .one_or_none()
        )

    def to_dict(self):
        return {
            "id": self.id,
            "refresh_date": self.refresh_date,
            "status": self.status.name,
        }
