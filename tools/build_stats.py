#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub signal card builder
==========================
Fetches the public GitHub API + contribution calendar, then renders
`assets/github-stats.svg` in the same Liquid Glass language as the rest
of the profile.

Run:  python tools/build_stats.py
      GITHUB_TOKEN=ghp_xxx python tools/build_stats.py   (recommended)

The GitHub Action in .github/workflows/profile-stats.yml runs this daily.
"""

from __future__ import annotations

import collections
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_assets import (  # noqa: E402
    A, BLUE, CYAN, DIM, FONT, INK, MINT, MONO, MUTED, ROSE, VIOLET,
    Doc, esc, setup_canvas, txt,
)

USER = "rifkillah"
API = "https://api.github.com"
CACHE = A / "github-stats.json"
OUT = A / "github-stats.svg"
OUT_MOBILE = A / "github-stats-mobile.svg"

HEADERS = {
    "User-Agent": f"{USER}-profile-stats",
    "Accept": "application/vnd.github+json",
}
if os.environ.get("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"

# Bootstrap used only when GitHub's anonymous rate limit is exhausted and no
# cache exists yet. The scheduled Action always refreshes this with a token.
BOOTSTRAP_LANGS = {
    "PHP": 1_351_903,      # PHP + Blade
    "Kotlin": 281_134,
    "Java": 176_320,
    "Hack": 91_862,
    "CSS": 70_566,
    "Python": 29_453,
    "JavaScript": 10_158,
    "Dockerfile": 2_404,
}


# ── network ────────────────────────────────────────────────────────────────
def get_json(url: str, tries: int = 3):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.2 * (attempt + 1))
    raise last


def collect() -> dict:
    user = get_json(f"{API}/users/{USER}")
    repos = get_json(f"{API}/users/{USER}/repos?per_page=100&sort=updated")

    languages = collections.Counter()
    for repo in repos:
        try:
            for name, size in get_json(repo["languages_url"]).items():
                languages[name] += size
        except Exception:  # noqa: BLE001 — rate limit on a single repo is fine
            continue
    if not languages:
        languages.update(BOOTSTRAP_LANGS)

    # contribution calendar (public endpoint used by the profile page)
    cal = get_json(f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last")
    days = cal["contributions"]
    total = int(cal.get("total", {}).get("lastYear", sum(d["count"] for d in days)))

    # merge Blade into PHP: Blade is a template syntax, not a separate language
    if "Blade" in languages:
        languages["PHP"] += languages.pop("Blade")

    total_bytes = sum(languages.values()) or 1
    top = [
        {"name": name, "bytes": size, "pct": round(size / total_bytes * 100, 1)}
        for name, size in languages.most_common(6)
    ]

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "user": {
            "login": USER,
            "repos": user["public_repos"],
            "followers": user["followers"],
            "created": user["created_at"][:4],
        },
        "contributions": {
            "total": total,
            "days": days,
        },
        "languages": top,
        "language_count": len(languages),
    }


# ── derived numbers ────────────────────────────────────────────────────────
def streaks(days):
    current = longest = run = 0
    for day in days:
        if day["count"] > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    # a streak stays alive if today has no contributions yet
    tail = list(reversed(days))
    if tail and tail[0]["count"] == 0:
        tail = tail[1:]
    for day in tail:
        if day["count"] > 0:
            current += 1
        else:
            break
    return current, longest


# ── svg ────────────────────────────────────────────────────────────────────
LEVELS = ["#FFFFFF", "#1D3A5C", "#2C5F92", "#4C93D6", "#9BD8FF"]


def build_desktop(data: dict) -> str:
    d = Doc(1200, 470, "stats", radius=34)
    setup_canvas(d, [
        (110, 20, 380, "#2563EB", .34, "fl-a"),
        (1090, 470, 420, "#7C3AED", .30, "fl-b"),
        (700, 520, 360, "#0891B2", .18, "fl-c"),
    ])
    d.add(d.rv(d.panel(0, 0, 1200, 470, 34, sweep=True), .02, "rv-s"))

    days = data["contributions"]["days"]
    total = data["contributions"]["total"]
    current, longest = streaks(days)
    langs = data["languages"]

    # ── masthead ──────────────────────────────────────────────────────────
    d.add(d.rv(txt(56, 46, "GITHUB SIGNAL", size=11, fill=CYAN, weight=700, ls=4.2, family=MONO), .06))
    d.add(d.rv(txt(56, 66, "Ritme kerja, bukan angka kosong.", size=15, fill=MUTED), .11))
    stamp = data["generated"].replace("T", " ").replace("Z", " UTC")
    d.add(d.rv(
        txt(1144, 46, "LAST 12 MONTHS", size=9, fill=DIM, weight=600, ls=2.4,
            anchor="end", family=MONO) +
        txt(1144, 64, f"synced {stamp}", size=9, fill=DIM, weight=500,
            anchor="end", family=MONO),
        .08))

    # ── stat strip ────────────────────────────────────────────────────────
    stats = [
        (str(total), "CONTRIBUTIONS", MINT),
        (f"{current}", "DAY STREAK", BLUE),
        (str(data["user"]["repos"]), "PUBLIC REPOS", VIOLET),
        (str(data["language_count"]), "LANGUAGES", ROSE),
    ]
    for i, (value, label, color) in enumerate(stats):
        x = 56 + i * 278
        d.add(d.rv(
            f'<circle cx="{x + 3:g}" cy="106" r="3" fill="{color}" class="dotpulse"/>' +
            txt(x, 148, value, size=38, weight=800, fill=INK, ls=-1) +
            txt(x, 168, label, size=9.5, fill=DIM, weight=600, ls=2.2) +
            (f'<line x1="{x - 40:g}" y1="104" x2="{x - 40:g}" y2="170" stroke="#FFFFFF" '
             f'stroke-opacity=".10"/>' if i else ""),
            .16 + i * .07))

    d.add(d.rv(
        txt(1144, 148, f"longest streak {longest}d", size=10, fill=DIM,
            anchor="end", family=MONO) +
        txt(1144, 168, f"member since {data['user']['created']}", size=10, fill=DIM,
            anchor="end", family=MONO),
        .30))

    # ── contribution heatmap ──────────────────────────────────────────────
    left, top, step, cell = 56, 236, 12, 9
    d.add(d.rv(txt(left, 202, "CONTRIBUTION MAP", size=10, fill=MUTED, weight=700, ls=2.6, family=MONO), .20))

    # pad the first week so Sunday starts on the top row
    pad = (datetime.strptime(days[0]["date"], "%Y-%m-%d").weekday() + 1) % 7
    cells = [None] * pad + days

    # each week fades in a beat after the previous one: a slow left-to-right wave
    for col in range((len(cells) + 6) // 7):
        parts = []
        for row in range(7):
            idx = col * 7 + row
            if idx >= len(cells) or cells[idx] is None:
                continue
            day = cells[idx]
            color = LEVELS[min(int(day["level"]), 4)]
            x = left + col * step
            y = top + row * step
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.4" fill="{color}" opacity="{".07" if day["count"] == 0 else "1"}"/>')
            if day["count"] >= 10:
                parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.4" fill="none" stroke="{MINT}" stroke-opacity=".5" stroke-width=".8"/>')
        d.add(f'<g class="pop" style="animation-delay:{.24 + col * .014:.3f}s">{"".join(parts)}</g>')

    # month labels
    months = []
    last_month = None
    for idx, day in enumerate(cells):
        if day is None:
            continue
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        if dt.month != last_month:
            last_month = dt.month
            x = left + (idx // 7) * step
            months.append(txt(x, 228, dt.strftime("%b").upper(), size=7, fill=DIM, weight=600, ls=.6, family=MONO))
    d.add(d.rv("".join(months), .30))

    # legend
    legend = [txt(left, 336, "LESS", size=8, fill=DIM, weight=600, ls=1.2, family=MONO)]
    lx = left + 34
    for i, color in enumerate(LEVELS):
        extra = ' stroke="#FFFFFF" stroke-opacity=".18"' if i == 0 else ""
        op = ".10" if i == 0 else "1"
        legend.append(f'<rect x="{lx}" y="327" width="9" height="9" rx="2.4" fill="{color}" opacity="{op}"{extra}/>')
        lx += 13
    legend.append(txt(lx + 4, 336, "MORE", size=8, fill=DIM, weight=600, ls=1.2, family=MONO))
    d.add(d.rv("".join(legend), .62))
    d.add(d.rv(
        txt(left, 366, "Setiap kotak adalah satu hari. Garis mint menandai hari dengan 10+ kontribusi.", size=10, fill=DIM) +
        txt(left, 386, f"{total} kontribusi dalam 12 bulan terakhir · streak terpanjang {longest} hari.", size=10, fill=DIM),
        .70))

    # ── language bars ─────────────────────────────────────────────────────
    d.d("""
<linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#6EA8FF"/>
  <stop offset=".55" stop-color="#67E8F9"/>
  <stop offset="1" stop-color="#6EE7B7"/>
</linearGradient>""")
    bx, bw = 720, 424
    d.add(d.rv(txt(bx, 202, "MOST WRITTEN", size=10, fill=MUTED, weight=700, ls=2.6, family=MONO), .26))

    for i, lang in enumerate(langs):
        y = 240 + i * 34
        d.add(d.rv(
            txt(bx, y - 6, lang["name"], size=12, fill="#DCE8F8", weight=600) +
            txt(bx + bw, y - 6, f"{lang['pct']:.0f}%", size=11, fill=MUTED,
                anchor="end", family=MONO),
            .34 + i * .07))
        d.add(d.rv(f'<rect x="{bx}" y="{y}" width="{bw}" height="5" rx="2.5" fill="#FFFFFF" fill-opacity=".07"/>',
                   .38 + i * .07))
        # the bar itself grows out of its baseline, one language after another
        d.add(f'<rect x="{bx}" y="{y}" width="{max(4, bw * lang["pct"] / 100):.1f}" height="5" rx="2.5" '
              f'fill="url(#barGrad)" class="grow" style="animation-delay:{.42 + i * .08:.2f}s"/>')

    d.add(d.rv(txt(bx, 430, "Blade digabung ke PHP · JavaScript & Dockerfile <1% · publik saja", size=9.5, fill=DIM), .78))

    # ── footer ────────────────────────────────────────────────────────────
    d.add(d.rv(
        '<line x1="56" y1="440" x2="1144" y2="440" stroke="#FFFFFF" stroke-opacity=".08"/>' +
        txt(56, 456, "source  GitHub REST API + contribution calendar", size=8.5, fill=DIM, family=MONO) +
        txt(1144, 456, "auto-refresh  tools/build_stats.py", size=8.5, fill=DIM,
            anchor="end", family=MONO),
        .84))

    return d.render()


def build_mobile(data: dict) -> str:
    """480×788 stacked variant — same data, readable on a phone."""
    W, H = 480, 788
    d = Doc(W, H, "statsm", radius=30)
    setup_canvas(d, [
        (50, 10, 250, "#2563EB", .34, "fl-a"),
        (450, 470, 300, "#7C3AED", .30, "fl-b"),
        (240, 800, 280, "#0891B2", .16, "fl-c"),
    ])
    d.add(d.rv(d.panel(0, 0, W, H, 30, sweep=True), .02, "rv-s"))

    days = data["contributions"]["days"]
    total = data["contributions"]["total"]
    current, longest = streaks(days)
    langs = data["languages"]
    pad = 36

    # ── masthead ──────────────────────────────────────────────────────────
    stamp = data["generated"].replace("T", " ").replace("Z", " UTC")
    d.add(d.rv(txt(pad, 44, "GITHUB SIGNAL", size=10, fill=CYAN, weight=700, ls=3.2, family=MONO), .06))
    d.add(d.rv(
        txt(W - pad, 40, "LAST 12 MONTHS", size=8.5, fill=DIM, weight=600, ls=1.8,
            anchor="end", family=MONO) +
        txt(W - pad, 54, f"synced {stamp}", size=8.5, fill=DIM, weight=500,
            anchor="end", family=MONO),
        .09))
    d.add(d.rv(txt(pad, 68, "Ritme kerja, bukan angka kosong.", size=14, fill=MUTED), .14))

    # ── stat cards 2×2 ────────────────────────────────────────────────────
    stats = [
        (str(total), "CONTRIBUTIONS", MINT),
        (str(current), "DAY STREAK", BLUE),
        (str(data["user"]["repos"]), "PUBLIC REPOS", VIOLET),
        (str(data["language_count"]), "LANGUAGES", ROSE),
    ]
    cw, ch, gap = 200, 74, 8
    for i, (value, label, color) in enumerate(stats):
        x = pad + (i % 2) * (cw + gap)
        y = 92 + (i // 2) * (ch + gap)
        d.add(d.rv(
            d.panel(x, y, cw, ch, 16) +
            f'<circle cx="{x + 16:g}" cy="{y + 17:g}" r="2.8" fill="{color}" class="dotpulse"/>' +
            txt(x + 16, y + 50, value, size=30, weight=800, fill=INK, ls=-.8) +
            txt(x + 16, y + 64, label, size=8, fill=DIM, weight=600, ls=1.6),
            .18 + i * .08, "rv-s"))
    d.add(d.rv(
        txt(pad, 266, "longest streak", size=8.5, fill=DIM, family=MONO) +
        txt(pad + 84, 266, f"{longest} days", size=8.5, fill=BLUE, weight=600, family=MONO) +
        txt(W - pad, 266, f"member since {data['user']['created']}", size=8.5, fill=DIM,
            anchor="end", family=MONO),
        .50))

    # ── contribution heatmap ──────────────────────────────────────────────
    left, top, step, cell = pad, 322, 7.5, 5.6
    d.add(d.rv(txt(left, 292, "CONTRIBUTION MAP", size=9.5, fill=MUTED, weight=700, ls=2.2, family=MONO), .56))

    first = (datetime.strptime(days[0]["date"], "%Y-%m-%d").weekday() + 1) % 7
    cells = [None] * first + days

    months = []
    last_month = None
    for idx, day in enumerate(cells):
        if day is None:
            continue
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        if dt.month != last_month:
            last_month = dt.month
            months.append(txt(left + (idx // 7) * step, 312, dt.strftime("%b").upper(),
                              size=6, fill=DIM, weight=600, ls=.4, family=MONO))
    d.add(d.rv("".join(months), .60))

    for col in range((len(cells) + 6) // 7):
        parts = []
        for row in range(7):
            idx = col * 7 + row
            if idx >= len(cells) or cells[idx] is None:
                continue
            day = cells[idx]
            color = LEVELS[min(int(day["level"]), 4)]
            x, y = left + col * step, top + row * step
            op = ".07" if day["count"] == 0 else "1"
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="1.7" fill="{color}" opacity="{op}"/>')
            if day["count"] >= 10:
                parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="1.7" fill="none" stroke="{MINT}" stroke-opacity=".6" stroke-width=".7"/>')
        d.add(f'<g class="pop" style="animation-delay:{.46 + col * .013:.3f}s">{"".join(parts)}</g>')

    # legend
    legend = [txt(left, 402, "LESS", size=7, fill=DIM, weight=600, ls=1, family=MONO)]
    lx = left + 28
    for i, color in enumerate(LEVELS):
        extra = ' stroke="#FFFFFF" stroke-opacity=".18"' if i == 0 else ""
        op = ".10" if i == 0 else "1"
        legend.append(f'<rect x="{lx}" y="394.5" width="7" height="7" rx="1.8" fill="{color}" opacity="{op}"{extra}/>')
        lx += 10
    legend.append(txt(lx + 3, 402, "MORE", size=7, fill=DIM, weight=600, ls=1, family=MONO))
    d.add(d.rv("".join(legend), 1.18))
    d.add(d.rv(
        txt(left, 422, "Setiap kotak adalah satu hari.", size=8.5, fill=DIM) +
        txt(left, 436, "Garis mint menandai hari dengan 10+ kontribusi.", size=8.5, fill=DIM) +
        txt(left, 454, f"{total} kontribusi dalam 12 bulan terakhir.", size=8.5, fill=MUTED),
        1.26))

    # ── languages ─────────────────────────────────────────────────────────
    d.add(d.rv('<line x1="36" y1="476" x2="444" y2="476" stroke="#FFFFFF" stroke-opacity=".08"/>', 1.34))
    d.add(d.rv(txt(left, 500, "MOST WRITTEN", size=9.5, fill=MUTED, weight=700, ls=2.2, family=MONO), 1.38))
    d.d("""
<linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#6EA8FF"/>
  <stop offset=".55" stop-color="#67E8F9"/>
  <stop offset="1" stop-color="#6EE7B7"/>
</linearGradient>""")
    bw = 408
    for i, lang in enumerate(langs):
        y = 524 + i * 35
        d.add(d.rv(
            txt(left, y, lang["name"], size=11.5, fill="#DCE8F8", weight=600) +
            txt(left + bw, y, f"{lang['pct']:.0f}%", size=10, fill=MUTED,
                anchor="end", family=MONO),
            1.46 + i * .07))
        d.add(d.rv(f'<rect x="{left}" y="{y + 8}" width="{bw}" height="5" rx="2.5" fill="#FFFFFF" fill-opacity=".07"/>',
                   1.50 + i * .07))
        d.add(f'<rect x="{left}" y="{y + 8}" width="{max(4, bw * lang["pct"] / 100):.1f}" height="5" rx="2.5" '
              f'fill="url(#barGrad)" class="grow" style="animation-delay:{1.54 + i * .08:.2f}s"/>')

    d.add(d.rv(txt(left, 728, "Blade digabung ke PHP · JavaScript & Dockerfile <1%", size=8.5, fill=DIM), 1.90))

    # ── footer ────────────────────────────────────────────────────────────
    d.add(d.rv(
        '<line x1="36" y1="746" x2="444" y2="746" stroke="#FFFFFF" stroke-opacity=".08"/>' +
        txt(left, 764, "source  GitHub REST API + calendar", size=8, fill=DIM, family=MONO) +
        txt(W - pad, 764, "auto-refresh daily", size=8, fill=DIM,
            anchor="end", family=MONO),
        1.96))

    return d.render()


def main():
    cached = None
    if CACHE.exists():
        try:
            cached = json.loads(CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cached = None

    if "--offline" in sys.argv:
        if cached is None:
            raise SystemExit("No cached assets/github-stats.json to render offline.")
        data = cached
        print("  offline mode · rendering from cache")
    else:
        try:
            data = collect()
        except Exception as exc:  # noqa: BLE001 — keep the last good card alive
            print(f"! GitHub API unavailable ({exc}).", file=sys.stderr)
            if cached is None:
                raise
            print("  using cached assets/github-stats.json", file=sys.stderr)
            data = cached

    CACHE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    OUT.write_text(build_desktop(data), encoding="utf-8")
    OUT_MOBILE.write_text(build_mobile(data), encoding="utf-8")
    for path in (OUT, OUT_MOBILE):
        print(f"  · {path.name:24s} {path.stat().st_size / 1024:6.1f} KB")
    print(f"  · {data['contributions']['total']} contributions · {data['user']['repos']} repos · {data['language_count']} languages")


if __name__ == "__main__":
    main()
