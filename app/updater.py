import itertools
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

import requests
from dateutil import parser
from flask import current_app

from app.lookup import find_case
from app.models import Refresh, RefreshStatus, Update, UpdateType, db
from app.utils import Regexps, validate


class Updater(ABC):
    @abstractmethod
    def get_update_type(self) -> UpdateType:
        return NotImplemented

    @abstractmethod
    def get_update_url(self, last_update_dt) -> str:
        return NotImplemented

    def process(self, data, update_dt) -> List[Update]:
        return NotImplemented

    def update(self, last_update_dt, update_dt) -> List[Update]:
        data = requests.get(self.get_update_url(last_update_dt)).json()
        return self.process(data, update_dt)


class ClosedCaseSummaryUpdater(Updater):
    def get_update_type(self) -> UpdateType:
        return UpdateType.CCS_PUBLISHED

    def get_update_url(self, last_update_dt) -> str:
        return f"https://data.seattle.gov/api/id/m33m-84uk.json?$query=select * where (`posted_date` > '{last_update_dt.isoformat()}') order by `posted_date` desc"

    def process_case(self, case, update_dt) -> Update:
        # Response:
        # [
        #   {
        #     "posted_date":"2022-05-03T00:00:00.000",
        #     "case":{
        #       "url":"https://www.seattle.gov/Documents/Departments/OPA/ClosedCaseSummaries/2021OPA-0281ccs032922.pdf",
        #       "description":"2021OPA-0281"
        #     },
        #     "disposition":"Partially Sustained",
        #     ":id":"row-3rbe.8ye2-uaai"
        #   },
        #   ...
        # ]
        update = Update()
        update.case_num = validate(
            case["case"]["description"], Regexps.CASE_NUM, "Invalid case number"
        )
        update.create_date = update_dt
        update.disposition = validate(
            case["disposition"], Regexps.CCS_DISPOSITION, "Unknown"
        )
        update.event_date = parser.parse(
            validate(case["posted_date"], Regexps.TIMESTAMP, "1970-01-01T00:00:00")
        )
        update.type = self.get_update_type()
        update.url = validate(case["case"]["url"], Regexps.CCS_URL, None)

        result = find_case(update.case_num)
        if result:
            update.officers = result.officers
            update.allegations = result.allegations
        else:
            update.officers = []
            update.allegations = []

        return update

    def process(self, data, update_dt) -> List[Update]:
        return [self.process_case(case, update_dt) for case in data]


class NewComplaintUpdater(Updater):
    def get_update_type(self) -> UpdateType:
        return UpdateType.COMPLAINT_FILED

    def get_update_url(self, last_update_dt) -> str:
        return f"https://data.seattle.gov/api/id/pafy-bfmu.json?$query=select * where ((`task_creation_date` > '{last_update_dt.isoformat()}') and (upper(`status_description`) = upper('OPA Intake'))) order by `task_creation_date` desc"

    def process_complaint(self, complaint, update_dt) -> Update:
        # Response:
        # [
        #   {
        #     "opa_case_number":"2022OPA-0134",
        #     "status":"Done",
        #     "status_description":"OPA Intake",
        #     "due_date":"2022-05-20T00:00:00.000",
        #     "completed_date":"2022-05-04T00:00:00.000",
        #     "task_creation_date":"2022-05-03T00:00:00.000",
        #     "due_date_2":"2022-05-20T00:00:00.000",
        #     "completed_date_2":"2022-05-04T00:00:00.000",
        #     "task_creation_date_2":"2022-05-03T00:00:00.000",
        #     "currentstatus":"Done"
        #   },
        #   ...
        update = Update()
        update.case_num = validate(
            complaint["opa_case_number"], Regexps.CASE_NUM, "Invalid case number"
        )
        update.create_date = update_dt
        update.event_date = parser.parse(
            validate(
                complaint["task_creation_date"],
                Regexps.TIMESTAMP,
                "1970-01-01T00:00:00",
            )
        )
        update.type = self.get_update_type()

        result = find_case(update.case_num)
        if result:
            update.allegations = result.allegations
            update.disposition = result.disposition
            update.officers = result.officers
        else:
            update.allegations = []
            update.disposition = ""
            update.officers = []

        return update

    def process(self, data, update_dt) -> List[Update]:
        return [self.process_complaint(complaint, update_dt) for complaint in data]


class ClosedInvestigationUpdater(Updater):
    def get_update_type(self) -> UpdateType:
        return UpdateType.INVESTIGATION_CLOSED

    def get_update_url(self, last_update_dt) -> str:
        return f"https://data.seattle.gov/api/id/99yi-dthu.json?$query=select * where (`investigation_end_date` > '{last_update_dt.isoformat()}') order by `investigation_end_date` desc"

    def process_case(self, case_num, rows, update_dt) -> Update:
        # Response:
        # [
        #   {
        #     "unique_id":"65217-98589-69722-1595-26426",
        #     "file_number":"2021OPA-0452",
        #     "incident_number":"65217",
        #     "occurred_date":"2021-10-03T00:00:00.000",
        #     "received_date":"2021-10-04T00:00:00.000",
        #     "incident_precinct":"-",
        #     "incident_beat":"-",
        #     "source":"SPD - Forwarded",
        #     "incident_type":"OPA Investigation",
        #     "allegation":"Professionalism",
        #     "disposition":"-",
        #     "discipline":"-",
        #     "named_employee_id":"1595",
        #     "named_employee_race":"Asian",
        #     "named_employee_gender":"M",
        #     "named_employee_age_at":"38",
        #     "named_employee_title_at":"ACTING POLICE SERGEANT",
        #     "named_employee_squad_at":"SOUTH PCT 3RD W - R/S RELIEF",
        #     "complainant_number":"26426",
        #     "complainant_gender":"Male",
        #     "complainant_race":"White",
        #     "complainant_age_complaint":"34",
        #     "case_status":"Active",
        #     "finding":"-",
        #     "investigation_begin_date":"2021-10-03T00:00:00.000",
        #     "investigation_end_date":"2022-05-01T00:00:00.000"
        #   },
        #   ...
        # ]
        officers = set()
        allegations = set()
        disposition = set()

        for row in rows:
            officers.add(validate(row["named_employee_id"], Regexps.SERIAL, "Unknown"))
            allegations.add(validate(row["allegation"], Regexps.STRING, "Unknown"))
            disposition.add(validate(row["disposition"], Regexps.STRING, "Unknown"))

        update = Update()
        update.allegations = list(allegations)
        update.case_num = validate(case_num, Regexps.CASE_NUM, "Invalid case number")
        update.create_date = update_dt
        update.event_date = parser.parse(
            validate(rows[0]["investigation_end_date"], Regexps.TIMESTAMP, None)
        )
        update.officers = list(officers)
        update.type = self.get_update_type()

        if len(disposition) == 1:
            update.disposition = "".join(disposition)
        else:
            update.disposition = "Partially Sustained"

        return update

    def process(self, data, update_dt) -> List[Update]:
        # Since this dataset lists one allegation per row, we need to aggregate by case number
        def key_by_case(d):
            return d["file_number"]

        data = sorted(data, key=key_by_case)
        cases = {k: list(v) for k, v in itertools.groupby(data, key=key_by_case)}
        return [
            self.process_case(case_num, rows, update_dt)
            for case_num, rows in cases.items()
        ]


updaters = [
    # updater, Refresh last_updated column
    (ClosedCaseSummaryUpdater(), "closed_case_summary_last_updated"),
    (NewComplaintUpdater(), "complaint_filed_last_updated"),
    (ClosedInvestigationUpdater(), "investigation_closed_last_updated"),
]


def do_update(last_refresh, now):
    """Retrieve updates from each updater and saves updates to the database."""
    refresh = Refresh()
    refresh.status = RefreshStatus.STARTED
    refresh.refresh_date = now
    db.session.add(refresh)
    db.session.commit()

    update_count = 0
    try:
        for updater, update_attr in updaters:
            # Get entries since latest entry we've seen
            last_updated = getattr(last_refresh, update_attr)
            updates = updater.update(last_updated, now)
            [db.session.add(update) for update in updates]

            # Set high water mark
            if len(updates):
                latest_event_date = max([update.event_date for update in updates])
                setattr(refresh, update_attr, latest_event_date)
            else:
                setattr(refresh, update_attr, getattr(last_refresh, update_attr))

            current_app.logger.debug(
                f"Found {len(updates)} updates for updater %s", type(updater)
            )
            update_count += len(updates)

        refresh.status = RefreshStatus.COMPLETED
        refresh.updates = update_count
    except Exception as e:
        refresh.status = RefreshStatus.FAILED
        current_app.logger.error("Update failed", e)

    db.session.add(refresh)
    db.session.commit()


def update():
    """Call do_update if an update is needed"""
    last_refresh = Refresh.last_refresh()
    now = datetime.now()

    if last_refresh:
        if (
            last_refresh.status == RefreshStatus.COMPLETED
            and now - last_refresh.refresh_date > current_app.config["REFRESH_INTERVAL"]
            or last_refresh.status in [RefreshStatus.STARTED, RefreshStatus.FAILED]
            and now - last_refresh.refresh_date > current_app.config["RETRY_INTERVAL"]
        ):
            if last_refresh.status != RefreshStatus.COMPLETED:
                # If the last refresh failed, look for updates since the last successful refresh
                # Assumption: there will always be a previous COMPLETED refresh
                last_refresh = Refresh.last_completed_refresh()
            current_app.logger.debug("Starting refresh...")
            do_update(last_refresh, now)
            current_app.logger.debug("Refresh completed")
        else:
            current_app.logger.debug(
                "Last run at %s, skipping update.", last_refresh.refresh_date
            )
    else:
        # On the first run, backfill 1 week and create a new Refresh entry.
        current_app.logger.info("First run, skipping update.")
        now = now - timedelta(weeks=1)
        refresh = Refresh()
        refresh.status = RefreshStatus.COMPLETED
        refresh.refresh_date = now

        refresh.closed_case_summary_last_updated = now
        refresh.complaint_filed_last_updated = now
        refresh.investigation_closed_last_updated = now

        db.session.add(refresh)
        db.session.commit()
