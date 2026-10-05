#!/usr/bin/env python3
"""Probe round 4: NeurIPS media/stylesheet URLs, ICML media, Overleaf, AAMAS, JASSS."""
from __future__ import annotations

import concurrent.futures as cf
import urllib.error
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) dsh-anymath"}

URLS = [
    # NeurIPS media patterns
    ("nn-media-2025-Styles", "https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip"),
    ("nn-media-2025-sty", "https://media.neurips.cc/Conferences/NeurIPS2025/neurips_2025.sty"),
    ("nn-media-2024-Styles", "https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip"),
    ("nn-media-2023-Styles", "https://media.neurips.cc/Conferences/NeurIPS2023/Styles.zip"),
    ("nn-media-2022-Styles", "https://media.neurips.cc/Conferences/NeurIPS2022/Styles.zip"),
    ("nn-media-2021-Styles", "https://media.neurips.cc/Conferences/NeurIPS2021/Styles.zip"),
    ("nn-media-2020-Styles", "https://media.neurips.cc/Conferences/NeurIPS2020/Styles.zip"),
    ("nn-media-2025-s2", "https://media.neurips.cc/Conferences/2025/Styles.zip"),
    ("nn-2025-CFP", "https://neurips.cc/Conferences/2025/CallForPapers"),
    ("nn-checklist-guide", "https://neurips.cc/public/guides/PaperChecklist"),
    # ICML media
    ("icml2025-media-zip", "https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip"),
    ("icml2024-media-zip", "https://media.icml.cc/Conferences/ICML2024/Styles/icml2024.zip"),
    ("icml2023-media-zip", "https://media.icml.cc/Conferences/ICML2023/Styles/icml2023.zip"),
    ("icml2022-media-zip", "https://media.icml.cc/Conferences/ICML2022/Styles/icml2022.zip"),
    ("icml2025-media-ex", "https://media.icml.cc/Conferences/ICML2025/Styles/example_paper.pdf"),
    # CTAN extras
    ("ctan-aamas-hint", "https://mirrors.ctan.org/macros/latex/contrib/aamas.zip"),
    ("ctan-templates-root", "https://mirrors.ctan.org/macros/latex/contrib/"),
    ("ctan-ieeetran-dir", "https://mirrors.ctan.org/macros/latex/contrib/IEEEtran/"),
    # JASSS
    ("jasss-site", "https://www.jasss.org/"),
    # Overleaf (may be blocked)
    ("overleaf-neurips", "https://www.overleaf.com/latex/templates/neurips-2025/"),
]


def head(name: str, url: str):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(2048)
            return name, resp.status, f"ct={resp.headers.get('content-type','')} len={resp.headers.get('content-length','?')} head={data[:70]!r}"
    except urllib.error.HTTPError as exc:
        return name, exc.code, str(exc)[:70]
    except Exception as exc:  # noqa: BLE001
        return name, -1, str(exc)[:70]


with cf.ThreadPoolExecutor(max_workers=10) as pool:
    for name, status, note in pool.map(lambda t: head(*t), URLS):
        print(f"{status:>5}  {name:<24} {note}")
