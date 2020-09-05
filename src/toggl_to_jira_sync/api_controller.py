import datetime

import flask

from . import api_service, service


def api_routes(app):
    @app.route("/api/diff/get", methods=["GET"])
    def api_get_diff():
        date_max, date_min = _get_date_args()

        result = api_service.inspect_interval(date_min, date_max)
        aggregated_actions = [
            action
            for row in result["rows"]
            for action in row["actions"]
        ]
        return flask.jsonify(_format_day(aggregated_actions, date_max, date_min, result))

    @app.route("/api/diff/sync", methods=["POST"])
    def api_sync_diff():
        date_max, date_min = _get_date_args()
        result = api_service.inspect_interval(date_min, date_max)
        aggregated_actions = [
            action
            for row in result["rows"]
            for action in row["actions"]
        ]
        for action in aggregated_actions:
            service.ActionExecutor().execute(action)
        return flask.jsonify({"result": "ok"})


def _get_date_args():
    date_min = flask.request.args.get("min", None)
    date_min = datetime.datetime.fromisoformat(date_min)
    date_max = flask.request.args.get("max", None)
    date_max = datetime.datetime.fromisoformat(date_max)
    return date_max, date_min


def _format_day(aggregated_actions, date_max, date_min, result):
    return {
        "date_min": _format_date(date_min),
        "date_max": _format_date(date_max),
        "actions": aggregated_actions,
        "rows": [{
            "actions": row["actions"],
            "toggl": _format_toggl(row.get("toggl")),
            "jira": _format_jira(row.get("jira")),
            "messages": [{
                "text": m.message,
                "level": m.level
            } for m in row["messages"]],
            "dist": row["dist"],
        } for row in result["rows"]],
        "projects": result["projects"],
        "entries": result["entries"],
    }


def _format_toggl(data):
    if data is None:
        return None
    return {
        "comment": data.comment,
        "time_start": _format_date(data.start),
        "time_length": str(data.stop - data.start),
        "id": data.tag.id,
        "project_name": data.tag.project_name,
        "billable": data.tag.billable,
    }


def _format_jira(data):
    if data is None:
        return None
    return {
        "comment": data.comment,
        "time_start": _format_date(data.start),
        "time_length": str(data.stop - data.start),
        "id": data.tag.id,
        "issue": data.issue,
    }


def _format_date(dt: datetime.datetime):
    if dt is None:
        return None
    return dt.isoformat()