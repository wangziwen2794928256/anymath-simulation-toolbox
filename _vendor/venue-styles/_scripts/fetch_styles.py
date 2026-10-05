#!/usr/bin/env python3
"""Download official venue LaTeX style kits into _vendor/venue-styles/<venue>/.

Records PROVENANCE.md per venue with the exact URL, byte count, sha256 and UTC time.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime
import hashlib
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile

ROOT = r"D:\anymath-and-simulation\_vendor\venue-styles"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) dsh-anymath"}

# (venue_dir, kind, url)  kind: zip | file
TARGETS = [
    # ---------------- NeurIPS ----------------
    ("neurips", "zip", "https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip"),
    ("neurips", "zip", "https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip"),
    ("neurips", "file", "https://neurips.cc/public/guides/PaperChecklist"),
    ("neurips", "file", "https://neurips.cc/Conferences/2025/CallForPapers"),
    # ---------------- ICML ----------------
    ("icml", "zip", "https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip"),
    ("icml", "file", "https://media.icml.cc/Conferences/ICML2025/Styles/example_paper.pdf"),
    ("icml", "zip", "https://media.icml.cc/Conferences/ICML2024/Styles/icml2024.zip"),
    ("icml", "file", "https://icml.cc/Conferences/2025/AuthorInstructions"),
    # ---------------- AAAI ----------------
    ("aaai", "zip", "https://aaai.org/authorkit25-2/"),
    # ---------------- ACM acmart ----------------
    ("acm-acmart", "zip", "https://mirrors.ctan.org/macros/latex/contrib/acmart.zip"),
    # ---------------- IEEEtran ----------------
    ("ieee-ieeetran", "zip", "https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip"),
    # ---------------- arxiv-style ----------------
    ("arxiv-style", "zip", "https://codeload.github.com/kourgeorge/arxiv-style/zip/refs/heads/master"),
]


def fetch(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def slug_for(url: str) -> str:
    tail = url.rstrip("/").split("/")[-1] or "index"
    tail = tail.split("?")[0]
    if "." not in tail:
        tail += ".html"
    return tail


def unzip_into(blob: bytes, dest: str) -> list[str]:
    """Extract, flattening a single top-level wrapper directory."""
    written: list[str] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
        roots = {n.split("/")[0] for n in names if n.split("/")[0]}
        strip = ""
        if len(roots) == 1 and all("/" in n for n in names if not n.endswith("/")):
            strip = roots.pop() + "/"
        for info in z.infolist():
            if info.is_dir():
                continue
            rel = info.filename[len(strip):] if info.filename.startswith(strip) else info.filename
            if not rel or rel.endswith("/"):
                continue
            target = os.path.join(dest, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                out.write(src.read())
            written.append(rel)
    return written


def main() -> int:
    records: list[dict] = []
    os.makedirs(ROOT, exist_ok=True)

    def work(target):
        venue, kind, url = target
        dest = os.path.join(ROOT, venue, "_raw")
        os.makedirs(dest, exist_ok=True)
        try:
            blob = fetch(url)
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", "")
            return {"venue": venue, "url": url, "ok": False, "note": f"{code} {str(exc)[:120]}"}
        sha = hashlib.sha256(blob).hexdigest()
        rec = {
            "venue": venue,
            "url": url,
            "ok": True,
            "bytes": len(blob),
            "sha256": sha,
            "kind": kind,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        }
        if kind == "zip":
            try:
                files = unzip_into(blob, dest)
                rec["files"] = files
                rec["path"] = os.path.join(dest, " (extracted)")
            except zipfile.BadZipFile:
                # Server returned something that is not a zip (e.g. an HTML redirect page)
                name = slug_for(url) + ".zip"
                p = os.path.join(dest, name)
                with open(p, "wb") as fh:
                    fh.write(blob)
                rec["ok"] = False
                rec["note"] = f"NOT A ZIP (saved as {name})"
                rec["path"] = p
        else:
            name = slug_for(url)
            p = os.path.join(dest, name)
            with open(p, "wb") as fh:
                fh.write(blob)
            rec["path"] = p
        return rec

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for rec in pool.map(work, TARGETS):
            records.append(rec)
            if rec["ok"]:
                n = len(rec.get("files", [])) or 1
                print(f"OK   {rec['venue']:<14} {rec['bytes']:>9,} B  {n:>3} files  {rec['url']}")
            else:
                print(f"FAIL {rec['venue']:<14} {rec.get('note','')}  {rec['url']}")

    with open(os.path.join(ROOT, "_download-manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)

    # per-venue PROVENANCE.md
    for venue in sorted({r["venue"] for r in records}):
        rows = [r for r in records if r["venue"] == venue]
        lines = [f"# {venue} — 官方样式文件来源 / source of truth", ""]
        for r in rows:
            lines.append(f"## {r['url']}")
            if r["ok"]:
                lines.append(f"- 本地路径: `{r['path']}`")
                lines.append(f"- 字节数: {r['bytes']:,}")
                lines.append(f"- sha256: `{r['sha256']}`")
                lines.append(f"- 获取时间(UTC): {r['utc']}")
                if r.get("files"):
                    lines.append(f"- 解压条目 ({len(r['files'])}):")
                    for f in sorted(r["files"]):
                        lines.append(f"  - `{f}`")
            else:
                lines.append(f"- **下载失败/异常**: {r.get('note','')}")
            lines.append("")
        with open(os.path.join(ROOT, venue, "PROVENANCE.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    bad = [r for r in records if not r["ok"]]
    print(f"\n完成: {len(records) - len(bad)}/{len(records)} 成功")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
