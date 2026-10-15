"""Merge events into one chronological timeline + CSV."""
import csv
from typing import Dict, List

FIELDS = ["time", "source", "type", "actor", "text", "lat", "lon"]


def build_timeline(event_lists):
    # type: (List[List[Dict]]) -> List[Dict]
    all_ev = []  # type: List[Dict]
    for lst in event_lists:
        all_ev.extend(lst)
    all_ev.sort(key=lambda e: (e.get("time") or ""))
    return all_ev


def write_csv(events, path):
    # type: (List[Dict], str) -> None
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for e in events:
            row = dict(e)
            row["text"] = str(row.get("text", ""))[:500]
            w.writerow(row)
