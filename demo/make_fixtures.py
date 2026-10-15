"""Build synthetic fixtures (clearly fake data) + verify the pipeline."""
import hashlib
import os
import shutil
import sqlite3
from datetime import datetime, timedelta

import piexif
from PIL import Image

APPLE_EPOCH = datetime(2001, 1, 1)


def _fid(domain, rel):
    return hashlib.sha1(("%s-%s" % (domain, rel)).encode()).hexdigest()


def _put_blob(backup_dir, domain, rel, src):
    fid = _fid(domain, rel)
    dest = os.path.join(backup_dir, fid[:2], fid)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(src, dest)


def _to_ns(dt):
    return int((dt - APPLE_EPOCH).total_seconds() * 1e9)


def _to_coredata(dt):
    return (dt - APPLE_EPOCH).total_seconds()


def build(root):
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)

    # ---- fake iTunes backup ----
    backup = os.path.join(root, "iphone_backup")
    os.makedirs(backup)
    work = os.path.join(root, "_work")
    os.makedirs(work)

    sms = os.path.join(work, "sms.db")
    con = sqlite3.connect(sms)
    con.execute("CREATE TABLE handle (ROWID INTEGER PRIMARY KEY, id TEXT)")
    con.execute("CREATE TABLE message (ROWID INTEGER PRIMARY KEY, text TEXT,"
                " date INTEGER, is_from_me INTEGER, handle_id INTEGER)")
    con.execute("INSERT INTO handle VALUES (1, '+900000000001')")
    t1 = datetime(2024, 3, 12, 10, 0, 0)
    t2 = datetime(2024, 3, 12, 10, 5, 0)
    con.execute("INSERT INTO message VALUES (1, 'demo sms inbound', ?, 0, 1)",
                (_to_ns(t1),))
    con.execute("INSERT INTO message VALUES (2, 'demo sms outbound', ?, 1, 1)",
                (_to_ns(t2),))
    con.commit()
    con.close()

    ab = os.path.join(work, "AddressBook.sqlitedb")
    con = sqlite3.connect(ab)
    con.execute("CREATE TABLE ABPerson (ROWID INTEGER PRIMARY KEY,"
                " First TEXT, Last TEXT)")
    con.execute("INSERT INTO ABPerson VALUES (1, 'Demo', 'Contact')")
    con.commit()
    con.close()

    ch = os.path.join(work, "CallHistory.storedata")
    con = sqlite3.connect(ch)
    con.execute("CREATE TABLE ZCALLRECORD (ZDATE REAL, ZDURATION REAL,"
                " ZADDRESS TEXT)")
    con.execute("INSERT INTO ZCALLRECORD VALUES (?, 61, '+900000000001')",
                (_to_coredata(datetime(2024, 3, 12, 9, 30, 0)),))
    con.commit()
    con.close()

    man = os.path.join(backup, "Manifest.db")
    con = sqlite3.connect(man)
    con.execute("CREATE TABLE Files (fileID TEXT PRIMARY KEY, domain TEXT,"
                " relativePath TEXT, flags INTEGER, file BLOB)")
    for domain, rel, src in [
            ("HomeDomain", "Library/SMS/sms.db", sms),
            ("HomeDomain", "Library/AddressBook/AddressBook.sqlitedb", ab),
            ("WirelessDomain", "Library/CallHistoryDB/CallHistory.storedata", ch)]:
        con.execute("INSERT INTO Files VALUES (?, ?, ?, 1, zeroblob(1))",
                    (_fid(domain, rel), domain, rel))
        _put_blob(backup, domain, rel, src)
    con.commit()
    con.close()

    # ---- fake WhatsApp export (both phone formats) ----
    wa = os.path.join(root, "whatsapp_chat.txt")
    with open(wa, "w", encoding="utf-8") as f:
        f.write("[12/03/2024, 10:15:22] Demo User: hello from ios format\n")
        f.write("continued line of same message\n")
        f.write("12/03/2024, 10:16 - Demo User: hello from android format\n")

    # ---- fake photo with GPS EXIF ----
    media = os.path.join(root, "photos")
    os.makedirs(media)
    img = Image.new("RGB", (32, 32), (200, 30, 30))
    photo_path = os.path.join(media, "IMG_demo.jpg")
    img.save(photo_path)
    exif_dict = {
        "0th": {}, "Interop": {}, "1st": {}, "thumbnail": None,
        "Exif": {piexif.ExifIFD.DateTimeOriginal: "2024:03:12 10:20:00"},
        "GPS": {
            piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: "N",
            piexif.GPSIFD.GPSLatitude: ((38, 1), (55, 1), (6, 1)),
            piexif.GPSIFD.GPSLongitudeRef: "E",
            piexif.GPSIFD.GPSLongitude: ((27, 1), (25, 1), (30, 1)),
        },
    }
    piexif.insert(piexif.dump(exif_dict), photo_path)

    return {"ios": backup, "wa": wa, "media": media}


def verify(res, fx):
    ev = res["events"]
    assert len(ev) == 7, "expected 7 events, got %d" % len(ev)
    srcs = sorted(set(e["source"] for e in ev))
    assert srcs == ["ios-calls", "ios-contacts", "ios-sms", "photo", "whatsapp"], srcs
    times = [e["time"] for e in ev if e["time"]]
    assert times == sorted(times), "timeline not sorted"
    wa_texts = [e["text"] for e in ev if e["source"] == "whatsapp"]
    assert any("continued line" in t for t in wa_texts), "multiline join failed"
    photo = [e for e in ev if e["source"] == "photo"][0]
    assert abs(float(photo["lat"]) - 38.918333) < 0.001, photo
    assert abs(float(photo["lon"]) - 27.425) < 0.001, photo
    assert len(res["manifest"]) >= 6, res["manifest"]
    html = open(res["html"], encoding="utf-8").read()
    assert "Baran Avisat" in html and "timeline.csv" in html
    assert os.path.exists(res["csv"])
