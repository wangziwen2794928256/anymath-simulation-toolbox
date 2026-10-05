#!/usr/bin/env python3
"""Discover authoritative style-file repos via GitHub API search (rate limited: 10/min)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = {"User-Agent": "dsh-anymath-probe"}


def get(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(400000)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(500)
    except Exception as exc:  # noqa: BLE001
        return -1, str(exc).encode()


def search(q: str, kind: str = "repositories", sort: str = "stars"):
    url = (
        f"https://api.github.com/search/{kind}?"
        + urllib.parse.urlencode({"q": q, "per_page": 8, "sort": sort})
    )
    s, b = get(url)
    print(f"\n### [{s}] {kind}: {q}")
    if s != 200:
        print("   ", b.decode("utf-8", "replace")[:200])
        return
    d = json.loads(b)
    print(f"    total_count={d.get('total_count')}")
    for it in d.get("items", []):
        if kind == "repositories":
            print(f"    - {it['full_name']:<45} br={it.get('default_branch')} stars={it.get('stargazers_count')} :: {(it.get('description') or '')[:80]}")
        else:
            print(f"    - {it['repository']['full_name']:<40} {it['path']}")


for q in [
    "org:NeurIPS",
    "user:mlresearch",
    "aaai25 in:name",
    "aamas.cls in:path",
    "neurips_2025.sty in:path",
    "icml2025.sty in:path",
]:
    search(q, "repositories")
    time.sleep(7)

search("filename:neurips_2025.sty", "code")
time.sleep(7)
search("filename:aamas.cls", "code")
