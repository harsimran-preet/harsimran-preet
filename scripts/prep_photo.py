"""
Prepare a portrait photo for clean ASCII conversion, then hand off to
make_ascii_svg.py. Output: source-prepped.png (grayscale, subject on WHITE so
the background reads as blank -- white -> spaces in the ascii ramp).

Tonal step is Avi Vashishta's (github.com/AVIVASHISHTA29): CLAHE local contrast
so a flatly- or harshly-lit face gains even highlights and shadows instead of
crushing one side to a solid black slab. Uses OpenCV when available (his exact
path); falls back to a numpy illumination-flatten so the script still runs with
only Pillow + numpy. Cutout here is a feathered elliptical head+shoulders matte
rather than his rembg -- good enough for a centered head-and-shoulders photo.

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

# crop + matte tuned for source-photo.jpg (433x433). Retune if the photo changes.
CROP = (100, 22, 330, 288)
CX, CY, RX, RY = 106, 95, 68, 118          # head ellipse (crop coords)
SHOULDER_Y, SXL, SXR = 182, 8, 180         # tapered shoulder band
FEATHER = 7

im = Image.open(INP).convert("RGB").crop(CROP)
gray = np.asarray(ImageOps.grayscale(im))
w, h = im.size

# --- tonal: even out the lighting so no half of the face is a black slab ------
if cv2 is not None:
    gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)   # slight global lift
else:
    a = gray.astype(np.float32)
    blur = np.asarray(
        Image.fromarray(gray).filter(ImageFilter.GaussianBlur(max(w, h) / 7.0))
    ).astype(np.float32)
    a = (a - 0.72 * (blur - float(blur.mean())) - 128.0) * 1.18 + 128.0 + 18.0
    gray = np.clip(a, 0, 255).astype(np.uint8)

g = Image.fromarray(gray, "L").filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=2))

# --- cutout: feathered head+shoulders matte, composite onto white -------------
yy, xx = np.mgrid[0:h, 0:w]
head = ((xx - CX) / RX) ** 2 + ((yy - CY) / RY) ** 2 <= 1.0
shoulders = (yy > SHOULDER_Y) & (xx > SXL) & (xx < SXR)
mask = (head | shoulders).astype(np.float32)
mask = np.asarray(
    Image.fromarray((mask * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(FEATHER))
).astype(np.float32) / 255.0

arr = np.asarray(g).astype(np.float32)
composited = np.clip(arr * mask + 255.0 * (1.0 - mask), 0, 255).astype("uint8")

# Pad to a square so make_ascii_svg's 100x53 resample (shown in 8x15 cells ~=
# square art) doesn't stretch the face. White padding stays blank in the ramp.
side = max(composited.shape)
canvas = np.full((side, side), 255, np.uint8)
oy = (side - composited.shape[0]) // 2
ox = (side - composited.shape[1]) // 2
canvas[oy:oy + composited.shape[0], ox:ox + composited.shape[1]] = composited

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape, "(cv2 CLAHE)" if cv2 else "(numpy fallback)")
