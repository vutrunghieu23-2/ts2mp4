#!/usr/bin/env python3
"""
ts2mp4.py — Convert .ts files to .mp4 without CPU re-encoding.

Uses ffmpeg stream-copy (-c copy) to remux the container from MPEG-TS to
MP4 without decoding/re-encoding any audio or video streams, so no CPU
cycles are spent on codec work.

Usage
-----
    python ts2mp4.py input.ts [output.mp4]
    python ts2mp4.py video1.ts video2.ts ...
    python ts2mp4.py --help
"""

import argparse
import os
import subprocess
import sys


def find_ffmpeg() -> str:
    """Return the path to the ffmpeg binary, or raise if not found."""
    import shutil

    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
    if shutil.which(ffmpeg):
        return ffmpeg
    raise FileNotFoundError(
        "ffmpeg not found. Install it (e.g. 'apt install ffmpeg' or "
        "'brew install ffmpeg') and make sure it is on your PATH."
    )


def output_path(input_path: str) -> str:
    """Derive the output .mp4 path from an input .ts path."""
    root, ext = os.path.splitext(input_path)
    if ext.lower() == ".ts":
        return root + ".mp4"
    return input_path + ".mp4"


def convert(input_path: str, out_path: str, ffmpeg: str = "ffmpeg") -> None:
    """
    Remux *input_path* (MPEG-TS) to *out_path* (MP4) using stream-copy.

    ``-c copy``          – copy all streams without re-encoding (no CPU codec work)
    ``-movflags +faststart`` – place the MP4 moov atom at the front of the file
                               for better streaming / seek performance
    ``-y``               – overwrite the output file if it already exists
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    cmd = [
        ffmpeg,
        "-i", input_path,
        "-c", "copy",
        "-movflags", "+faststart",
        "-y",
        out_path,
    ]

    print(f"Converting: {input_path} -> {out_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(
            f"ffmpeg exited with code {result.returncode} for: {input_path}"
        )

    print(f"Done: {out_path}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ts2mp4",
        description=(
            "Convert MPEG-TS (.ts) files to MP4 without CPU re-encoding.\n\n"
            "Uses ffmpeg stream-copy so no video/audio decoding or encoding\n"
            "takes place — the container is simply remuxed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        metavar="input.ts",
        nargs="+",
        help="One or more input .ts files.",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="output.mp4",
        help=(
            "Output file path. Only valid when a single input file is given. "
            "When omitted the output path is derived from the input filename."
        ),
    )
    args = parser.parse_args(argv)

    if args.output and len(args.inputs) > 1:
        parser.error("--output / -o can only be used with a single input file.")

    try:
        ffmpeg = find_ffmpeg()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    errors = []
    for inp in args.inputs:
        out = args.output if args.output else output_path(inp)
        try:
            convert(inp, out, ffmpeg=ffmpeg)
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            errors.append(inp)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
