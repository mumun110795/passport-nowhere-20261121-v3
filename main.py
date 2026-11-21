#!/usr/bin/env python3
"""Entry point for the make.fun grader.

Regenerates the passport spread with draw.py (deterministically) and
copies the resulting entry.png to /output/entry.png.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import draw  # noqa: E402


def main():
    draw.build()
    src = os.path.join(HERE, "entry.png")
    os.makedirs("/output", exist_ok=True)
    shutil.copyfile(src, "/output/entry.png")
    print("wrote /output/entry.png", os.path.getsize(src), "bytes")


if __name__ == "__main__":
    main()
