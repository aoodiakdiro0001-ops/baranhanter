"""EXIF scan of photos (YOUR OWN images): capture time + GPS if present."""
import os
from typing import Dict, List

from PIL import Image
from PIL.ExifTags import IFD

GPS_IFD = 0x8825


def _rational(v):
    try:
        return float(v)
    except Exception:
        return 0.0


def _dms_to_deg(dms, ref):
    try:
        d = _rational(dms[0]) + _rational(dms[1]) / 60.0 + _rational(dms[2]) / 3600.0
        if ref in ("S", "W"):
            d = -d
        return round(d, 6)
    except Exception:
        return ""


def scan_images(root):
    # type: (str) -> Dict[str, List[Dict]]
    events = []  # type: List[Dict]
    notes = []  # type: List[str]
    n = 0
    for dp, _dn, fns in os.walk(root):
        for fn in sorted(fns):
            if not fn.lower().endswith((".jpg", ".jpeg")):
                continue
            p = os.path.join(dp, fn)
            n += 1
            try:
                with Image.open(p) as im:
                    ex = im.getexif()
                taken = ex.get(36867, "")
                if not taken and hasattr(ex, "get_ifd"):
                    try:
                        taken = ex.get_ifd(0x8769).get(36867, "")
                    except Exception:
                        taken = ""
                taken = str(taken).replace(":", "-", 2)
                lat = lon = ""
                gps = ex.get_ifd(GPS_IFD) if hasattr(ex, "get_ifd") else {}
                if gps and 1 in gps and 2 in gps:
                    lat = _dms_to_deg(gps[2], gps.get(1))
                    lon = _dms_to_deg(gps.get(4), gps.get(3))
                events.append({
                    "time": taken.replace(" ", "T") if taken else "",
                    "source": "photo", "type": "photo",
                    "actor": "camera", "text": os.path.relpath(p, root),
                    "lat": lat, "lon": lon,
                })
            except Exception as ex2:
                notes.append("%s: %s" % (fn, ex2))
    notes.insert(0, "images_scanned=%d" % n)
    return {"events": events, "notes": notes}
