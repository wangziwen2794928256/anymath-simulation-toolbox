#!/usr/bin/env python3
"""Diagnose codeload channel + read api rate/limits + resolve default branches."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

UA = {"User-Agent": "dsh-anymath-probe"}


def get(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read(200000)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read(500)
    except Exception as exc:  # noqa: BLE001
        return -1, {}, str(exc).encode()


print("=== api rate_limit ===")
s, h, b = get("https://api.github.com/rate_limit")
print(s, b.decode("utf-8", "replace")[:400])

print("\n=== codeload sanity (known repos) ===")
for slug in ["oxwhirl/epymarl", "kourgeorge/arxiv-style", "borisveytsman/acmart"]:
    for br in ["main", "master"]:
        url = f"https://codeload.github.com/{slug}/zip/refs/heads/{br}"
        s, h, b = get(url, timeout=60)
        print(f"{s:>5} {slug}@{br} bytes={len(b)} head={b[:80]!r}")

print("\n=== default branches (API, rate limited) ===")
for slug in [
    "NeurIPS/NeurIPS-2025",
    "NeurIPS/NeurIPS-2024",
    "mlresearch/icml2025",
    "aaai/aaai25",
    "borisveytsman/acmart",
]:
    s, h, b = get(f"https://api.github.com/repos/{slug}")
    if s == 200:
        d = json.loads(b)
        print(f"{s:>5} {slug} default_branch={d.get('default_branch')} size={d.get('size')}KB")
    else:
        print(f"{s:>5} {slug} {b.decode('utf-8','replace')[:120]}")
