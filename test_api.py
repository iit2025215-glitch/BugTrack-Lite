
import urllib.request
import json

url = "http://127.0.0.1:5000/api/bugs"

data = {
    "title": "Search button not working",
    "description": "Clicking search does not show any results.",
    "project": "BugTrack Lite",
    "severity": "High"
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(request) as response:
    print("Status:", response.status)
    print("Response:", response.read().decode("utf-8"))
