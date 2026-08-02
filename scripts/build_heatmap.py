#!/usr/bin/env python3
"""GitHub contributions -> animated contribution-heatmap SVG.

Auth comes from the environment, never a file:
    GH_USER   the login to graph (workflow passes github.repository_owner)
    GH_TOKEN  a token that can read contributions (workflow prefers the
              GH_READ_USER secret, else the built-in GITHUB_TOKEN)

    GH_USER=me GH_TOKEN=$(gh auth token) python scripts/build_heatmap.py heatmap.svg
    python scripts/build_heatmap.py out.svg --demo     # offline synthetic data
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme

API = "https://api.github.com/graphql"
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""

# ---- layout ----------------------------------------------------------------
CELL, GAP = 11, 3
STEP = CELL + GAP
LEFT, TOP = 30, 40         # weekday-label gutter, header + month-label band
PADX, PADY = 16, 14
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch(login, token):
    """Return (total, weeks) where weeks is a list of 7-long [(date, count)] lists."""
    import requests
    resp = requests.post(
        API,
        json={"query": QUERY, "variables": {"login": login}},
        headers={"Authorization": f"bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if payload.get("errors"):
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    user = payload["data"]["user"]
    if user is None:
        raise SystemExit(f"No such user: {login}")
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [(d["date"], d["contributionCount"]) for d in wk["contributionDays"]]
        for wk in cal["weeks"]
    ]
    return cal["totalContributions"], weeks


def demo():
    """Deterministic synthetic year, so the script is verifiable with no token."""
    rng = random.Random(7)
    weeks = []
    for w in range(53):
        days = []
        for d in range(7):
            count = 0 if rng.random() < 0.45 else rng.randint(1, 16)
            days.append((f"2025-{(w // 4) % 12 + 1:02d}-{(w % 4) * 7 + d + 1:02d}", count))
        weeks.append(days)
    total = sum(c for wk in weeks for _, c in wk)
    return total, weeks


def level(count, hi):
    if count <= 0:
        return 0
    for i, frac in enumerate((0.25, 0.50, 0.75)):
        if count <= max(1, round(hi * frac)):
            return i + 1
    return 4


def to_svg(total, weeks):
    ncols = len(weeks)
    grid_w = ncols * STEP - GAP
    W = PADX * 2 + LEFT + grid_w
    H = PADY * 2 + TOP + 7 * STEP - GAP + 30
    hi = max((c for wk in weeks for _, c in wk), default=0)

    cells, months = [], []
    last_m = None
    for wi, wk in enumerate(weeks):
        x = PADX + LEFT + wi * STEP
        if wk:
            m = int(wk[0][0][5:7])
            if m != last_m:
                months.append(f'<text class="lbl" x="{x}" y="{PADY + TOP - 10}">{MONTHS[m - 1]}</text>')
                last_m = m
        for di, (date, c) in enumerate(wk):
            y = PADY + TOP + di * STEP
            delay = round(wi * 0.016 + di * 0.004, 3)
            # No <title>: GitHub renders this as an <img>, where hover tooltips
            # never fire — they'd just be ~50 KB of dead weight committed daily.
            cells.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{theme.HEAT[level(c, hi)]}" style="animation-delay:{delay}s"/>'
            )

    weekdays = "".join(
        f'<text class="lbl" x="{PADX + LEFT - 8}" y="{PADY + TOP + di * STEP + CELL - 2}" '
        f'text-anchor="end">{name}</text>'
        for di, name in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )

    ly = H - PADY - CELL
    lx = W - PADX - (5 * (CELL + 3) + 78)
    legend = [f'<text class="lbl" x="{lx - 6}" y="{ly + CELL - 2}" text-anchor="end">Less</text>']
    for i, col in enumerate(theme.HEAT):
        legend.append(f'<rect x="{lx + i * (CELL + 3)}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{col}"/>')
    legend.append(f'<text class="lbl" x="{lx + 5 * (CELL + 3) + 6}" y="{ly + CELL - 2}">More</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub contribution heatmap">
  <style>
    /* Cells stay at full opacity; the wave only nudges them, so a frozen frame
       still shows the whole calendar rather than an empty grid. */
    .c   {{ opacity:1; animation:drop .5s ease-out both; }}
    .lbl {{ font-family:{theme.MONO}; font-size:10px; fill:{theme.MUTED}; }}
    .hdr {{ font-family:{theme.SANS}; font-size:14px; font-weight:600; fill:{theme.FG}; }}
    @keyframes drop {{ from {{ transform:translateY(-3px); }} to {{ transform:translateY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{ .c {{ animation:none; transform:none; }} }}
  </style>
  <rect width="{W}" height="{H}" rx="{theme.RADIUS}" fill="{theme.BG}"/>
  <text class="hdr" x="{PADX}" y="{PADY + 16}">{total} contributions in the last year</text>
  {"".join(months)}
  {weekdays}
  {"".join(cells)}
  {"".join(legend)}
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="{theme.RADIUS}" fill="none" stroke="{theme.STROKE}"/>
</svg>
'''


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    out = args[0] if args else "heatmap.svg"

    if "--demo" in sys.argv:
        total, weeks = demo()
    else:
        user = os.environ.get("GH_USER")
        token = os.environ.get("GH_TOKEN")
        if not user or not token:
            raise SystemExit("GH_USER and GH_TOKEN must be set (or pass --demo).")
        total, weeks = fetch(user, token)

    with open(out, "w", encoding="utf-8") as f:
        f.write(to_svg(total, weeks))
    print(f"wrote {out}  (total contributions: {total})")

    if "--demo" not in sys.argv and total == 0:
        sys.stderr.write(
            "WARNING: 0 contributions returned. The token likely lacks read:user "
            "scope. Create a classic PAT with read:user and set it as the repo "
            "secret GH_READ_USER (the workflow prefers it).\n"
        )
