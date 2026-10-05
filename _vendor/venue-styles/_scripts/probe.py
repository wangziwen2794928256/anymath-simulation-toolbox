#!/usr/bin/env python3
"""Probe reachability of candidate sources for venue style kits."""
from __future__ import annotations

import concurrent.futures as cf
import urllib.error
import urllib.request

UA = {"User-Agent": "dsh-anymath-probe"}

URLS = [
    # GitHub codeload (channel 1)
    ("codeload/neurips-2025", "https://codeload.github.com/NeurIPS/NeurIPS-2025/main"),
    ("codeload/neurips-2024", "https://codeload.github.com/NeurIPS/NeurIPS-2024/main"),
    ("codeload/neurips-anon", "https://codeload.github.com/NeurIPS/NeurIPS-Anonymous-Code-Submission/main"),
    ("codeload/icml-2025", "https://codeload.github.com/mlresearch/icml2025/main"),
    ("codeload/icml-2024", "https://codeload.github.com/mlresearch/icml2024/main"),
    ("codeload/icml-2023", "https://codeload.github.com/mlresearch/icml2023/main"),
    ("codeload/aaai25", "https://codeload.github.com/aaai/aaai25/main"),
    ("codeload/acmart", "https://codeload.github.com/borisveytsman/acmart/main"),
    ("codeload/arxiv-style", "https://codeload.github.com/kourgeorge/arxiv-style/main"),
    # raw (channel 3)
    ("raw/acmart", "https://raw.githubusercontent.com/borisveytsman/acmart/master/acmart.dtx"),
    # CTAN mirrors
    ("ctan/mirrors/acmart", "https://mirrors.ctan.org/macros/latex/contrib/acmart.zip"),
    ("ctan/mirrors/IEEEtran", "https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip"),
    ("ctan/org/acmart", "https://ctan.org/pkg/acmart"),
    # API (channel 2, rate limited)
    ("api/rate", "https://api.github.com/rate_limit"),
]


def head(name: str, url: str) -> tuple[str, str, int, str]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read(4096)
            return name, url, resp.status, f"{len(data)}B+ ct={resp.headers.get('content-type','')} ctlen={resp.headers.get('content-length','?')}"
    except urllib.error.HTTPError as exc:
        return name, url, exc.code, str(exc)[:90]
    except Exception as exc:  # noqa: BLE001
        return name, url, -1, str(exc)[:90]


with cf.ThreadPoolExecutor(max_workers=8) as pool:
    for name, url, status, note in pool.map(lambda t: head(*t), URLS):
        print(f"{status:>5}  {name:<26} {note}")
