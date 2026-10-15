"""Parse a WhatsApp 'Export chat' .txt file (YOUR OWN export).

Handles both common formats:
  [12/03/2024, 10:15:22] Name: message   (iOS)
  12/03/2024, 10:15 - Name: message      (Android)
"""
import re
from datetime import datetime
from typing import Dict, List

_PATTERNS = [
    # [d/m/Y, H:M:S] Name: text
    re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.*)$"),
    # d/m/Y, H:M - Name: text
    re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(.*)$"),
]


def _parse_dt(d, t):
    # type: (str, str) -> str
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
                "%d/%m/%y %H:%M:%S", "%d/%m/%y %H:%M",
                "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime("%s %s" % (d, t), fmt).isoformat()
        except ValueError:
            continue
    return ""


def parse_export(path):
    # type: (str) -> Dict[str, List[Dict]]
    events = []  # type: List[Dict]
    skipped = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = None
            for rx in _PATTERNS:
                m = rx.match(line)
                if m:
                    break
            if not m:
                # continuation of previous multi-line message
                if events:
                    events[-1]["text"] += "\n" + line
                else:
                    skipped += 1
                continue
            date_s, time_s, rest = m.group(1), m.group(2), m.group(3)
            if ": " in rest:
                actor, text = rest.split(": ", 1)
            else:
                actor, text = "system", rest
            events.append({
                "time": _parse_dt(date_s, time_s), "source": "whatsapp",
                "type": "message", "actor": actor.strip(),
                "text": text.strip(), "lat": "", "lon": "",
            })
    return {"events": events, "notes": ["skipped_lines=%d" % skipped]}
