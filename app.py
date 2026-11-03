from flask import Flask, render_template, request, jsonify

from database.db import (
    initialize_database,
    get_all_bugs,
    get_bug_statistics,
    create_bug,
    get_bug,
    update_bug,
    update_bug_status,
    delete_bug,
    add_comment,
    get_bug_comments,
    get_bug_activity,
    get_projects,
)

app = Flask(__name__)

initialize_database()

STATUSES = ["Open", "In Progress", "Resolved"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]


@app.get("/")
def dashboard():
    filters = {
        "search": request.args.get("search", "").strip(),
        "status": request.args.get("status", ""),
        "severity": request.args.get("severity", ""),
        "project": request.args.get("project", ""),
        "sort": request.args.get("sort", "newest"),
    }

    bugs = get_all_bugs(**filters)
    stats = get_bug_statistics()
    projects = get_projects()

    return render_template(
        "dashboard.html",
        bugs=bugs,
        stats=stats,
        projects=projects,
        filters=filters,
        statuses=STATUSES,
        severities=SEVERITIES,
    )


@app.post("/api/bugs")
def api_create_bug():
    data = request.get_json(silent=True) or {}

    required = ["title", "description", "project", "severity"]

    if any(not str(data.get(key, "")).strip() for key in required):
        return jsonify(error="Please complete all required fields."), 400

    if data["severity"] not in SEVERITIES:
        return jsonify(error="Invalid severity."), 400

    bug_id = create_bug(data)

    return jsonify(
        message="Issue created.",
        id=bug_id
    ), 201


@app.get("/api/bugs/<int:bug_id>")
def api_get_bug(bug_id):
    bug = get_bug(bug_id)

    if not bug:
        return jsonify(error="Issue not found."), 404

    bug["comments"] = get_bug_comments(bug_id)
    bug["activity"] = get_bug_activity(bug_id)

    return jsonify(bug)


@app.put("/api/bugs/<int:bug_id>")
def api_update_bug(bug_id):
    data = request.get_json(silent=True) or {}

    required = ["title", "description", "project", "severity"]

    if any(not str(data.get(key, "")).strip() for key in required):
        return jsonify(error="Please complete all required fields."), 400

    if data["severity"] not in SEVERITIES:
        return jsonify(error="Invalid severity."), 400

    if not get_bug(bug_id):
        return jsonify(error="Issue not found."), 404

    update_bug(bug_id, data)

    return jsonify(message="Issue updated.")


@app.patch("/api/bugs/<int:bug_id>/status")
def api_update_status(bug_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status", "")

    if status not in STATUSES:
        return jsonify(error="Invalid status."), 400

    if not get_bug(bug_id):
        return jsonify(error="Issue not found."), 404

    update_bug_status(bug_id, status)

    return jsonify(message="Status updated.")


@app.delete("/api/bugs/<int:bug_id>")
def api_delete_bug(bug_id):
    if not get_bug(bug_id):
        return jsonify(error="Issue not found."), 404

    delete_bug(bug_id)

    return jsonify(message="Issue deleted.")


@app.post("/api/bugs/<int:bug_id>/comments")
def api_add_comment(bug_id):
    data = request.get_json(silent=True) or {}

    body = str(data.get("body", "")).strip()
    author = str(data.get("author", "You")).strip() or "You"

    if not body:
        return jsonify(error="Comment cannot be empty."), 400

    if not get_bug(bug_id):
        return jsonify(error="Issue not found."), 404

    add_comment(bug_id, author, body)

    return jsonify(message="Comment added."), 201


if __name__ == "__main__":
    app.run(debug=True)