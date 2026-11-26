#!/usr/bin/env bash
# Generates placeholder clips (no real footage needed) and renders the demo.
set -euo pipefail
cd "$(dirname "$0")/.."
M=examples/demo_media
mkdir -p "$M"
mk() { # name, lavfi video source, tone frequency
  ffmpeg -y -v error -f lavfi -i "$2" -f lavfi -i "sine=frequency=$3:sample_rate=48000" \
    -t 3 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$M/$1.mp4"
}
mk speaker "gradients=s=720x1280:c0=0x2a1a6a:c1=0xb01060:c2=0x101040:speed=0.02:r=30" 220
mk broll_laptop "gradients=s=720x1280:c0=0x3a3020:c1=0x0a0a08:speed=0.03:r=30" 260
mk broll_loft "gradients=s=1280x720:c0=0xd8c8a8:c1=0x403020:c2=0x8090a0:speed=0.02:r=30" 300
mk broll_teal "gradients=s=720x1280:c0=0x0a3a48:c1=0x02121a:speed=0.04:r=30" 330
mk broll_snow "gradients=s=720x1280:c0=0x6a7888:c1=0x1a2028:speed=0.03:r=30" 350
mk broll_closeup "gradients=s=720x1280:c0=0x8a6a58:c1=0x2a1a14:c2=0xb0b8b8:speed=0.03:r=30" 390
mk broll_suit "mandelbrot=s=720x1280:r=30" 440
[ -f textures/sky.png ] || python3 scripts/make_texture.py textures/sky.png
python3 render.py examples/demo.json -o examples/demo.mp4
python3 render.py examples/demo.json --still 3.1 -o examples/still_accent.png
python3 render.py examples/demo.json --still 3.9 -o examples/still_caption.png
