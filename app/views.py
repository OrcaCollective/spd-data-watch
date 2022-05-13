import re

from flask import (
    Blueprint,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
)

import app.updater as updater
from app.lookup import find_case
from app.models import Refresh, Update


views = Blueprint("app", __name__)


@views.before_request
def before():
    updater.update()


@views.route("/")
def index():
    return render_template("index.html")


@views.route("/refreshes")
def refreshes():
    page = request.args.get("page", 1, type=int)
    refreshes = Refresh.query.order_by(Refresh.refresh_date.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"]
    )
    return render_template("refreshes.html", refreshes=refreshes)


@views.route("/refreshes.json")
def refreshes_json():
    refreshes = Refresh.query.all()
    return jsonify([refresh.to_dict() for refresh in refreshes])


@views.route("/updates")
def updates():
    # Pagination example: https://betterprogramming.pub/simple-flask-pagination-example-4190b12c2e2e
    page = request.args.get("page", 1, type=int)
    updates = Update.query.order_by(
        Update.create_date.desc(), Update.event_date.desc()
    ).paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"])
    return render_template("updates.html", updates=updates)


@views.route("/updates.json")
def updates_json():
    updates = Update.query.all()  # TODO: trim to last 30 days?
    return jsonify([update.to_dict() for update in updates])


@views.route("/updates/<id>")
def update(id):
    update = Update.query.filter_by(id=id).one_or_none()
    if not update:
        return "Update not found", 404
    return render_template("update.html", update=update)


@views.route("/case")
def case():
    case_num = request.args.get("id", type=str)
    if not case_num or not re.match("^\\d{4}OPA-\\d{4}$", case_num):
        return "Invalid case number", 400

    result = find_case(case_num)
    if not result:
        return "Case not found", 404
    return render_template("case.html", case=result)


@views.route("/updates.xml")
def updates_atom():
    updates = Update.query.order_by(
        Update.create_date.desc(), Update.id.desc()
    ).all()  # TODO: trim to last 30 days?
    last_refresh = Refresh.last_refresh()

    resp = make_response(
        render_template(
            "updates.xml.j2", updates=updates, last_update=last_refresh.refresh_date
        )
    )
    resp.headers["Content-Type"] = "application/atom+xml; charset=utf-8"
    return resp


@views.route("/robots.txt")
def robots():
    return render_template("robots.txt")
