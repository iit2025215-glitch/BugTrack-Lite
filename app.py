
from flask import Flask, render_template

app = Flask(__name__)

bugs = [
    {
        "id": 1,
        "title": "Login button not working",
        "project": "Student Portal",
        "severity": "Critical",
        "status": "Open"
    },
    {
        "id": 2,
        "title": "Incorrect dashboard statistics",
        "project": "BugTrack Lite",
        "severity": "High",
        "status": "In Progress"
    },
    {
        "id": 3,
        "title": "Profile image not loading",
        "project": "Student Portal",
        "severity": "Medium",
        "status": "Resolved"
    },
    {
        "id": 4,
        "title": "Typo in registration form",
        "project": "BugTrack Lite",
        "severity": "Low",
        "status": "Open"
    }
]

@app.route("/")
def home():
    return render_template("dashboard.html", bugs=bugs)

if __name__ == "__main__":
    app.run(debug=True)
