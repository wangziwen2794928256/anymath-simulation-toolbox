#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csf_build —— 论文编译驱动器（判断成功与否不依赖退出码）

为什么需要它
------------
直接调 ``lualatex`` 有两个坑，都在本项目里真实踩到过：

1. **退出码不可信。** MiKTeX 在没检查更新时会打印
   ``major issue: So far, you have not checked for MiKTeX updates.``
   并返回**退出码 1**，即使编译完全成功、PDF 正常产出。
   若用 ``$LASTEXITCODE`` 判断，每次构建都会被误判为失败，
   而真正的失败（日志里有 ``!`` 开头）反而被这层噪声掩盖。
   本脚本因此用**实证判据**：日志里出现 ``Output written on`` 且没有 ``!`` 行。

2. **引擎必须按语言选。** 中文路径必须 XeLaTeX（CJK 字体），
   英文路径应当用 LuaLaTeX——``microtype`` 的字体**伸展（expansion）**
   在 XeLaTeX 下不可用，而伸展是 microtype 收益中更大的那一半。
   同一次构建用错引擎不会报错，只会让行文观感变差，属于"静默降级"。

另外它会跑够遍数（含 BibTeX），因为引用/交叉引用需要两遍才收敛；
只跑一遍得到的 PDF 里全是 ``??``，而作者常常以为是自己 label 写错了。

用法
----
    python csf_build.py --tex paper.tex
    python csf_build.py --tex paper.tex --engine xelatex --passes 3
    python csf_build.py --tex paper.tex --clean
    python csf_build.py --tex paper.tex --json

退出码
------
    0 = 成功（PDF 产出且无 ``!`` 错误）
    1 = 失败（有 LaTeX 错误，或未产出 PDF）
    2 = 产出成功但有需人工确认的告警（未定义引用、overfull box、shape doctor 告警）
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

#: MiKTeX 的二进制目录。硬编码是因为本仓的环境已固定；
#: 若 PATH 里已有这些程序，找到的就是同样的东西。
MIKTEX_BIN = Path(r"C:\Users\wzw\AppData\Local\Programs\MiKTeX\miktex\bin\x64")

CJK_RE = re.compile(r"[\u4e00-\u9fff]")

#: 判断"编译成功"的实证判据。故意不看退出码，原因见模块 docstring。
SUCCESS_RE = re.compile(r"Output written on .*\((\d+) page")
ERROR_RE = re.compile(r"^!", re.MULTILINE)


def find_tool(name: str) -> str | None:
    """先在 MiKTeX 目录找，再退回 PATH。"""
    cand = MIKTEX_BIN / f"{name}.exe"
    if cand.exists():
        return str(cand)
    return shutil.which(name)


def detect_engine(tex_text: str) -> tuple[str, str]:
    """按正文语言选引擎，并给出理由（便于日志里核对）。"""
    cjk = len(CJK_RE.findall(tex_text))
    latin = len(re.findall(r"[A-Za-z]{2,}", tex_text))
    if cjk > 0 and cjk * 8 > latin:
        return "xelatex", (f"正文以中文为主（CJK {cjk} 字 vs 英文词 {latin}）——"
                           f"中文需要 XeLaTeX 的 CJK 字体支持")
    return "lualatex", (f"正文以英文为主（英文词 {latin} vs CJK {cjk} 字）——"
                        f"LuaLaTeX 才能启用 microtype 字体伸展；"
                        f"XeLaTeX 会静默禁用伸展，观感变差但不报错")


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def build(tex: Path, engine: str, jobs: int, do_bib: bool) -> dict:
    """跑够遍数并解析日志。返回结构化结果，由调用方决定退出码。"""
    cwd = tex.parent
    stem = tex.stem
    log = cwd / f"{stem}.log"

    if not shutil.which(engine) and find_tool(engine) is None:
        return {"ok": False, "fatal": f"找不到 {engine}", "engine": engine}

    exe = find_tool(engine) or engine
    passes: list[dict] = []
    for i in range(jobs):
        rc, out = run([exe, "-interaction=nonstopmode", "-file-line-error",
                       tex.name], cwd)
        passes.append({"pass": i + 1, "exit_code": rc,
                       "miktex_update_nag": "major issue" in out})
        # 第一遍之后如果存在 .bib 且还没 .bbl，就跑 BibTeX 让引用先落地
        if i == 0 and do_bib:
            bib = find_tool("bibtex")
            if bib and (cwd / f"{stem}.aux").exists() and not (cwd / f"{stem}.bbl").exists():
                brc, bout = run([bib, stem], cwd)
                passes.append({"bibtex": True, "exit_code": brc,
                               "output": bout.strip().splitlines()[:6]})

    if not log.exists():
        return {"ok": False, "fatal": "没有生成 .log，编译在第 1 遍就中断了",
                "engine": engine, "passes": passes}

    text = log.read_text(encoding="utf-8", errors="replace")
    errors = [ln for ln in text.splitlines() if ln.startswith("!")]
    pages = 0
    m = SUCCESS_RE.search(text)
    if m:
        pages = int(m.group(1))

    warns: list[str] = []
    for pat, label in (
        (r"LaTeX Warning: (?:Reference|Citation) .* undefined", "未定义引用"),
        (r"Overfull \\hbox", "Overfull hbox（文字或公式超出边界）"),
        (r"resolves to the SAME font", "shape doctor：字体形状静默回退"),
        (r"Package .* Warning: (?!.*unicode-math).*", "宏包告警"),
    ):
        hits = re.findall(pat, text)
        if hits:
            warns.append(f"{label}: {len(hits)} 处")

    return {
        "ok": bool(pages) and not errors,
        "engine": engine,
        "pages": pages,
        "pdf": str(cwd / f"{stem}.pdf"),
        "errors": errors[:10],
        "warnings": warns,
        "passes": passes,
    }


def clean(tex: Path) -> list[str]:
    """删除中间产物，保留 .tex/.pdf/.bib 与图目录。"""
    keep = {".tex", ".pdf", ".bib", ".sty", ".cls"}
    removed = []
    for p in tex.parent.iterdir():
        if p.is_file() and p.suffix.lower() not in keep and p.stem.startswith(tex.stem):
            p.unlink()
            removed.append(p.name)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser(description="论文编译驱动器（不依赖退出码判断成功）")
    ap.add_argument("--tex", required=True, help="主 .tex 文件")
    ap.add_argument("--engine", choices=["auto", "lualatex", "xelatex"],
                    default="auto", help="默认按正文语言自动选择")
    ap.add_argument("--passes", type=int, default=3, help="编译遍数，默认 3")
    ap.add_argument("--no-bib", action="store_true", help="不调用 BibTeX")
    ap.add_argument("--clean", action="store_true", help="编译前清理中间产物")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    tex = Path(args.tex)
    if not tex.exists():
        print(f"找不到 {tex}", file=sys.stderr)
        return 1

    if args.clean:
        gone = clean(tex)
        if gone and not args.json:
            print(f"已清理 {len(gone)} 个中间文件: {', '.join(gone[:8])}")

    text = tex.read_text(encoding="utf-8", errors="replace")
    engine, why = (args.engine, "由 --engine 指定") if args.engine != "auto" \
        else detect_engine(text)

    res = build(tex, engine, args.passes, not args.no_bib)
    res["engine_reason"] = why

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"csf-build —— {tex.name}")
        print(f"引擎: {engine}  ({why})")
        for p in res.get("passes", []):
            if "bibtex" in p:
                print(f"  bibtex       exit={p['exit_code']}")
            else:
                # Only annotate when the exit code is actually non-zero: the nag is
                # what MAKES it non-zero. Printing the note next to exit=0 would
                # suggest a failure that did not happen.
                note = ""
                if p["exit_code"] != 0 and p["miktex_update_nag"]:
                    note = "  [该非零码来自 MiKTeX 更新提示，不是编译失败]"
                print(f"  第 {p['pass']} 遍      exit={p['exit_code']}{note}")
        if res.get("fatal"):
            print(f"\n失败: {res['fatal']}")
        else:
            print(f"\n页数: {res['pages']}")
            print(f"PDF : {res['pdf']}")
            if res["errors"]:
                print(f"\nLaTeX 错误 {len(res['errors'])} 条（前若干条）:")
                for e in res["errors"]:
                    print(f"  {e}")
            else:
                print("LaTeX 错误: 无")
            if res["warnings"]:
                print("\n需人工确认的告警:")
                for w in res["warnings"]:
                    print(f"  - {w}")

    if not res.get("ok"):
        print("\n结论：不通过", file=sys.stderr)
        return 1
    if res.get("warnings"):
        print("\n结论：编译成功，有告警需确认")
        return 2
    print("\n结论：编译成功")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
