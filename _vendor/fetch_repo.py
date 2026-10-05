#!/usr/bin/env python3
"""从 GitHub 获取仓库（多通道自动降级，适配中国网络与 API 限流）。

通道优先级（实测）
------------------
1. `codeload.github.com/<repo>/zip/refs/heads/{main,master}` —— **无需认证、不限流**，
   浏览器"Download ZIP"走的就是它。有 VPN 时最快最稳。
2. `api.github.com/repos/<repo>/zipball` —— 无 VPN 也能通，但**未认证时限流 60 次/小时**，
   批量下载会 403。
3. `raw.githubusercontent.com/<repo>/<branch>/<path>` —— 单文件抓取，无 VPN 可通。

设计要点
--------
* 自动在 `main` / `master` 之间回退（仓库默认分支不一致是常态）。
* 解压后剥掉 GitHub 自动加的 `<owner>-<repo>-<sha>/` 前缀。
* 写入 `PROVENANCE.md` 记录来源、许可、获取时间，便于日后升级与合规。
* API 仅用于**读元数据**（许可、stars、默认分支），失败不阻塞下载。

用法
----
    python fetch_repo.py <owner/repo> [目标目录]
    python fetch_repo.py <owner/repo> --list              # 列文件树（需 API，可能限流）
    python fetch_repo.py <owner/repo> <dest> --raw a.py,b.md
    python fetch_repo.py --batch repos.txt --batch-dest _vendor
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile

UA = {"User-Agent": "dsh-anymath-fetch"}
CODELOAD = "https://codeload.github.com/{slug}/zip/refs/heads/{branch}"
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com/{slug}/{branch}/{path}"
BRANCHES = ("main", "master")


def _get(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def repo_meta(slug: str) -> dict:
    """读仓库元数据；失败返回空 dict（限流不阻塞下载）。"""
    try:
        return json.loads(_get(f"{API}/repos/{slug}", timeout=30).decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  (元数据不可用: {str(exc)[:50]})", file=sys.stderr)
        return {}


def default_branch(slug: str) -> str | None:
    return repo_meta(slug).get("default_branch")


def _unzip_to(blob: bytes, dest: str) -> int:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
        root = names[0].split("/")[0] if names else ""
        tmp = dest + ".__tmp__"
        if os.path.isdir(tmp):
            shutil.rmtree(tmp)
        z.extractall(tmp)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(dest, exist_ok=True)
        cand = os.path.join(tmp, root)
        src = cand if root and os.path.isdir(cand) else tmp
        for entry in os.listdir(src):
            shutil.move(os.path.join(src, entry), os.path.join(dest, entry))
        shutil.rmtree(tmp, ignore_errors=True)
        return len(names)


def download(slug: str, dest: str) -> bool:
    """按通道优先级尝试下载整仓。"""
    branches: list[str] = []
    db = default_branch(slug)
    if db:
        branches.append(db)
    branches += [b for b in BRANCHES if b not in branches]

    # 通道 1：codeload（无需认证，不限流）
    for br in branches:
        url = CODELOAD.format(slug=slug, branch=br)
        try:
            blob = _get(url)
            n = _unzip_to(blob, dest)
            print(f"  v codeload[{br}] {len(blob):,} B, {n} 条目 -> {dest}")
            _provenance(dest, slug, channel=f"codeload/zip/{br}", size=len(blob))
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"  . codeload[{br}] 失败 {getattr(exc, 'code', '')} {str(exc)[:40]}")

    # 通道 2：api zipball（会限流）
    try:
        blob = _get(f"{API}/repos/{slug}/zipball")
        n = _unzip_to(blob, dest)
        print(f"  v api/zipball {len(blob):,} B, {n} 条目 -> {dest}")
        _provenance(dest, slug, channel="api/zipball", size=len(blob))
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  x api/zipball 失败 {getattr(exc, 'code', '')} {str(exc)[:40]}")

    print(f"  x {slug} 所有通道均失败", file=sys.stderr)
    return False


def download_raw(slug: str, paths: list[str], dest: str) -> None:
    br = default_branch(slug) or "main"
    os.makedirs(dest, exist_ok=True)
    for p in paths:
        target = os.path.join(dest, p.replace("/", os.sep))
        os.makedirs(os.path.dirname(target) or dest, exist_ok=True)
        try:
            data = _get(RAW.format(slug=slug, branch=br, path=p), timeout=60)
            with open(target, "wb") as fh:
                fh.write(data)
            print(f"  v {p} ({len(data):,} B)")
        except Exception as exc:  # noqa: BLE001
            print(f"  x {p} ({str(exc)[:40]})")
    _provenance(dest, slug, channel=f"raw/{br}", size=None)


def list_tree(slug: str) -> None:
    meta = repo_meta(slug)
    br = meta.get("default_branch") or "main"
    try:
        tree = json.loads(
            _get(f"{API}/repos/{slug}/git/trees/{br}?recursive=1", timeout=60).decode("utf-8")
        )
    except Exception as exc:  # noqa: BLE001
        print(f"读文件树失败（多为 API 限流）: {str(exc)[:60]}", file=sys.stderr)
        return
    files = [n for n in tree.get("tree", []) if n["type"] == "blob"]
    total = sum(f.get("size", 0) for f in files)
    print(f"{slug}: {len(files)} 文件, 约 {total / 1024 / 1024:.1f} MB（分支 {br}）")
    for f in sorted(files, key=lambda x: -x.get("size", 0))[:60]:
        print("  {0:>10,} B  {1}".format(f.get("size", 0), f["path"]))


def _provenance(dest: str, slug: str, *, channel: str, size: int | None) -> None:
    meta = repo_meta(slug)
    lic = (meta.get("license") or {}).get("spdx_id") or "NONE"
    lines = [
        f"# 来源：https://github.com/{slug}",
        "",
        f"- stars: {meta.get('stargazers_count', 'n/a')}",
        f"- license: {lic}",
        f"- default_branch: {meta.get('default_branch', 'n/a')}",
        f"- 获取通道: {channel}",
        f"- 获取时间(UTC): {datetime.datetime.utcnow().isoformat(timespec='seconds')}Z",
    ]
    if size:
        lines.append(f"- 下载字节数: {size:,}")
    lines += [
        "",
        "本目录为第三方只读引用。**所有本地改动落在工作区自己的 `skills/` 下**，",
        "不直接改这里，便于日后按许可与版本升级。",
        "",
        "许可提示：若为 `NONE` / `NOASSERTION`，商用或再分发前须自行确认；",
        "仅作阅读与思路借鉴时风险较低。",
    ]
    with open(os.path.join(dest, "PROVENANCE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="多通道 GitHub 仓库获取")
    ap.add_argument("slug", nargs="?", help="owner/repo")
    ap.add_argument("dest", nargs="?", help="目标目录")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--raw", help="逗号分隔的文件路径")
    ap.add_argument("--batch", metavar="FILE", help="批量清单，每行一个 owner/repo")
    ap.add_argument("--batch-dest", metavar="DIR", default="_vendor", help="批量目标根目录")
    args = ap.parse_args()

    if args.batch:
        root = args.batch_dest
        os.makedirs(root, exist_ok=True)
        with open(args.batch, encoding="utf-8") as fh:
            slugs = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
        ok = fail = 0
        for i, slug in enumerate(slugs, 1):
            print(f"[{i}/{len(slugs)}] {slug}")
            if download(slug, os.path.join(root, slug.split("/")[-1])):
                ok += 1
            else:
                fail += 1
        print(f"\n批量完成：成功 {ok}，失败 {fail}")
        return 1 if fail else 0

    if not args.slug:
        ap.print_help()
        return 2
    if args.list:
        list_tree(args.slug)
        return 0
    if not args.dest:
        print("需要目标目录（或 --list / --batch）", file=sys.stderr)
        return 2
    if args.raw:
        download_raw(args.slug, [p.strip() for p in args.raw.split(",") if p.strip()], args.dest)
        return 0
    return 0 if download(args.slug, args.dest) else 1


if __name__ == "__main__":
    raise SystemExit(main())
