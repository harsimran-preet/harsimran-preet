"""Shared design tokens for the three profile SVGs.

Colors and type live HERE, not inline in the build scripts, so the portrait,
heatmap, and info card never drift apart. Change a value once and rebuild.
"""

# ---- palette (dark) --------------------------------------------------------
BG      = "#0d1117"   # card background
PANEL   = "#0f151d"   # inner chips / panels
STROKE  = "#232b36"   # hairline borders
FG      = "#e6edf3"   # primary text
MUTED   = "#8b949e"   # secondary text / labels
ACCENT  = "#58a6ff"   # blue accent
ACCENT2 = "#3fb950"   # green accent
WARN    = "#d29922"

# contribution-heatmap ramp, empty -> most active (5 buckets)
HEAT = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# ---- type ------------------------------------------------------------------
# Generic families ONLY. No @font-face, no named webfonts: a downloaded or
# missing font falls back unpredictably once GitHub rasterizes the SVG.
MONO = "monospace"
SANS = "sans-serif"

# ---- geometry --------------------------------------------------------------
RADIUS = 12           # card corner radius
