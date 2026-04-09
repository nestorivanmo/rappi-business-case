import csv
import os
from datetime import datetime

from app.budget.models import Intervention

FIELDNAMES = [
    "id",
    "kam_name",
    "restaurant_id",
    "timestamp",
    "amount_mxn",
    "category",
    "quadrant_at_time",
    "health_score_at_time",
    "description",
    "revenue_7d_before",
    "revenue_7d_after",
]


def load_interventions(path: str) -> list[Intervention]:
    if not os.path.exists(path):
        return []
    interventions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["amount_mxn"] = float(row["amount_mxn"])
            row["health_score_at_time"] = float(row["health_score_at_time"])
            row["revenue_7d_before"] = float(row["revenue_7d_before"])
            row["revenue_7d_after"] = (
                float(row["revenue_7d_after"]) if row.get("revenue_7d_after") else None
            )
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            interventions.append(Intervention(**row))
    return interventions


def save_intervention(intervention: Intervention, path: str) -> None:
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        row = intervention.model_dump()
        row["timestamp"] = row["timestamp"].isoformat()
        writer.writerow(row)
