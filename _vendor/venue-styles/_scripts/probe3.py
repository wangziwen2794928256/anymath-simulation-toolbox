#!/usr/bin/env python3
"""Probe official conference-site / Overleaf URLs for style kits."""
from __future__ import annotations

import concurrent.futures as cf
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) dsh-anymath"}

URLS = [
    ("neurips-2025-media", "https://neurips.cc/media/neurips-2025/Styles.zip"),
    ("neurips-2024-media", "https://neurips.cc/media/neurips-2024/Styles.zip"),
    ("neurips-2025-media2", "https://neurips.cc/media/neurips-2025/neurips_2025.sty"),
    ("neurips-2024-media2", "https://neurips.cc/media/neurips-2024/neurips_2024.sty"),
    ("neurips-2023-media", "https://neurips.cc/media/neurips-2023/Styles.zip"),
    ("neurips-2022-media", "https://neurips.cc/media/neurips-2022/Styles.zip"),
    ("neurips-authorinstr", "https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles"),
    ("icml-2025-site", "https://icml.cc/Conferences/2025/AuthorInstructions"),
    ("icml-2025-dl", "https://icml.cc/media/icml-2025/Styles.zip"),
    ("icml-2025-dl2", "https://icml.cc/media/icml-2025/icml2025.sty"),
    ("icml-2024-dl", "https://icml.cc/media/icml-2024/Styles.zip"),
    ("icml-2023-dl", "https://icml.cc/media/icml-2023/Styles.zip"),
    ("icml-2022-dl", "https://icml.cc/media/icml-2022/Styles.zip"),
    ("aaai-2025-site", "https://aaai.org/authorkit25-2/"),
    ("aaai-2025-zip", "https://aaai.org/wp-content/uploads/2024/07/AAAI-25-Author-Kit.zip"),
    ("aaai-2025-zip2", "https://aaai.org/wp-content/uploads/2024/08/AAAI-25-Author-Kit.zip"),
    ("aamas-2025-site", "https://aamas2025.org/index.php/conference/calls/submission-instructions-main-technical-track/"),
    ("aamas-templates", "https://aamas2025.org/index.php/conference/attend/templates/"),
    ("ctan-mirrors-root", "https://mirrors.ctan.org/macros/latex/contrib/"),
]


def head(name: str, url: str):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(2048)
            return name, url, resp.status, f"ct={resp.headers.get('content-type','')} len={resp.headers.get('content-length','?')} head={data[:60]!r}"
    except urllib.error.HTTPError as exc:
        return name, url, exc.code, str(exc)[:70]
    except Exception as exc:  # noqa: BLE001
        return name, url, -1, str(exc)[:70]


with cf.ThreadPoolExecutor(max_workers=10) as pool:
    for name, url, status, note in pool.map(lambda t: head(*t), URLS):
        print(f"{status:>5}  {name:<22} {note}")
