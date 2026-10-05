#!/usr/bin/env python3
"""Hunt for the AAMAS proceedings style file across plausible hosts."""
from __future__ import annotations

import concurrent.futures as cf
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) dsh-anymath"}

CANDIDATES = [
    "https://www.ifaamas.org/Proceedings/aamas2025/forms/aamas2025.sty",
    "https://www.ifaamas.org/Proceedings/aamas2025/forms/aamas.cls",
    "https://www.ifaamas.org/Proceedings/aamas2024/forms/aamas2024.sty",
    "https://www.ifaamas.org/Proceedings/aamas2023/forms/aamas2023.sty",
    "https://www.ifaamas.org/Proceedings/aamas2022/forms/aamas2022.sty",
    "https://www.ifaamas.org/Proceedings/aamas2025/aamas2025.zip",
    "https://www.ifaamas.org/aamas2025/aamas2025.zip",
    "https://www.ifaamas.org/authorinfo.html",
    "https://www.ifaamas.org/",
    "https://aamas2025.org/index.php/conference/calls/submission-instructions-main-technical-track/",
    "https://aamas2025.org/index.php/conference/calls/",
    "https://www.aamas2025.org/",
    "https://raw.githubusercontent.com/ifaamas/aamas2025/main/aamas2025.sty",
    "https://mirrors.ctan.org/macros/latex/contrib/acmart/",
    "https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/",
    "https://mirrors.ctan.org/macros/latex/contrib/simulations/",
    "https://mirrors.ctan.org/macros/latex/contrib/",
]


def probe(url: str):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            b = resp.read(1024)
            return url, resp.status, f"{resp.headers.get('content-type','')} len={resp.headers.get('content-length','?')}"
    except urllib.error.HTTPError as exc:
        return url, exc.code, str(exc)[:60]
    except Exception as exc:  # noqa: BLE001
        return url, -1, str(exc)[:60]


with cf.ThreadPoolExecutor(max_workers=8) as pool:
    for url, st, note in pool.map(probe, CANDIDATES):
        print(f"{st:>5}  {note:<52} {url}")
