"""Parse an iTunes/Finder iPhone backup directory (YOUR OWN backup).

Real layout: Manifest.db (Files: fileID=sha1(domain-relativePath),
backup blob at fileID[:2]/fileID). We parse SMS + contacts + call log.
Read-only: never writes into the backup.
"""
import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List

APPLE_EPOCH = datetime(2001, 1, 1)


def file_id(domain, rel):
    # type: (str, str) -> str
    return hashlib.sha1(("%s-%s" % (domain, rel)).encode()).hexdigest()


def blob_path(backup_dir, fid):
    # type: (str, str) -> str
    return os.path.join(backup_dir, fid[:2], fid)


def _ns_to_iso(ns):
    # type: (object) -> str
    try:
        return (APPLE_EPOCH + timedelta(seconds=float(ns) / 1e9)).isoformat()
    except Exception:
        return ""


def _coredata_to_iso(ts):
    # type: (object) -> str
    try:
        return (APPLE_EPOCH + timedelta(seconds=float(ts))).isoformat()
    except Exception:
        return ""


def parse_backup(backup_dir):
    # type: (str) -> Dict[str, List[Dict]]
    events = []  # type: List[Dict]
    notes = []  # type: List[str]

    man = os.path.join(backup_dir, "Manifest.db")
    if not os.path.exists(man):
        return {"events": events, "notes": ["Manifest.db not found: %s" % man]}

    # --- SMS (HomeDomain-Library/SMS/sms.db) ---
    sms_id = file_id("HomeDomain", "Library/SMS/sms.db")
    sms_path = blob_path(backup_dir, sms_id)
    if os.path.exists(sms_path):
        try:
            con = sqlite3.connect("file:%s?mode=ro" % sms_path, uri=True)
            cur = con.cursor()
            cur.execute(
                "SELECT m.text, m.date, m.is_from_me, h.id "
                "FROM message m LEFT JOIN handle h ON h.ROWID=m.handle_id "
                "ORDER BY m.date"
            )
            for text, date, frm, handle in cur.fetchall():
                events.append({
                    "time": _ns_to_iso(date), "source": "ios-sms",
                    "type": "sms",
                    "actor": "me" if frm else (handle or "unknown"),
                    "text": text or "",
                    "lat": "", "lon": "",
                })
            con.close()
        except Exception as ex:
            notes.append("sms.db parse failed: %s" % ex)
    else:
        notes.append("sms.db blob absent (no SMS in this backup)")

    # --- Contacts (HomeDomain-Library/AddressBook/AddressBook.sqlitedb) ---
    ab_id = file_id("HomeDomain", "Library/AddressBook/AddressBook.sqlitedb")
    ab_path = blob_path(backup_dir, ab_id)
    if os.path.exists(ab_path):
        try:
            con = sqlite3.connect("file:%s?mode=ro" % ab_path, uri=True)
            cur = con.cursor()
            cur.execute("SELECT First, Last FROM ABPerson ORDER BY ROWID")
            for first, last in cur.fetchall():
                events.append({
                    "time": "", "source": "ios-contacts",
                    "type": "contact",
                    "actor": " ".join([x for x in [first, last] if x]),
                    "text": "", "lat": "", "lon": "",
                })
            con.close()
        except Exception as ex:
            notes.append("AddressBook parse failed: %s" % ex)
    else:
        notes.append("AddressBook blob absent")

    # --- Call history (WirelessDomain-Library/CallHistoryDB/CallHistory.storedata) ---
    ch_id = file_id("WirelessDomain", "Library/CallHistoryDB/CallHistory.storedata")
    ch_path = blob_path(backup_dir, ch_id)
    if os.path.exists(ch_path):
        try:
            con = sqlite3.connect("file:%s?mode=ro" % ch_path, uri=True)
            cur = con.cursor()
            cur.execute("SELECT ZDATE, ZDURATION, ZADDRESS FROM ZCALLRECORD ORDER BY ZDATE")
            for zdate, dur, addr in cur.fetchall():
                events.append({
                    "time": _coredata_to_iso(zdate), "source": "ios-calls",
                    "type": "call",
                    "actor": addr or "unknown",
                    "text": "duration=%ss" % (dur if dur is not None else "?"),
                    "lat": "", "lon": "",
                })
            con.close()
        except Exception as ex:
            notes.append("CallHistory parse failed: %s" % ex)
    else:
        notes.append("CallHistory blob absent")

    return {"events": events, "notes": notes}
