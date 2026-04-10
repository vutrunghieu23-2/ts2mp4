#!/usr/bin/env bash
# ts2mp4.sh — Convert .ts files to .mp4 without CPU re-encoding
#
# Uses ffmpeg stream-copy (-c copy) to remux the container from MPEG-TS to
# MP4 without decoding/re-encoding any audio or video streams, so no CPU
# cycles are spent on codec work.
#
# Usage:
#   ./ts2mp4.sh input.ts [output.mp4]
#   ./ts2mp4.sh *.ts
#
# If no output path is supplied the script derives it from the input filename
# by replacing the .ts extension with .mp4 in the same directory.

set -euo pipefail

FFMPEG="${FFMPEG:-ffmpeg}"

usage() {
    echo "Usage: $(basename "$0") <input.ts> [output.mp4]"
    echo "       $(basename "$0") <input1.ts> [input2.ts ...]"
    echo ""
    echo "Converts one or more MPEG-TS files to MP4 using stream-copy (no re-encoding)."
    exit 1
}

convert_file() {
    local input="$1"
    local output="${2:-}"

    if [[ ! -f "$input" ]]; then
        echo "ERROR: Input file not found: $input" >&2
        return 1
    fi

    if [[ -z "$output" ]]; then
        # Replace .ts extension with .mp4; if no .ts extension, append .mp4
        if [[ "$input" == *.ts ]]; then
            output="${input%.ts}.mp4"
        else
            output="${input}.mp4"
        fi
    fi

    echo "Converting: $input -> $output"

    "$FFMPEG" \
        -i "$input" \
        -c copy \
        -movflags +faststart \
        -y \
        "$output"

    echo "Done: $output"
}

if [[ $# -eq 0 ]]; then
    usage
fi

# If exactly two arguments are given and the second does not end in .ts,
# treat it as the explicit output path.
if [[ $# -eq 2 && "$2" != *.ts ]]; then
    convert_file "$1" "$2"
else
    # Process each argument as an input file
    for input in "$@"; do
        convert_file "$input"
    done
fi
