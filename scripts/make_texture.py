#!/usr/bin/env python3
"""Generate the default sky/chrome texture used to fill the accent word.

Usage: python3 scripts/make_texture.py [out.png] [seed]
Swap in your own image (clouds, chrome, light leaks, fire...) any time --
just point "texture" in presets/style.json or an accent entry at it.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from render import procedural_sky  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "textures/sky.png"
procedural_sky(1024, 1024).save(out)
print(f"wrote {out}")
