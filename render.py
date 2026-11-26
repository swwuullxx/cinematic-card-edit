#!/usr/bin/env python3
"""
Cinematic Card renderer.

Takes a project file (clips + captions + accent words) and renders a 9:16
video in the "Cinematic Card" style:

  * footage inside a rounded-corner 4:5 card on a black background
  * darkened, slightly desaturated grade
  * small white sans-serif captions that blur/fade in and hard-cut out
  * one big condensed accent word filled with an image texture
  * hard cuts only

Requirements: Python 3.8+, Pillow, ffmpeg + ffprobe on PATH.

Usage:
  python3 render.py examples/demo.json -o out.mp4
  python3 render.py project.json --srt captions.srt -o out.mp4
  python3 render.py project.json --still 3.1 -o preview.png
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def die(msg):
    sys.exit(f"error: {msg}")


def resolve(path, base):
    """Resolve a path relative to `base`, falling back to the repo root."""
    if path is None or os.path.isabs(path):
        return path
    for root in (base, ROOT):
        p = os.path.join(root, path)
        if os.path.exists(p):
            return p
    return os.path.join(base, path)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease_out_quad(x):
    return 1 - (1 - x) ** 2


def has_audio(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return bool(out)


def media_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Captions: SRT parsing and 2-4 word splitting
# --------------------------------------------------------------------------- #
def _srt_time(s):
    h, m, rest = s.strip().replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def parse_srt(path):
    with open(path, encoding="utf-8-sig") as f:
        blocks = re.split(r"\n\s*\n", f.read().strip())
    cues = []
    for b in blocks:
        lines = [l for l in b.strip().splitlines() if l.strip()]
        ti = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if ti is None:
            continue
        a, b2 = lines[ti].split("-->")
        text = " ".join(lines[ti + 1:]).strip()
        if text:
            cues.append({"text": text, "start": _srt_time(a), "end": _srt_time(b2)})
    return cues


def split_caption(cue, max_words):
    """Split a long cue into chunks of <= max_words, timed by character count."""
    words = cue["text"].split()
    if len(words) <= max_words:
        return [cue]
    n_chunks = math.ceil(len(words) / max_words)
    per = math.ceil(len(words) / n_chunks)  # balance chunk sizes
    chunks = [" ".join(words[i:i + per]) for i in range(0, len(words), per)]
    total = sum(len(c) for c in chunks)
    t, dur, out = cue["start"], cue["end"] - cue["start"], []
    for c in chunks:
        d = dur * len(c) / total
        out.append({"text": c, "start": t, "end": t + d})
        t += d
    out[-1]["end"] = cue["end"]
    return out


# --------------------------------------------------------------------------- #
# Overlay layer (frame mask + captions + accent), rendered with Pillow
# --------------------------------------------------------------------------- #
class OverlayRenderer:
    def __init__(self, style, base):
        self.s = style
        self.base = base
        cv = style["canvas"]
        self.W, self.H = cv["width"], cv["height"]
        self.frame = self._frame_mask()
        cap = style["caption"]
        self.cap_font = ImageFont.truetype(resolve(cap["font"], base), cap["size"])
        self.cap_color = hex_rgb(cap["color"])
        self.accent_font_path = resolve(style["accent"]["font"], base)
        self._tex_cache = {}

    # -- rounded card "window" ------------------------------------------------
    def _frame_mask(self):
        c = self.s["card"]
        ss = 4  # supersample for smooth corners
        hole = Image.new("L", (self.W * ss, self.H * ss), 255)
        ImageDraw.Draw(hole).rounded_rectangle(
            [c["x"] * ss, c["y"] * ss,
             (c["x"] + c["width"]) * ss - 1, (c["y"] + c["height"]) * ss - 1],
            radius=c["corner_radius"] * ss, fill=0)
        alpha = hole.resize((self.W, self.H), Image.LANCZOS)
        bg = hex_rgb(self.s["canvas"]["background"])
        img = Image.new("RGBA", (self.W, self.H), bg + (255,))
        img.putalpha(alpha)
        return img

    # -- small caption --------------------------------------------------------
    def _wrap(self, text):
        maxw = self.s["caption"]["max_width"]
        words, lines, cur = text.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.cap_font.getlength(trial) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def caption_layer(self, text, progress, y=None, shadow=0):
        """progress 0..1 through the blur-in animation (1 = settled).
        y overrides the caption's vertical center; shadow (0..1) adds a soft
        dark glow for busy backgrounds."""
        cap = self.s["caption"]
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        lines = self._wrap(text)
        lh = cap["size"] * cap["line_spacing"]
        y0 = (y or cap["center_y"]) - lh * (len(lines) - 1) / 2
        for i, line in enumerate(lines):
            d.text((self.W / 2, y0 + i * lh), line, font=self.cap_font,
                   fill=self.cap_color + (255,), anchor="mm")
        if shadow > 0:
            glow = layer.getchannel("A").filter(ImageFilter.GaussianBlur(10))
            glow = glow.point(lambda v: int(min(255, v * 2.5) * shadow))
            under = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
            under.putalpha(glow)
            under.alpha_composite(layer)
            layer = under
        e = ease_out_quad(progress)
        blur = cap["in_blur"] * (1 - e)
        if blur > 0.3:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        if e < 1:
            a = layer.getchannel("A").point(lambda v: int(v * e))
            layer.putalpha(a)
        return layer

    # -- big textured accent word --------------------------------------------
    def _texture(self, path):
        key = path or "__procedural__"
        if key not in self._tex_cache:
            p = resolve(path, self.base) if path else None
            if p and os.path.exists(p):
                self._tex_cache[key] = Image.open(p).convert("RGB")
            else:
                self._tex_cache[key] = procedural_sky(1024, 1024)
        return self._tex_cache[key]

    def accent_layer(self, text, texture=None, width=None):
        ac = self.s["accent"]
        target_w = width or ac["target_width"]
        if ac.get("uppercase", True):
            text = text.upper()
        sy = ac.get("stretch_y", 1.0)  # vertical stretch = taller, more condensed look
        # find the font size that hits the target width (capped by max height)
        size = 400
        f = ImageFont.truetype(self.accent_font_path, size)
        l, t, r, b = f.getbbox(text)
        scale = min(target_w / (r - l), ac["max_height"] / ((b - t) * sy))
        f = ImageFont.truetype(self.accent_font_path, max(10, int(size * scale)))
        l, t, r, b = f.getbbox(text)
        tw, th = r - l, b - t
        mask = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(mask).text((-l, -t), text, font=f, fill=255)
        if sy != 1.0:
            th = int(th * sy)
            mask = mask.resize((tw, th), Image.LANCZOS)
        tex = cover(self._texture(texture or ac.get("texture")), tw, th)
        word = tex.convert("RGBA")
        word.putalpha(mask)
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        pos = (int(self.W / 2 - tw / 2), int(ac["center_y"] - th / 2))
        shadow = ac.get("shadow_opacity", 0)
        if shadow > 0:  # soft dark glow so pale textures stay readable on bright footage
            sh = Image.new("L", (self.W, self.H), 0)
            sh.paste(mask, pos)
            sh = sh.filter(ImageFilter.GaussianBlur(ac.get("shadow_blur", 24)))
            sh = sh.point(lambda v: int(min(255, v * 1.6) * shadow))
            layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
            layer.putalpha(sh)
        layer.alpha_composite(word, pos)
        return layer

    # -- compose --------------------------------------------------------------
    def compose(self, caption=None, accent=None):
        img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        if caption:
            img.alpha_composite(self.caption_layer(*caption))
        if accent:
            img.alpha_composite(self.accent_layer(*accent))
        img.alpha_composite(self.frame)
        return img


def cover(img, w, h):
    """Resize + center-crop to fill w x h."""
    s = max(w / img.width, h / img.height)
    im = img.resize((max(w, math.ceil(img.width * s)), max(h, math.ceil(img.height * s))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def procedural_sky(w, h, seed=7):
    """Bright sky/chrome texture: pale-blue gradient with soft white clouds."""
    grad = Image.linear_gradient("L").resize((w, h))
    top, bottom = (150, 185, 230), (245, 248, 255)
    base = Image.merge("RGB", [grad.point(lambda v, a=a, b=b: int(a + (b - a) * v / 255))
                               for a, b in zip(top, bottom)])
    clouds = Image.new("L", (w, h), 0)
    for i, sc in enumerate((8, 16, 32)):
        n = Image.effect_noise((max(2, w // sc), max(2, h // sc)), 64 + i * 10)
        clouds = ImageChops.add(clouds, n.resize((w, h), Image.BICUBIC), scale=1.6)
    clouds = clouds.filter(ImageFilter.GaussianBlur(6)).point(lambda v: max(0, min(255, (v - 110) * 3)))
    out = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), base, clouds)
    # a diagonal chrome streak, like the reference
    streak = Image.new("L", (w, h), 0)
    ImageDraw.Draw(streak).line([(0, int(h * 0.9)), (w, int(h * 0.1))], fill=200, width=w // 18)
    out = Image.composite(Image.new("RGB", (w, h), (90, 120, 170)), out,
                          streak.filter(ImageFilter.GaussianBlur(w // 40)))
    return out


# --------------------------------------------------------------------------- #
# Timeline -> per-frame overlay state
# --------------------------------------------------------------------------- #
def frame_state(t, captions, accents, style, fps):
    acc = next((a for a in accents if a["start"] <= t < a["end"]), None)
    accent_key = (acc["text"], acc.get("texture"), acc.get("width")) if acc else None
    cap_key = None
    if not (acc and style["accent"].get("hide_captions", True)):
        c = next((c for c in captions if c["start"] <= t < c["end"]), None)
        if c:
            n = max(1, round(style["caption"]["in_duration"] * fps))
            step = int((t - c["start"]) * fps + 1e-6) + 1
            cap_key = (c["text"], 1.0 if step > n else (step - 0.5) / n,
                       c.get("y"), c.get("shadow", 0))
    return cap_key, accent_key


# --------------------------------------------------------------------------- #
# Main render
# --------------------------------------------------------------------------- #
def build_ffmpeg(project, style, base, out, fps, total, audio_mode):
    cv, card, g = style["canvas"], style["card"], style["grade"]
    W, H = cv["width"], cv["height"]
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats"]
    clips = project["clips"]
    for c in clips:
        cmd += ["-ss", str(c.get("start", 0)), "-t", str(c["duration"]),
                "-i", resolve(c["file"], base)]
    ov_idx = len(clips)
    cmd += ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
            "-r", str(fps), "-i", "pipe:0"]
    fc = []
    for i, c in enumerate(clips):
        fc.append(
            f"[{i}:v]scale={card['width']}:{card['height']}:force_original_aspect_ratio=increase,"
            f"crop={card['width']}:{card['height']}:(iw-ow)/2:(ih-oh)*{c.get('crop_y', card.get('crop_y', 0.5))},"
            f"setsar=1,fps={fps},"
            f"trim=duration={c['duration']},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    fc.append("".join(f"[v{i}]" for i in range(len(clips))) +
              f"concat=n={len(clips)}:v=1:a=0[cat]")
    d = g["dim"]
    fc.append(
        f"[cat]eq=contrast={g['contrast']}:saturation={g['saturation']},"
        f"colorchannelmixer=rr={d}:gg={d}:bb={d},"
        f"pad={W}:{H}:{card['x']}:{card['y']}:color={cv['background']}[base]")
    fc.append(f"[base][{ov_idx}:v]overlay=format=auto:shortest=1,format=yuv420p[vout]")

    maps = ["-map", "[vout]"]
    if audio_mode == "voiceover":
        cmd += ["-i", resolve(project["audio"], base)]
        maps += ["-map", f"{ov_idx + 1}:a"]
    elif audio_mode == "clips":
        for i, c in enumerate(clips):
            fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,"
                      f"atrim=0:{c['duration']},apad=whole_dur={c['duration']},"
                      f"asetpts=PTS-STARTPTS[a{i}]")
        fc.append("".join(f"[a{i}]" for i in range(len(clips))) +
                  f"concat=n={len(clips)}:v=0:a=1[aout]")
        maps += ["-map", "[aout]"]
    cmd += ["-filter_complex", ";".join(fc)] + maps
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(fps),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    if audio_mode != "none":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += ["-t", f"{total:.3f}", out]
    return cmd


def render_still(project, style, base, t, out, captions, accents, fps):
    """Render one frame (footage + overlay) to PNG for quick previews."""
    card = style["card"]
    elapsed = 0.0
    clip = project["clips"][-1]
    local = clip["duration"] - 1 / fps
    for c in project["clips"]:
        if t < elapsed + c["duration"]:
            clip, local = c, t - elapsed
            break
        elapsed += c["duration"]
    g = style["grade"]
    tmp = out + ".src.png"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", str(clip.get("start", 0) + local),
         "-i", resolve(clip["file"], base), "-frames:v", "1", "-vf",
         f"scale={card['width']}:{card['height']}:force_original_aspect_ratio=increase,"
         f"crop={card['width']}:{card['height']}:(iw-ow)/2:(ih-oh)*{clip.get('crop_y', card.get('crop_y', 0.5))},eq=contrast={g['contrast']}:saturation={g['saturation']},"
         f"colorchannelmixer=rr={g['dim']}:gg={g['dim']}:bb={g['dim']}", tmp], check=True)
    ov = OverlayRenderer(style, base)
    img = Image.new("RGBA", (ov.W, ov.H), hex_rgb(style["canvas"]["background"]) + (255,))
    img.paste(Image.open(tmp).convert("RGBA"), (card["x"], card["y"]))
    os.remove(tmp)
    cap, acc = frame_state(t, captions, accents, style, fps)
    img.alpha_composite(ov.compose(cap, acc))
    img.convert("RGB").save(out)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(description="Render a video in the Cinematic Card style.")
    ap.add_argument("project", help="project JSON (see examples/demo.json)")
    ap.add_argument("-o", "--out", default="out.mp4")
    ap.add_argument("--style", default=os.path.join(ROOT, "presets", "style.json"))
    ap.add_argument("--srt", help="load captions from an SRT file (overrides project captions)")
    ap.add_argument("--still", type=float, metavar="SECONDS",
                    help="render a single PNG frame at this time instead of a video")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} not found on PATH")

    with open(args.style) as f:
        style = json.load(f)
    with open(args.project) as f:
        project = json.load(f)
    base = os.path.dirname(os.path.abspath(args.project))
    style_base = os.path.dirname(os.path.dirname(os.path.abspath(args.style)))
    # fonts/textures in the style are relative to the repo (or the style's parent dir)
    for sec, key in (("caption", "font"), ("accent", "font"), ("accent", "texture")):
        if style[sec].get(key):
            style[sec][key] = resolve(style[sec][key], style_base)

    fps = project.get("fps", style["canvas"]["fps"])
    if not project.get("clips"):
        die("project has no clips")
    for c in project["clips"]:
        p = resolve(c["file"], base)
        if not os.path.exists(p):
            die(f"clip not found: {p}")
        if "duration" not in c:
            dur = media_duration(p)
            if dur is None:
                die(f"could not read duration of {p}; set \"duration\"")
            c["duration"] = dur - c.get("start", 0)
    total = sum(c["duration"] for c in project["clips"])

    captions = parse_srt(args.srt) if args.srt else project.get("captions", [])
    max_words = style["caption"].get("max_words", 4)
    if project.get("split_captions", True):
        captions = [piece for c in captions for piece in split_caption(c, max_words)]
    accents = project.get("accents", [])

    if args.still is not None:
        render_still(project, style, base, args.still, args.out, captions, accents, fps)
        return

    if project.get("audio"):
        audio_mode = "voiceover"
    elif all(has_audio(resolve(c["file"], base)) for c in project["clips"]):
        audio_mode = "clips"
    else:
        audio_mode = "none"
        print("note: no voiceover and not every clip has audio -> rendering silent video")

    cmd = build_ffmpeg(project, style, base, args.out, fps, total, audio_mode)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ov = OverlayRenderer(style, base)
    cache = {}
    n_frames = math.ceil(total * fps)
    try:
        for i in range(n_frames):
            key = frame_state(i / fps, captions, accents, style, fps)
            if key not in cache:
                if len(cache) > 64:
                    cache.clear()
                cache[key] = ov.compose(*key).tobytes()
            proc.stdin.write(cache[key])
        proc.stdin.close()
    except BrokenPipeError:
        pass
    if proc.wait() != 0:
        die("ffmpeg failed")
    print(f"wrote {args.out} ({total:.2f}s, {n_frames} frames @ {fps}fps, audio: {audio_mode})")


if __name__ == "__main__":
    main()
