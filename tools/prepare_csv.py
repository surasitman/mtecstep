"""Prepare step-challenge CSV files for the public dashboard.

Usage
  python tools/prepare_csv.py path/to/raw-export.csv   # trim a raw export into data/ and rebuild the manifest
  python tools/prepare_csv.py                          # re-check every file in data/ and rebuild the manifest

What it does
  * keeps only rows where activityType is "steps" (or "step")
  * drops admin accounts (groupName containing "แอดมิน" or "admin")
  * keeps only the columns the dashboard needs; gender, weight, BMI,
    employeeId and every other column are removed
  * writes data/manifest.json, newest file first, which index.html reads on load

The repository is public: run this on a raw export BEFORE committing it,
so the removed columns never reach git history.
"""
import csv
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys

KEEP = ["date", "time", "firstname", "lastname", "groupId", "groupName", "activityType", "source", "steps"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def read_text(path):
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp874")


def parse_date(s):
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", s)
    if m:
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
    else:
        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
        if not m:
            return None
        y, mo, d = int(m[1]), int(m[2]), int(m[3])
    if y > 2400:
        y -= 543
    try:
        return dt.date(y, mo, d)
    except ValueError:
        return None


def trim(src, dst):
    rows = list(csv.DictReader(io.StringIO(read_text(src))))
    rows = [{(k or "").strip(): v for k, v in r.items()} for r in rows]
    missing = [c for c in ["date", "firstname", "lastname", "groupName", "activityType", "steps"] if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"{src}: missing columns {missing}")
    out = []
    for r in rows:
        if not re.fullmatch(r"steps?", (r.get("activityType") or "").strip(), re.I):
            continue
        if re.search(r"แอดมิน|admin", r.get("groupName") or "", re.I):
            continue
        out.append({k: (r.get(k) or "").strip() for k in KEEP})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=KEEP, lineterminator="\n")
    w.writeheader()
    w.writerows(out)
    new = "﻿" + buf.getvalue()
    old = read_text(dst) if os.path.exists(dst) else None
    if old is None or "﻿" + old != new:
        with open(dst, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print(f"wrote {os.path.relpath(dst, ROOT)}: {len(out)} rows")
    return out


def commit_time(path):
    try:
        t = subprocess.run(["git", "log", "-1", "--format=%cI", "--", path], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        t = ""
    return t or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def main(args):
    os.makedirs(DATA, exist_ok=True)
    for src in args:
        trim(src, os.path.join(DATA, os.path.basename(src)))
    files = []
    for name in sorted(os.listdir(DATA)):
        if not name.lower().endswith(".csv"):
            continue
        p = os.path.join(DATA, name)
        rows = trim(p, p)
        days = sorted({d for d in (parse_date(r["date"]) for r in rows) if d})
        files.append({
            "file": name,
            "updated": commit_time(p),
            "rows": len(rows),
            "from": days[0].isoformat() if days else None,
            "to": days[-1].isoformat() if days else None,
        })
    files.sort(key=lambda f: (f["updated"], f["to"] or ""), reverse=True)
    manifest = {"files": files}
    mp = os.path.join(DATA, "manifest.json")
    text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if not os.path.exists(mp) or open(mp, encoding="utf-8").read() != text:
        with open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote data/manifest.json")


if __name__ == "__main__":
    main(sys.argv[1:])
