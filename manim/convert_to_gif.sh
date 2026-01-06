#!/bin/bash

current_dir=$(pwd)
echo "The current directory is: $current_dir"

# High-quality MP4 to GIF converter
for f in ./manim/videos/*.mp4; do
    if [ -f "$f" ]; then
        output_file="./manim/gifs/$(basename "${f%.mp4}.gif")"
        echo "Converting $f...placing in ${output_file}"
        # Generates an optimized palette for better color accuracy
        ffmpeg -i "$f" -filter_complex "[0:v] split [a][b]; [a] palettegen [p]; [b][p] paletteuse" "$output_file"
    fi
done
