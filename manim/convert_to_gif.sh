#!/bin/bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
    convert_to_gif.sh -a
        Convert all *.mp4 files found under ./manim/videos (recursive).

    convert_to_gif.sh <name1> [name2 ...]
        Convert only the specified files. Each name can be:
            - a full/relative path to an .mp4
            - a basename with or without ".mp4" (looked up under ./manim/videos)

Notes:
    Output GIFs are written to: ./manim/gifs/<basename>.gif
EOF
}

current_dir=$(pwd)
echo "The current directory is: $current_dir"

OUT_DIR="./manim/gifs"
DEFAULT_IN_DIR="./manim/videos"

mkdir -p "$OUT_DIR"

convert_one() {
    local in="$1"
    local base
    base="$(basename "${in%.mp4}")"
    local out="$OUT_DIR/$base.gif"

    echo "Converting $in... placing in $out"

    # Settings for size reduction
    local width="${GIF_WIDTH:-640}"
    local fps="${GIF_FPS:-20}" # Reduced from 15 to 12 for better compression

    # Optimization strategy: 
    # 1. Scale and reduce FPS first.
    # 2. palettegen=stats_mode=diff: Only looks at pixels that change (great for Manim).
    # 3. paletteuse=dither=sierra2_4a: Better compression than the default bayer dither.
   ffmpeg -y -i "$in" -filter_complex \
        "[0:v] fps=$fps,scale=$width:-1:flags=lanczos,split [a][b]; \
         [a] palettegen=stats_mode=full:max_colors=256 [p]; \
         [b][p] paletteuse=dither=bayer:bayer_scale=2:diff_mode=rectangle" \
        "$out"
}


find_by_name() {
    local name="$1"
    local target="$name"

    # If they passed just a name, try appending .mp4
    if [[ "$target" != *.mp4 ]]; then
        target="$target.mp4"
    fi

    # If it's an existing path, use it directly
    if [[ -f "$name" ]]; then
        echo "$name"
        return 0
    fi
    if [[ -f "$target" ]]; then
        echo "$target"
        return 0
    fi

    # Otherwise search under the default input dir (recursive)
    local found=""
    found="$(find "$DEFAULT_IN_DIR" -type f -name "$(basename "$target")" -print -quit 2>/dev/null || true)"
    if [[ -n "$found" ]]; then
        echo "$found"
        return 0
    fi

    return 1
}

if [[ $# -lt 1 ]]; then
    usage
    exit 2
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

if [[ "$1" == "-a" ]]; then
    shopt -s nullglob globstar
    files=( "$DEFAULT_IN_DIR"/**/*.mp4 )
    if (( ${#files[@]} == 0 )); then
        echo "No .mp4 files found under $DEFAULT_IN_DIR"
        exit 0
    fi
    for f in "${files[@]}"; do
        convert_one "$f"
    done
    exit 0
fi

# Convert only the listed files/names
for name in "$@"; do
    if in_file="$(find_by_name "$name")"; then
        convert_one "$in_file"
    else
        echo "Error: could not find mp4 for '$name' (looked in current path and under $DEFAULT_IN_DIR)" >&2
        exit 1
    fi
done
