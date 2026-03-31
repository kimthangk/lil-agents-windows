#!/usr/bin/env python3
"""
One-time script to convert original lil-agents .mov and .png assets for Windows.

Requirements:
    - ffmpeg on PATH  (https://ffmpeg.org/download.html)
    - Pillow: pip install Pillow

Usage:
    python tools/convert_assets.py --mov-dir /path/to/lil-agents/LilAgents
"""
import argparse
import subprocess
from pathlib import Path


def convert_gif(mov_path: Path, out_path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mov_path),
            "-vf", "fps=15,scale=80:-1:flags=lanczos",
            str(out_path),
        ],
        check=True,
    )


def convert_ico(png_path: Path, out_path: Path) -> None:
    from PIL import Image
    img = Image.open(str(png_path))
    img.save(str(out_path), format="ICO", sizes=[(32, 32), (16, 16)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert lil-agents assets for Windows")
    parser.add_argument(
        "--mov-dir",
        required=True,
        help="Path to LilAgents/ source directory containing .mov files and menuicon.png",
    )
    args = parser.parse_args()

    mov_dir = Path(args.mov_dir)
    assets_dir = Path(__file__).parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)

    print("Converting bruce.gif ...")
    convert_gif(mov_dir / "walk-bruce-01.mov", assets_dir / "bruce.gif")

    print("Converting jazz.gif ...")
    convert_gif(mov_dir / "walk-jazz-01.mov", assets_dir / "jazz.gif")

    print("Converting icon.ico ...")
    convert_ico(mov_dir / "menuicon.png", assets_dir / "icon.ico")

    print("Done. Assets written to:", assets_dir)


if __name__ == "__main__":
    main()
