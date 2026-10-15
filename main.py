#!/usr/bin/env python3
"""Baran Hanter CLI — logical backup analysis for YOUR OWN data.

Usage:
  python3 main.py demo                      # build fixtures + full pipeline
  python3 main.py run --ios BACKUP --wa CHAT --media DIR --out OUT --case NAME
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hanter import __version__
from hanter import exifmedia, hashes, ios_backup, report, timeline, whatsapp


def run_pipeline(ios_dir, wa_path, media_dir, out_dir, case):
    os.makedirs(out_dir, exist_ok=True)
    events, notes = [], []

    if ios_dir:
        r = ios_backup.parse_backup(ios_dir)
        events.extend(r["events"])
        notes.extend(["ios: " + n for n in r["notes"]])
    if wa_path:
        r = whatsapp.parse_export(wa_path)
        events.extend(r["events"])
        notes.extend(["whatsapp: " + n for n in r["notes"]])
    if media_dir:
        r = exifmedia.scan_images(media_dir)
        events.extend(r["events"])
        notes.extend(["media: " + n for n in r["notes"]])

    tl = timeline.build_timeline([events])
    csv_path = os.path.join(out_dir, "timeline.csv")
    timeline.write_csv(tl, csv_path)

    inputs = []
    if ios_dir:
        inputs.extend(hashes.collect_files(ios_dir))
    for p in (wa_path, media_dir):
        if p and os.path.isfile(p):
            inputs.append(p)
        elif p and os.path.isdir(p):
            inputs.extend(hashes.collect_files(p))
    man = hashes.manifest(inputs)

    html_path = os.path.join(out_dir, "report.html")
    report.write_html(case, tl, man, notes, "timeline.csv", html_path, __version__)

    print("case     : %s" % case)
    print("events   : %d" % len(tl))
    print("timeline : %s" % csv_path)
    print("report   : %s" % html_path)
    print("hashed   : %d files" % len(man))
    return {"events": tl, "manifest": man, "notes": notes,
            "csv": csv_path, "html": html_path}


def main():
    ap = argparse.ArgumentParser(prog="hanter")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo")
    r = sub.add_parser("run")
    r.add_argument("--ios", default="")
    r.add_argument("--wa", default="")
    r.add_argument("--media", default="")
    r.add_argument("--out", required=True)
    r.add_argument("--case", default="case-001")
    a = ap.parse_args()

    if a.cmd == "demo":
        from demo import make_fixtures
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "demo")
        fx = make_fixtures.build(os.path.join(base, "case_in"))
        res = run_pipeline(fx["ios"], fx["wa"], fx["media"],
                           os.path.join(base, "case_out"), "demo-case")
        make_fixtures.verify(res, fx)
        print("DEMO PASS — all assertions ok")
    else:
        run_pipeline(a.ios or "", a.wa or "", a.media or "", a.out, a.case)


if __name__ == "__main__":
    main()
