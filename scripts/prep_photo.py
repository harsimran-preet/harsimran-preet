"""
Prepare a portrait photo for clean ASCII conversion, then hand off to
make_ascii_svg.py. Output: source-prepped.png (grayscale, subject on WHITE so
the background reads as blank -- white -> spaces in the ascii ramp).

Tuned for an evenly-lit headshot on a LIGHT background (the background is simply
whitened to pure white; no cutout matte needed). For a busy or dark background,
reach for rembg or an alpha matte instead.

Tonal step is Avi Vashishta's CLAHE (github.com/AVIVASHISHTA29) when OpenCV is
available -- local contrast so features stay crisp -- with a numpy fallback so
the script still runs on just Pillow + numpy.

    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageOps, ImageFilter

try:
    import cv2
except ImportError:
    cv2 = None

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

CROP = (100, 40, 950, 890)   # head + shoulders on the 1024x1024 source
WHITE_CUT = 200              # grayscale >= this -> pure white (blank background)

im = Image.open(INP).convert("RGB").crop(CROP)
gray = np.asarray(ImageOps.grayscale(im))

if cv2 is not None:
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
else:
    a = (gray.astype(np.float32) - 128.0) * 1.12 + 128.0
    gray = np.clip(a, 0, 255).astype(np.uint8)

g = Image.fromarray(gray, "L").filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))
arr = np.asarray(g).copy()
arr[arr >= WHITE_CUT] = 255      # whiten the light background + blown highlights

# Pad to a square so make_ascii_svg's 100x53 resample (shown in 8x15 cells ~=
# square art) doesn't stretch the face. White padding stays blank in the ramp.
side = max(arr.shape)
canvas = np.full((side, side), 255, np.uint8)
oy = (side - arr.shape[0]) // 2
ox = (side - arr.shape[1]) // 2
canvas[oy:oy + arr.shape[0], ox:ox + arr.shape[1]] = arr

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape, "(cv2 CLAHE)" if cv2 else "(numpy fallback)")
