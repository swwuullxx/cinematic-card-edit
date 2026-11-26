#!/usr/bin/env python3
"""Export the rounded-card frame as a PNG overlay (black with a transparent
rounded hole) to drop on the top track in CapCut / Premiere / Resolve.

Usage: python3 scripts/export_frame_png.py [out.png] [style.json]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from render import OverlayRenderer  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "presets", "card_frame.png")
style_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "presets", "style.json")
with open(style_path) as f:
    style = json.load(f)
OverlayRenderer(style, ROOT).frame.save(out)
print(f"wrote {out}")
