# 🕵️ Baran Hanter — Logical Backup Analyzer (v0.1.0)

Designed & built by **Baran Avisat** (Professional Programmer).
📧 baranavisat@gmail.com · 📞 +90 531 326 37 22 · [WhatsApp](https://wa.me/905313263722) ·
Support: BTC `bc1q8dhtdrndxsl70e97t8grydfe6pjue37zrhzf6c` · USDT-TRC20 `TLWdTjqqogkXNEXGiPWsGdjFP6ioycxeWW`
(see [SUPPORT.md](SUPPORT.md) — wallets, IBAN (soon), phone, email)

## LEGAL — your own data, authorized analysis only

Analyze backups/exports of **your own devices** or data you are explicitly
authorized to examine (e.g. your incident response, your lab). No lock
bypassing, no exploits, no credential theft — this tool only **reads**
files you already possess, read-only, and hashes everything for
chain of custody.

## What it does (honest scope)

| Stage | Covered |
|---|---|
| iTunes/Finder backup → SMS, contacts, call log | ✅ `hanter/ios_backup.py` |
| WhatsApp chat export (.txt, iOS+Android formats) | ✅ `hanter/whatsapp.py` |
| Photo EXIF time + GPS | ✅ `hanter/exifmedia.py` |
| Merged chronological timeline (CSV) | ✅ `hanter/timeline.py` |
| SHA-256 manifest + HTML report with owner credit | ✅ `hanter/hashes.py`, `hanter/report.py` |
| Physical bit-by-bit imaging, lock bypass, deleted-data carving, AI face recognition | ❌ out of scope (commercial-lab hardware territory) |

## Run

```bash
cd baranhanter
pip install -r requirements.txt
python3 main.py demo     # builds fake fixtures, runs full pipeline, asserts
python3 main.py run --ios /path/to/backup --wa chat.txt --media ./photos \
    --out ./case_out --case case-001
```

Outputs: `timeline.csv` + `report.html` (print to PDF from the browser).
