# Recipe: Premiere Pro / After Effects

## Premiere Pro
**Sequence:** 1080×1920, 25 or 30fps.

**Card frame (adjustment-layer template):**
1. V1: footage. Scale each clip to cover 1040×1330, then nest everything (or use the method below).
2. Apply **Crop** to a nest of your edit: Left/Right ≈ 1.85%, Top ≈ 13.8%, Bottom ≈ 16.9%. Set **Edge Feather 0** and turn on **Zoom off**.
   - Premiere's Crop has no rounding. The easy way is to skip the crop and put **`presets/card_frame.png`** (black with a rounded transparent hole) on the top track over the whole edit. Then scale the footage to fill the hole.
3. Add an **adjustment layer** over the footage: Lumetri → Exposure −0.5, Contrast +8, Saturation 90.

**Captions:**
- Text → Transcribe → Create captions. Set **Max length = 25 characters** and **Lines = single** to get 2–4 word chunks.
- Style: Inter/Helvetica Medium, about 62px, white, no stroke, no shadow. Save as a **Track Style**.
- Blur-in: captions on a caption track can't be animated, so **upgrade captions to graphics** and apply a saved **preset**: Gaussian Blur 18 → 0 and Opacity 0 → 100 over 4 frames, easing out. Make it once, then save it with *Save Preset → Anchor to In Point*.

**Accent word:**
- Graphic text in Anton (caps), Scale Height about 170% (unlink scale), centered.
- Put the texture clip on the track **below**. On the texture, add **Track Matte Key** → matte = the text track, composite using **Matte Alpha**.

## After Effects (most accurate)
1. Comp 1080×1920, black.
2. Footage precomp at 1040×1330. Draw a **Rounded Rectangle shape** (roundness 45) as an **Alpha Matte** above it. Position the precomp at (540, 930).
3. Adjustment layer: Curves/Exposure −0.5, Hue/Sat −10.
4. Caption animation preset on text layers: Gaussian Blur 18 → 0 and Opacity 0 → 100 over 4 frames, with Easy Ease Out. Save it as an **.ffx** animation preset.
5. Accent word: text layer (Anton, vertical scale 170%) set as the **Alpha Matte** for a texture layer.
6. Export it as a **.mogrt** to reuse in Premiere.
