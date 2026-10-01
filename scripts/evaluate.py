"""Run a small real-model smoke evaluation; never substitutes mock inference."""

import argparse
import getpass
import json
import statistics
from pathlib import Path

import requests

parser = argparse.ArgumentParser()
parser.add_argument("--api", default="http://127.0.0.1:8000")
parser.add_argument("--provider", choices=["local", "cloud", "auto"], default="local")
args = parser.parse_args()
password = getpass.getpass("Demo password: ")
auth = requests.post(
    args.api + "/api/v1/auth/token", json={"username": "reviewer", "password": password}, timeout=10
)
auth.raise_for_status()
headers = {"Authorization": "Bearer " + auth.json()["access_token"]}
rows = []
for sample in json.loads(Path("examples/tickets.json").read_text()):
    response = requests.post(
        args.api + "/api/v1/tickets/triage",
        headers=headers,
        json={
            "subject": sample["subject"],
            "description": sample["description"],
            "provider": args.provider,
        },
        timeout=110,
    )
    row = {"scenario": sample["name"], "http_status": response.status_code}
    if response.ok:
        data = response.json()
        row.update(
            category_correct=data["triage"]["category"] == sample["category"],
            priority_correct=data["triage"]["priority"] == sample["priority"],
            result=data,
        )
    rows.append(row)
    print(sample["name"], response.status_code)
latencies = [r["result"]["metadata"]["latency_ms"] for r in rows if "result" in r]
report = {
    "sample_count": len(rows),
    "schema_valid_count": len(latencies),
    "category_correct": sum(r.get("category_correct", False) for r in rows),
    "priority_correct": sum(r.get("priority_correct", False) for r in rows),
    "median_latency_ms": statistics.median(latencies) if latencies else None,
    "cases": rows,
}
Path("reports").mkdir(exist_ok=True)
Path("reports/evaluation.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
