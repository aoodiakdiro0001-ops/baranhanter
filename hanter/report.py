"""HTML forensic report with hash manifest + timeline + owner credit."""
import html
from typing import Dict, List

OWNER_HTML = (
    "Designed &amp; built by <b>Baran Avisat</b> (Professional Programmer) · "
    "baranavisat@gmail.com · +90 531 326 37 22 · "
    "<a href='https://wa.me/905313263722'>WhatsApp</a>"
)


def _esc(v):
    return html.escape("" if v is None else str(v))


def write_html(case, events, manifest, notes, timeline_csv, out_path, tool_version):
    # type: (str, List[Dict], List[Dict], List[str], str, str, str) -> None
    mrows = []
    for m in manifest:
        mrows.append("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>" % (
            _esc(m["path"]), _esc(m["bytes"]), _esc(m["sha256"])))
    mrows = "".join(mrows)
    trows = []
    for e in events:
        if e.get("lat") != "" and e.get("lon") != "":
            gps = ("<a href='https://maps.google.com/?q=%s,%s'>%s,%s</a>" % (
                e.get("lat"), e.get("lon"), e.get("lat"), e.get("lon")))
        else:
            gps = ""
        trows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                _esc(e.get("time")), _esc(e.get("source")),
                _esc(e.get("type")), _esc(e.get("actor")), gps,
                _esc(str(e.get("text", ""))[:300])))
    trows = "".join(trows)
    nlist = "".join("<li>%s</li>" % _esc(n) for n in notes)
    doc = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Baran Hanter Report — {case}</title>
<style>body{{font-family:monospace;max-width:1000px;margin:auto;padding:20px;
background:#0b0e17;color:#e3e9f5}}table{{border-collapse:collapse;width:100%;
font-size:12px}}td,th{{border:1px solid #2a3557;padding:6px;text-align:left}}
a{{color:#34d399}}h1,h2{{color:#fff}}.foot{{color:#9aa0a6;font-size:12px;
border-top:1px solid #2a3557;margin-top:20px;padding-top:10px}}</style>
</head><body>
<h1>🕵️ Baran Hanter — Case Report</h1>
<p>Case: <b>{case}</b> · Tool: Baran Hanter {ver} · Events: <b>{n}</b> ·
Timeline: {csv}</p>
<h2>1. Chain of custody (SHA-256)</h2>
<table><tr><th>File</th><th>Bytes</th><th>SHA-256</th></tr>{mrows}</table>
<h2>2. Timeline ({n} events)</h2>
<table><tr><th>Time</th><th>Source</th><th>Type</th><th>Actor</th>
<th>GPS</th><th>Detail</th></tr>{trows}</table>
<h2>3. Parser notes</h2><ul>{nlist}</ul>
<p class="foot">{owner}<br>
LEGAL: analysis of your own devices / data with explicit authorization only.
© Baran Avisat — Baran Hanter.</p>
</body></html>""".format(
        case=_esc(case), ver=_esc(tool_version), n=len(events),
        csv=_esc(timeline_csv), mrows=mrows or "<tr><td>-</td></tr>",
        trows=trows or "<tr><td>-</td></tr>", nlist=nlist or "<li>-</li>",
        owner=OWNER_HTML,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(doc)
