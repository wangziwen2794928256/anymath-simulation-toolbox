#!/usr/bin/env python3
"""Copy the bundled CUMCM LaTeX starter into a new project directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="new or empty output directory")
    args = parser.parse_args()

    source = Path(__file__).resolve().parents[1] / "assets" / "latex-template"
    destination = args.output_dir.expanduser().resolve()

    if not source.is_dir():
        parser.error(f"bundled template is missing: {source}")
    if destination.exists() and any(destination.iterdir()):
        parser.error(f"refusing to overwrite nonempty directory: {destination}")

    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    (destination / "figures").mkdir(exist_ok=True)
    print(f"Created CUMCM paper project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
