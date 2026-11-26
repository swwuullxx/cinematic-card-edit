# Style guide: Cinematic Card

This guide comes from a frame-by-frame breakdown of a 10.7s, 9:16, 25fps reference short. All values are given for a **1080×1920** canvas.

## 1. Frame / layout

The footage never fills the screen. It sits inside a **rounded "card"** on solid black. This is the most recognisable part of the style.

| Property | Value |
|---|---|
| Canvas | 1080×1920, background `#000000` |
| Card | 1040×1330 (about 4:5), x = 20, y = 265 |
| Margins | About 20px left/right, about 265px top, about 325px bottom (the card sits slightly **above** center) |
| Corner radius | About 45px |
| Fill | Footage is scaled to *cover* the card and center-cropped |

## 2. Grade

- Exposure is pulled down about 30% (equivalent to a 30% black solid over the footage)
- Contrast +5–10%, saturation −10%
- Blacks are crushed, and highlights roll off softly
- B-roll is moody: teal/cold for struggle, warm tungsten for work, dark luxury for "success"

## 3. Cutting

Cut timeline from the reference:

| Time | Shot | Role | Caption(s) |
|---|---|---|---|
| 0.00–1.40 | Speaker at mic | A-roll | Listen → for now |
| 1.40–2.44 | Dark room, laptop | B-roll | Put your head → down and just |
| 2.44–3.44 | Bright loft, laptop | B-roll | down and just → **WORK** at 2.96 |
| 3.44–4.56 | Teal side profile | B-roll | Ignore the noise. |
| 4.56–5.92 | Beanie, snow | B-roll | Ignore → the distractions. |
| 5.92–7.08 | Speaker | A-roll | Prove to yourself |
| 7.08–8.40 | Bearded close-up | B-roll | that you can → really do it. |
| 8.40–9.84 | Speaker | A-roll | And then go show → the rest of the → world that you did. |
| 9.84–10.70 | Suit, dark luxury | B-roll | world that you did. |

Rules:
1. **Hard cuts only.** No transitions, zooms, whips, flashes or shakes.
2. **Shot length is 0.5–1.5s, averaging about 1.1s.**
3. **Cut on phrase boundaries** (between caption chunks), never mid-word.
4. **Pattern:** speaker → 2–4 B-roll → speaker → 1 B-roll → speaker → closing B-roll.
5. **B-roll is literal:** "put your head down" → someone grinding at a laptop.
6. **Captions are independent of cuts.** A caption can span a cut (e.g. "world that you did." carries over the last cut), which makes the edit feel like one continuous thought.
7. End on an aspirational B-roll shot, such as success or luxury.

## 4. Captions

| Property | Value |
|---|---|
| Font | Neo-grotesk sans: **Inter Display Medium** (bundled), SF Pro Display, Helvetica Neue or Arial |
| Weight | Regular/Medium. Never bold. |
| Size | About 62px. Small and understated. |
| Color | `#FFFFFF`, with **no** stroke, shadow or background box |
| Case | Sentence case, with a period only at the end of a sentence |
| Position | Centered, about 52% down the canvas (y ≈ 1000) |
| Chunking | **2–4 words**, split at natural phrase breaks |
| In | **Blur + fade** over about 0.14s (4 frames @30fps, 3–4 @25fps). Gaussian blur 18 → 0, opacity 0 → 100, ease-out. |
| Out | **Hard cut** (the next caption replaces it instantly) |

## 5. Accent word

Use it once per video, on the single most important word.

| Property | Value |
|---|---|
| Font | Ultra-condensed heavy display: **Anton** (bundled), Bebas Neue Bold, Druk Condensed or League Gothic |
| Shape | ALL CAPS, stretched vertically about 1.7× so it's tall and narrow |
| Size | About 500px wide (about 46% of the canvas), about 400px tall |
| Position | Centered, y ≈ 960 |
| Fill | **Image texture inside the letters** (bright sky/clouds/chrome), via a clipping mask or track matte |
| In/Out | Hard cut in on the spoken word, hold about 0.5s, hard cut out |
| Captions | Hidden while the accent word is on screen |

Good accent words: WORK, FOCUS, DISCIPLINE, NOW, YOU, PROVE, GRIND, WIN.

## 6. Audio

The breakdown covered visuals only. In this genre it's typically a clean voiceover, optionally over a low, moody ambient or piano bed.
