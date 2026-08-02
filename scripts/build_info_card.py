#!/usr/bin/env python3
"""data/profile.json -> animated info-card SVG.

    python scripts/build_info_card.py            # -> info-card.svg
    python scripts/build_info_card.py out.svg

Chip and link widths are pinned with textLength (monospace) so the card cannot
overflow because of font-metric differences once GitHub rasterizes it.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "profile.json")
W, PAD = 520, 28
MONO_ADV = 7.0          # monospace advance at 12px, used to size chips/links


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_svg(p):
    x = PAD
    parts = []

    # --- name + blinking cursor -------------------------------------------
    name = p.get("name", "")
    name_tl = max(1, len(name)) * 15.0
    y = 58
    parts.append(
        f'<text class="name" x="{x}" y="{y}" textLength="{name_tl:.1f}" '
        f'lengthAdjust="spacing">{_esc(name)}</text>'
    )
    parts.append(f'<rect class="cur" x="{x + name_tl + 8:.1f}" y="{y - 18}" width="11" height="22" rx="2"/>')

    # --- role . location ---------------------------------------------------
    y += 26
    role, loc = p.get("role", ""), p.get("location", "")
    sub = role + (f"    ·    {loc}" if loc else "")
    parts.append(f'<text class="role" x="{x}" y="{y}">{_esc(sub)}</text>')

    # --- stack chips (wrap) ------------------------------------------------
    y += 36
    parts.append(f'<text class="h" x="{x}" y="{y}">STACK</text>')
    y += 14
    cx, cy = x, y
    for item in p.get("stack", []):
        tl = len(item) * MONO_ADV
        cw = tl + 18
        if cx + cw > W - PAD:
            cx, cy = x, cy + 30
        parts.append(
            f'<g class="chip"><rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="22" rx="6" '
            f'fill="{theme.PANEL}" stroke="{theme.STROKE}"/>'
            f'<text class="cht" x="{cx + 9:.1f}" y="{cy + 15}" textLength="{tl:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{_esc(item)}</text></g>'
        )
        cx += cw + 8
    y = cy + 22 + 28

    # --- now ---------------------------------------------------------------
    parts.append(f'<text class="h" x="{x}" y="{y}">NOW</text>')
    y += 20
    for line in p.get("now", []):
        parts.append(f'<circle cx="{x + 3}" cy="{y - 4}" r="3" fill="{theme.ACCENT2}"/>')
        parts.append(f'<text class="now" x="{x + 14}" y="{y}">{_esc(line)}</text>')
        y += 22
    y += 14

    # --- links -------------------------------------------------------------
    links = p.get("links", [])
    if links:
        parts.append(f'<text class="h" x="{x}" y="{y}">LINKS</text>')
        y += 20
        lx = x
        for i, link in enumerate(links):
            label = link.get("label", "")
            tl = len(label) * MONO_ADV
            # Rendered as an <img>, so the SVG is inert: show the label as text,
            # the clickable URLs live in the README next to the card.
            parts.append(
                f'<text class="lnk" x="{lx:.1f}" y="{y}" '
                f'textLength="{tl:.1f}" lengthAdjust="spacing">{_esc(label)}</text>'
            )
            lx += tl + 22
            if i < len(links) - 1:
                parts.append(f'<text class="sep" x="{lx - 15:.1f}" y="{y}">·</text>')
        y += 16

    H = round(y + PAD)
    body = "\n".join("    " + s for s in parts)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Profile info card">
  <style>
    .name {{ font-family:{theme.SANS}; font-size:26px; font-weight:700; fill:{theme.FG}; }}
    .role {{ font-family:{theme.SANS}; font-size:14px; fill:{theme.ACCENT}; }}
    .h    {{ font-family:{theme.MONO}; font-size:11px; letter-spacing:2px; fill:{theme.MUTED}; }}
    .cht  {{ font-family:{theme.MONO}; font-size:12px; fill:{theme.ACCENT2}; }}
    .now  {{ font-family:{theme.SANS}; font-size:13px; fill:{theme.FG}; }}
    .lnk  {{ font-family:{theme.MONO}; font-size:12px; fill:{theme.ACCENT}; }}
    .sep  {{ font-family:{theme.SANS}; font-size:13px; fill:{theme.MUTED}; }}
    .cur  {{ fill:{theme.ACCENT2}; animation:blink 1.1s steps(1) infinite; }}
    /* Card body never animates opacity (stays visible in a frozen frame); the
       intro only slides it up. */
    .in   {{ animation:rise .6s ease-out both; }}
    @keyframes blink {{ 0%,50% {{ opacity:1; }} 51%,100% {{ opacity:0; }} }}
    @keyframes rise  {{ from {{ transform:translateY(10px); }} to {{ transform:translateY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .cur {{ animation:none; opacity:1; }}
      .in  {{ animation:none; transform:none; }}
    }}
  </style>
  <rect width="{W}" height="{H}" rx="{theme.RADIUS}" fill="{theme.BG}"/>
  <g class="in">
{body}
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="{theme.RADIUS}" fill="none" stroke="{theme.STROKE}"/>
</svg>
'''


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    with open(DATA, encoding="utf-8") as f:
        profile = json.load(f)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_svg(profile))
    print(f"wrote {out}  (name={profile.get('name')!r}, stack={len(profile.get('stack', []))} items)")
