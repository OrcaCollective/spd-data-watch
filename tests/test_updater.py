from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

import app.updater
from app.models import Refresh, RefreshStatus, Update, UpdateType
from app.updater import do_update, update


NOW = datetime.now()


@pytest.mark.parametrize(
    "last_refresh_date, last_refresh_failed, do_update_expected",
    [
        # First run -> no update
        (None, False, False),
        # Retry interval (10 min) not yet reached -> no update
        (NOW - timedelta(minutes=5), True, False),
        # Retry interval (10 min) reached -> update expected
        (NOW - timedelta(minutes=15), True, True),
        # Refresh interval (1 hour) not yet reached -> no update
        (NOW - timedelta(minutes=50), False, False),
        # Refresh interval (1 hour) reached -> update expected
        (NOW - timedelta(minutes=70), False, True),
    ],
)
def test_update(flask, db, last_refresh_date, last_refresh_failed, do_update_expected):
    if last_refresh_date:
        refresh = Refresh()
        refresh.id = 1
        refresh.updates = 0
        refresh.refresh_date = last_refresh_date

        if last_refresh_failed:
            refresh.status = RefreshStatus.FAILED
        else:
            refresh.status = RefreshStatus.COMPLETED

        db.session.add(refresh)

    with patch("app.updater.do_update") as do_update:
        update(NOW)

        if do_update_expected:
            do_update.assert_called()


@pytest.mark.parametrize(
    "event_dates, new_status, new_last_updated, update_count",
    [
        ([], RefreshStatus.COMPLETED, NOW - timedelta(weeks=1), 0),
        (
            [NOW - timedelta(weeks=2)],
            RefreshStatus.COMPLETED,
            NOW - timedelta(weeks=1),
            1,
        ),
        ([NOW], RefreshStatus.COMPLETED, NOW, 1),
        ([NOW, NOW], RefreshStatus.COMPLETED, NOW, 2),
    ],
)
def test_do_update(flask, db, event_dates, new_status, new_last_updated, update_count):
    last_refresh = Refresh()
    last_refresh.refresh_date = NOW - timedelta(weeks=1)
    last_refresh.closed_case_summary_last_updated = NOW - timedelta(weeks=1)

    def create_update(event_date):
        update = Update()
        update.create_date = datetime(1970, 1, 1)
        update.type = UpdateType.CCS_PUBLISHED
        update.officers = []
        update.case_num = ":)"
        update.event_date = event_date
        return update

    updater = MagicMock()
    updater.update.return_value = [create_update(d) for d in event_dates]
    app.updater.updaters = [(updater, "closed_case_summary_last_updated")]

    refresh_date = datetime.now()
    do_update(last_refresh, refresh_date)

    refreshes = Refresh.query.filter_by(refresh_date=refresh_date).all()
    assert 1 == len(refreshes)

    refresh = refreshes[0]
    assert refresh.status == RefreshStatus.COMPLETED
    assert refresh.closed_case_summary_last_updated == new_last_updated
    assert refresh.updates == update_count


def test_do_update_failed(flask, db):
    last_refresh = Refresh()
    last_refresh.refresh_date = NOW - timedelta(weeks=1)

    updater = MagicMock()
    updater.update.side_effect = Exception(":(")
    app.updater.updaters = [(updater, "closed_case_summary_last_updated")]

    refresh_date = datetime.now()
    do_update(last_refresh, refresh_date)

    refreshes = Refresh.query.filter_by(refresh_date=refresh_date).all()
    assert len(refreshes) == 1

    refresh = refreshes[0]
    assert refresh.status == RefreshStatus.FAILED


@pytest.mark.acceptance
@pytest.mark.parametrize("updater", [updater for (updater, _) in app.updater.updaters])
def test_updater(flask, db, updater):
    refresh_date = datetime.now()
    updates = updater.update(refresh_date - timedelta(weeks=10), refresh_date)
    assert len(updates) > 0
