#!/usr/bin/env python3
"""Photo -> animated ASCII-portrait SVG.

Pipeline: grayscale -> auto-exposure -> brightness/contrast -> resample to
COLS wide -> map each cell onto a 10-level glyph ramp -> emit one monospaced
<text> row per line, each pinned with textLength so the grid can never
overflow the viewBox on a machine whose "monospace" is wider than mine.

    python scripts/build_ascii.py            # -> portrait.svg
    python scripts/build_ascii.py out.svg    # custom output path

Tune via the CONFIG block. Preview the raw grid in a terminal with:

    python -c "import sys; sys.path.insert(0,'scripts'); import build_ascii as b; \
               print('\\n'.join(b.to_rows('source-photo.jpg')))"
"""
import os
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme

# ============================== CONFIG ==============================
SRC         = "source-photo.jpg"   # cropped-tight, background-removed face
COLS        = 108                  # detail vs. file size; below ~80 a face stops reading
CONTRAST    = 1.6                  # THE knob: ramp is only 10 levels, so push until features separate
BRIGHTNESS  = 0.86                 # >1 lighter (raise for dark photos)
INVERT      = False                # True if the subject is light-on-dark
AUTOCONTRAST = True                # normalize exposure before the manual knobs
SHARPEN     = 140                  # unsharp-mask % after downscale; crisps eyes/nose/mouth (0 = off)
CHAR_ASPECT = 0.50                 # monospace cell width/height; corrects vertical squash
RAMP        = " .:-=+*#%@"         # exactly 10 levels, dark -> dense
FONT_SIZE   = 11                   # px; textLength still pins the true width
# ====================================================================

CELL_W = FONT_SIZE * 0.60          # nominal glyph advance
LINE_H = CELL_W / CHAR_ASPECT      # row pitch that keeps the face un-stretched
PAD    = 22

assert len(RAMP) == 10, "RAMP must stay 10 levels (see CONTRAST note)"


def to_rows(path=SRC):
    """Return the ASCII portrait as a list of equal-length strings (one per row)."""
    img = Image.open(path).convert("L")
    if AUTOCONTRAST:
        img = ImageOps.autocontrast(img, cutoff=1)
    w, h = img.size
    rows = max(1, round(COLS * (h / w) * CHAR_ASPECT))
    img = img.resize((COLS, rows), Image.LANCZOS)
    if SHARPEN:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=SHARPEN, threshold=1))
    img = ImageEnhance.Brightness(img).enhance(BRIGHTNESS)
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)
    ramp = RAMP[::-1] if INVERT else RAMP
    top = len(ramp) - 1
    px = img.load()
    return [
        "".join(ramp[round(px[x, y] / 255 * top)] for x in range(COLS))
        for y in range(rows)
    ]


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_svg(rows):
    """Wrap the character grid in a self-contained, declaratively animated SVG."""
    textlen = COLS * CELL_W
    W = round(textlen + 2 * PAD)
    H = round(len(rows) * LINE_H + 2 * PAD)
    stagger = 0.9 / max(1, len(rows))

    body = []
    for i, row in enumerate(rows):
        y = round(PAD + (i + 0.85) * LINE_H, 2)
        delay = round(i * stagger, 3)
        # textLength + lengthAdjust="spacingAndGlyphs" is load-bearing: it pins
        # every row to the same rendered width so a wider "monospace" cannot
        # push the right edge of the face past the viewBox.
        body.append(
            f'<text class="r" x="{PAD}" y="{y}" textLength="{textlen:.2f}" '
            f'lengthAdjust="spacingAndGlyphs" style="animation-delay:{delay}s" '
            f'xml:space="preserve">{_esc(row)}</text>'
        )

    scan_h = round(2.2 * LINE_H, 1)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Animated ASCII-art portrait">
  <defs>
    <linearGradient id="ink" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{theme.ACCENT2}"/>
      <stop offset="1" stop-color="{theme.ACCENT}"/>
    </linearGradient>
    <clipPath id="card"><rect x="0" y="0" width="{W}" height="{H}" rx="{theme.RADIUS}"/></clipPath>
  </defs>
  <style>
    /* Rows are ALWAYS visible (opacity never animates); the intro only slides
       them, so a static rasterization or a frozen first frame still shows the
       whole face instead of a blank card. */
    .r {{ font-family:{theme.MONO}; font-size:{FONT_SIZE}px; fill:url(#ink);
          opacity:.96; animation:reveal .55s ease-out both; }}
    .scan {{ opacity:.10; animation:scan 5.5s ease-in-out infinite; }}
    @keyframes reveal {{ from {{ transform:translateY(4px); }} to {{ transform:translateY(0); }} }}
    @keyframes scan   {{ 0% {{ transform:translateY(-6%); }} 50% {{ transform:translateY(102%); }} 100% {{ transform:translateY(-6%); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .r    {{ animation:none; transform:none; }}
      .scan {{ display:none; }}
    }}
  </style>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="{theme.BG}"/>
    <g>
{chr(10).join("      " + b for b in body)}
    </g>
    <rect class="scan" x="0" y="0" width="{W}" height="{scan_h}" fill="{theme.ACCENT}"/>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="{theme.RADIUS}" fill="none" stroke="{theme.STROKE}"/>
</svg>
'''


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "portrait.svg"
    grid = to_rows(SRC)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_svg(grid))
    print(f"wrote {out}  ({COLS}x{len(grid)} chars, contrast={CONTRAST}, invert={INVERT})")
