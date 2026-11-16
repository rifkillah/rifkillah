#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Liquid Glass profile asset builder
==================================
Generates every SVG used by the profile README.

Design language
---------------
* deep midnight canvas + aurora light fields
* translucent glass panels with a 1px specular rim
* chromatic edge (cyan / magenta split) to fake dispersion
* animated sheen sweeps, floating elements and a slow orbit
* hand-built, zero-dependency SVG so GitHub can render it as an <img>

Run:  python tools/build_assets.py
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
SRC = A / "src"

# ── palette ────────────────────────────────────────────────────────────────
BG = "#060A12"
INK = "#EAF2FF"
MUTED = "#9DB0CC"
DIM = "#61738F"
BLUE = "#6EA8FF"
CYAN = "#67E8F9"
VIOLET = "#A78BFA"
MINT = "#6EE7B7"
ROSE = "#FDA4AF"
AMBER = "#FCD34D"

FONT = "'Inter','SF Pro Display','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace"

BASE_CSS = """
/* ------------------------------------------------------------------
   Motion system
   · one easing for everything: cubic-bezier(.22,.61,.36,1) (ease-out)
   · entrances finish within .85s and move at most 11px
   · ambient loops run at least 7s, amplitude under 15px
   · nothing bounces, spins fast, or changes hue
   ------------------------------------------------------------------ */
.fc{transform-box:fill-box;transform-origin:center}
.fl-a{animation:flA 11s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.fl-b{animation:flB 13s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.fl-c{animation:flC 15s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.orbit{animation:spinSlow 60s linear infinite;transform-box:fill-box;transform-origin:center}
.orbit-rev{animation:spinSlow 84s linear infinite reverse;transform-box:fill-box;transform-origin:center}
.dotpulse{animation:dotPulse 3.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.rot{opacity:0;animation:rot 13s cubic-bezier(.42,0,.2,1) infinite}
.rot0{opacity:1}
.mq{animation:mq 46s linear infinite;transform-box:fill-box}
.mq-rev{animation:mqRev 58s linear infinite;transform-box:fill-box}
.breath{animation:breath 7.5s ease-in-out infinite}
.aur{animation:aur 28s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.halo{animation:halo 8.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.bob{animation:bob 7.5s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.glowp{animation:glowP 8s ease-in-out infinite}
.shine{animation:shine 9s ease-in-out infinite}
.tilt{animation:tilt 14s ease-in-out infinite}
.grow{transform-box:fill-box;transform-origin:left center;animation:grow .95s cubic-bezier(.22,.61,.36,1) both}
.pop{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .55s cubic-bezier(.22,.61,.36,1) both}
.rv{opacity:0;animation:rv .75s cubic-bezier(.22,.61,.36,1) both}
.rv-s{opacity:0;animation:rvS .85s cubic-bezier(.22,.61,.36,1) both}

@keyframes flA{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@keyframes flB{0%,100%{transform:translateY(0)}50%{transform:translateY(12px)}}
@keyframes flC{0%,100%{transform:translate(0,0)}50%{transform:translate(8px,-10px)}}
@keyframes spinSlow{to{transform:rotate(360deg)}}
@keyframes dotPulse{0%,100%{opacity:.34;transform:scale(.84)}50%{opacity:1;transform:scale(1.14)}}
@keyframes rot{0%{opacity:0;transform:translateY(7px)}3%{opacity:1;transform:translateY(0)}21%{opacity:1}24%{opacity:0}100%{opacity:0}}
@keyframes mq{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes mqRev{from{transform:translateX(-50%)}to{transform:translateX(0)}}
@keyframes breath{0%,100%{opacity:.42}50%{opacity:.82}}
@keyframes aur{from{transform:translate(-1.2%,-.9%) scale(1)}to{transform:translate(1.2%,1%) scale(1.035)}}
@keyframes halo{0%,100%{opacity:.10;transform:scale(1)}50%{opacity:.20;transform:scale(1.06)}}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes glowP{0%,100%{opacity:.34}50%{opacity:.60}}
@keyframes shine{0%{opacity:.22}45%{opacity:.85}100%{opacity:.22}}
@keyframes tilt{0%,100%{transform:rotate(-4.4deg)}50%{transform:rotate(-3.5deg)}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pop{from{opacity:0;transform:translateY(4px) scale(.72)}to{opacity:1;transform:none}}
@keyframes rv{from{opacity:0;transform:translateY(11px)}to{opacity:1;transform:translateY(0)}}
@keyframes rvS{from{opacity:0;transform:translateY(7px) scale(.994)}to{opacity:1;transform:none}}

@media (prefers-reduced-motion:reduce){
  .fl-a,.fl-b,.fl-c,.orbit,.orbit-rev,.dotpulse,.mq,.mq-rev,.breath,
  .aur,.halo,.bob,.glowp,.shine,.tilt,.grow,.pop{animation:none!important}
  .rot{animation:none!important;opacity:0!important}
  .rot0{opacity:1!important}
  .rv,.rv-s,.pop{opacity:1!important;transform:none!important}
  .grow{transform:none!important}
}
"""

# ── tiny helpers ───────────────────────────────────────────────────────────
def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


_ICONS: dict[str, str] = {}

# A few marks are not in Simple Icons (or their wordmark is unreadable at 34px).
CUSTOM_PATHS = {
    "database": (
        '<path d="M12 2C7.58 2 4 3.34 4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5c0-1.66-3.58-3-8-3zm0 2c3.94 0 6 .84 6 1s-2.06 1-6 1-6-.84-6-1 2.06-1 6-1zm6 15c0 .16-2.06 1-6 1s-6-.84-6-1v-2.62c1.4.76 3.58 1.22 6 1.22s4.6-.46 6-1.22V19zm0-5c0 .16-2.06 1-6 1s-6-.84-6-1v-2.62c1.4.76 3.58 1.22 6 1.22s4.6-.46 6-1.22V14zm0-5c0 .16-2.06 1-6 1s-6-.84-6-1V6.38c1.4.76 3.58 1.22 6 1.22s4.6-.46 6-1.22V9z"/>'
    ),
}


def icon_body(name: str, folder: str = "icons") -> str:
    if folder == "icons" and name in CUSTOM_PATHS:
        return CUSTOM_PATHS[name]
    key = f"{folder}/{name}"
    if key not in _ICONS:
        raw = (SRC / folder / f"{name}.svg").read_text(encoding="utf-8")
        paths = re.findall(r"<path[^>]*/>", raw)
        _ICONS[key] = "".join(paths)
    return _ICONS[key]


def icon(name: str, x: float, y: float, size: float, fill: str = "#FFFFFF",
         opacity: float = 1.0, extra: str = "", folder: str = "icons") -> str:
    scale = size / 24.0
    return (
        f'<g transform="translate({x:g} {y:g}) scale({scale:.4f})" opacity="{opacity}" '
        f'fill="{fill}" {extra}>{icon_body(name, folder)}</g>'
    )


def txt(x: float, y: float, s: str, size: float = 18, fill: str = INK,
        weight: int = 400, ls: float = 0, anchor: str = "start",
        family: str = FONT, opacity: float = 1, cls: str = "",
        style: str = "") -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size:g}" '
        f'font-weight="{weight}" fill="{fill}" letter-spacing="{ls:g}" '
        f'text-anchor="{anchor}" opacity="{opacity}" class="{cls}" style="{style}">{esc(s)}</text>'
    )


def rrect(x, y, w, h, r, fill="none", stroke="none", sw=1, opacity=1, extra=""):
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}" opacity="{opacity}" {extra}/>'
    )


def line(x1, y1, x2, y2, stroke, sw=1, opacity=1, extra=""):
    return (
        f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" '
        f'stroke-width="{sw:g}" opacity="{opacity}" {extra}/>'
    )


class Doc:
    """Small SVG document builder with shared defs and a specular-card helper."""

    def __init__(self, w: int, h: int, seed: str = "lg", radius: int = 36):
        self.w, self.h, self.seed, self.radius = w, h, seed, radius
        self.defs: list[str] = []
        self.body: list[str] = []
        self._n = 0
        self._install_defs()

    # -- plumbing ---------------------------------------------------------
    def uid(self, prefix="u"):
        self._n += 1
        return f"{prefix}{self._n}"

    def d(self, markup):
        self.defs.append(markup)

    def add(self, markup):
        self.body.append(markup)

    def _install_defs(self):
        self.d("""
<linearGradient id="glass" x1="0" y1="0" x2="0.35" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".105"/>
  <stop offset=".48" stop-color="#FFFFFF" stop-opacity=".045"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity=".018"/>
</linearGradient>
<linearGradient id="rim" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".62"/>
  <stop offset=".28" stop-color="#BBD7FF" stop-opacity=".18"/>
  <stop offset=".62" stop-color="#FFFFFF" stop-opacity=".07"/>
  <stop offset="1" stop-color="#7DD3FC" stop-opacity=".34"/>
</linearGradient>
<linearGradient id="rimSoft" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".28"/>
  <stop offset=".5" stop-color="#FFFFFF" stop-opacity=".04"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity=".18"/>
</linearGradient>
<linearGradient id="topLine" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".18" stop-color="#FFFFFF" stop-opacity=".55"/>
  <stop offset=".5" stop-color="#FFFFFF" stop-opacity=".9"/>
  <stop offset=".82" stop-color="#FFFFFF" stop-opacity=".55"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".42" stop-color="#FFFFFF" stop-opacity=".16"/>
  <stop offset=".5" stop-color="#E4F1FF" stop-opacity=".34"/>
  <stop offset=".58" stop-color="#FFFFFF" stop-opacity=".14"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FFFFFF"/>
  <stop offset=".34" stop-color="#E8F2FF"/>
  <stop offset=".62" stop-color="#A9CBFF"/>
  <stop offset="1" stop-color="#C9B8FF"/>
  <animate attributeName="x1" values="-0.2;0.4;-0.2" dur="12s" repeatCount="indefinite"/>
  <animate attributeName="x2" values="0.8;1.4;0.8" dur="12s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="gridStroke" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#D6E6FF" stop-opacity=".10"/>
  <stop offset="1" stop-color="#8FB4FF" stop-opacity=".02"/>
</linearGradient>
<radialGradient id="vignette" cx=".5" cy=".34" r=".92">
  <stop offset=".42" stop-color="#000000" stop-opacity="0"/>
  <stop offset="1" stop-color="#000000" stop-opacity=".58"/>
</radialGradient>
<radialGradient id="glowWhite" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".85"/>
  <stop offset=".35" stop-color="#CFE6FF" stop-opacity=".28"/>
  <stop offset="1" stop-color="#CFE6FF" stop-opacity="0"/>
</radialGradient>
<filter id="grain" x="-10%" y="-10%" width="120%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/>
  <feColorMatrix type="saturate" values="0"/>
</filter>
<filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
  <feGaussianBlur stdDeviation="14" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
""")

    # -- reusable shapes --------------------------------------------------
    def orb(self, cx, cy, rx, color, opacity=.55, blur=.0):
        gid = self.uid("og")
        self.d(f"""
<radialGradient id="{gid}" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{color}" stop-opacity="{opacity:.3f}"/>
  <stop offset=".45" stop-color="{color}" stop-opacity="{opacity * .38:.3f}"/>
  <stop offset="1" stop-color="{color}" stop-opacity="0"/>
</radialGradient>""")
        return f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{rx * .82:g}" fill="url(#{gid})"/>'

    def background(self, orbs, grid=True, grain=True):
        w, h, r = self.w, self.h, self.radius
        self.add(f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#bgGrad)"/>')
        for o in orbs:
            self.add(f'<g class="{o[5] if len(o) > 5 else ""}">{self.orb(*o[:4], opacity=o[4] if len(o) > 4 else .5)}</g>')
        if grid:
            self.add(f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#grid)" mask="url(#gridMask)" opacity=".9"/>')
        self.add(f'<rect width="{w}" height="{h}" rx="{r}" fill="url(#vignette)"/>')
        if grain:
            self.add(f'<rect width="{w}" height="{h}" rx="{r}" filter="url(#grain)" opacity=".035"/>')
        self.add(rrect(0.6, 0.6, w - 1.2, h - 1.2, r - .6, stroke="url(#rimSoft)", sw=1.2))

    def panel(self, x, y, w, h, r=28, tint=None, sweep=False, rim=True,
              opacity=1.0, extra=""):
        gid = self.uid("clip")
        self.d(f'<clipPath id="{gid}"><rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}"/></clipPath>')
        out = [rrect(x, y, w, h, r, fill="url(#glass)", opacity=opacity, extra=extra)]
        if tint:
            out.append(rrect(x, y, w, h, r, fill=tint, opacity=.55))
        if rim:
            out.append(rrect(x + .3, y + .3, w - .6, h - .6, r, stroke="url(#rim)", sw=1.1))
            out.append(f'<path d="M {x + r:g} {y + 1.1:g} H {x + w - r:g}" stroke="url(#topLine)" stroke-width="1.2" opacity=".7"/>')
        if sweep:
            out.append(self.sweep(x, y, w, h, gid))
        return "".join(out)

    def sweep(self, x, y, w, h, clip_id, dur=9, delay=0):
        bw = max(90, w * .16)
        return (
            f'<g clip-path="url(#{clip_id})"><rect x="{x - bw:g}" y="{y - 40:g}" width="{bw:g}" '
            f'height="{h + 80:g}" fill="url(#sheen)" opacity=".55">'
            f'<animate attributeName="x" from="{x - bw:g}" to="{x + w + bw:g}" '
            f'dur="{dur}s" begin="{delay}s" repeatCount="indefinite"/></rect></g>'
        )

    @staticmethod
    def rv(markup: str, delay: float = 0.0, cls: str = "rv") -> str:
        """Wrap a fragment in a staggered entrance (fade + 11px rise)."""
        return f'<g class="{cls}" style="animation-delay:{delay:.2f}s">{markup}</g>'

    def render(self) -> str:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" fill="none" role="img">'
            f'<defs>{"".join(self.defs)}</defs>'
            f'<style>{BASE_CSS}</style>'
            f'{"".join(self.body)}</svg>'
        )

    def save(self, name: str):
        (A / name).write_text(self.render(), encoding="utf-8")
        print(f"  · {name:28s} {(A / name).stat().st_size / 1024:6.1f} KB")


# ── shared fragments ───────────────────────────────────────────────────────
def setup_canvas(doc: Doc, orbs, grid=True):
    doc.d(f"""
<linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#05080F"/>
  <stop offset=".42" stop-color="#080D1A"/>
  <stop offset=".74" stop-color="#0A1020"/>
  <stop offset="1" stop-color="#05080F"/>
</linearGradient>
<pattern id="grid" width="56" height="56" patternUnits="userSpaceOnUse">
  <path d="M56 0H0V56" fill="none" stroke="url(#gridStroke)" stroke-width="1"/>
</pattern>
<radialGradient id="gridMaskGrad" cx=".5" cy=".45" r=".62">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/>
  <stop offset=".7" stop-color="#FFFFFF" stop-opacity=".35"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</radialGradient>
<mask id="gridMask"><rect width="{doc.w}" height="{doc.h}" fill="url(#gridMaskGrad)"/></mask>
""")
    doc.background(orbs, grid=grid)


def pill(doc: Doc, x, y, w, h, label, icon_name=None, accent=BLUE, size=15,
         text_color=INK, glass=True, dot=False, mono=False):
    out = []
    out.append(doc.panel(x, y, w, h, h / 2, tint=f"{accent}22", sweep=False) if glass else
               rrect(x, y, w, h, h / 2, fill=f"{accent}18", stroke=f"{accent}55"))
    lx = x + 18
    if dot:
        out.append(f'<circle cx="{x + 18:g}" cy="{y + h / 2:g}" r="4" fill="{accent}" class="dotpulse"/>')
        lx = x + 32
    if icon_name:
        out.append(icon(icon_name, lx, y + h / 2 - size * .72, size * 1.44, fill=accent))
        lx += size * 1.44 + 10
    fam = MONO if mono else FONT
    out.append(txt(lx, y + h / 2 + size * .36, label, size=size, fill=text_color,
                   weight=600, family=fam, ls=.4))
    return "".join(out)


def stat(doc: Doc, x, y, value, label, accent=BLUE, align="start", width=170):
    anchor = align
    out = [txt(x, y, value, size=30, fill=INK, weight=700,
               anchor=anchor, family=FONT)]
    out.append(txt(x, y + 24, label, size=11.5, fill=DIM, weight=600,
                   ls=2.2, anchor=anchor))
    out.append(f'<circle cx="{x + (0 if align == "start" else width / 2):g}" cy="{y - 44:g}" r="2" fill="{accent}" opacity=".9"/>')
    return "".join(out)


def chat_bubble(doc: Doc, x, y, w, h, r=18, accent=BLUE):
    """Tiny glass glyph used as an accent ornament."""
    return (
        doc.panel(x, y, w, h, r, tint=f"{accent}18", sweep=False) +
        f'<path d="M {x + 16:g} {y + h * .32:g} H {x + w - 16:g}" stroke="{accent}" stroke-opacity=".55" stroke-width="2"/>'
        f'<path d="M {x + 16:g} {y + h * .52:g} H {x + w - 30:g}" stroke="#FFFFFF" stroke-opacity=".22" stroke-width="2"/>'
        f'<path d="M {x + 16:g} {y + h * .72:g} H {x + w - 46:g}" stroke="#FFFFFF" stroke-opacity=".14" stroke-width="2"/>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# 01 · HERO — desktop
# ═══════════════════════════════════════════════════════════════════════════
def build_hero():
    d = Doc(1200, 640, "hero")
    setup_canvas(d, [
        (150, 40, 430, "#2563EB", .62, "fl-a"),
        (1055, 30, 470, "#7C3AED", .52, "fl-b"),
        (990, 650, 440, "#0891B2", .46, "fl-c"),
        (170, 690, 380, "#DB2777", .24, "fl-a"),
    ])

    # ambient wash that drifts on its own clock
    d.add(f'<g class="aur" opacity=".55">{d.orb(620, 250, 560, "#1D4ED8", .16)}</g>')
    d.add(f'<g class="aur" opacity=".45" style="animation-delay:-9s">{d.orb(300, 520, 460, "#7C3AED", .12)}</g>')

    # — top bar ————————————————————————————————————————————————
    d.add(d.rv(
        pill(d, 64, 40, 256, 42, "OPEN TO COLLABORATE", accent=MINT, size=12.5, dot=True),
        .04))
    d.add(d.rv(
        txt(1136, 66, "TANGERANG · INDONESIA · UTC+7", size=11.5, fill=DIM,
            weight=600, ls=2.4, anchor="end", family=MONO) +
        f'<circle cx="1124" cy="84" r="2.4" fill="{MINT}" class="dotpulse"/>',
        .10))

    # — identity ———————————————————————————————————————————————
    d.add(d.rv(
        txt(66, 148, "PORTFOLIO  /  2026", size=12.5, fill=CYAN, weight=700, ls=6) +
        line(66, 166, 150, 166, CYAN, 1.2, .35),
        .14))
    d.add(d.rv(
        txt(62, 238, "RIFKILLAH", size=88, weight=800, fill="url(#nameGrad)", ls=-1.6),
        .20))
    d.add(d.rv(
        txt(66, 292, "MULIYA AL-FARIS", size=31, weight=600, fill="#D8E7FF",
            ls=8.6, opacity=.8),
        .28))

    # role rotator
    rotator = [txt(66, 354, "I craft", size=23, fill=MUTED, weight=400, ls=-.2)]
    words = [("interfaces.", BLUE), ("systems.", CYAN), ("stories.", VIOLET), ("experiences.", MINT)]
    for i, (word, color) in enumerate(words):
        rotator.append(txt(152, 354, word, size=23, fill=color, weight=600,
                           cls="rot rot0" if i == 0 else "rot",
                           style=f"animation-delay:{i * 3.25:.2f}s"))
    d.add(d.rv("".join(rotator), .36))

    d.add(d.rv(
        txt(66, 404, "From spinning fan blades at six to interfaces that refract light.", size=17.5, fill=MUTED) +
        txt(66, 430, "Curiosity, compiled into things people can actually use.", size=17.5, fill=MUTED),
        .44))

    # hairline with a slow travelling glint
    d.add(line(66, 470, 700, 470, "#FFFFFF", 1, .10))
    d.add('<g opacity=".55"><rect x="66" y="469" width="150" height="2" fill="url(#sheen)">'
          '<animate attributeName="x" values="66;550;66" dur="9s" repeatCount="indefinite"/></rect></g>')

    # chips
    chips = [
        (66, 158, "UI/UX DESIGN", BLUE),
        (234, 150, "ANDROID ROM", MINT),
        (394, 142, "MULTIMEDIA", VIOLET),
        (546, 122, "WEB DEV", CYAN),
    ]
    for i, (x, w, label, color) in enumerate(chips):
        d.add(d.rv(
            d.panel(x, 498, w, 42, 21, tint=f"{color}18", sweep=False) +
            f'<circle cx="{x + 20:g}" cy="519" r="3.2" fill="{color}"/>' +
            txt(x + 34, 524, label, size=12, fill="#E7F0FF", weight=600, ls=1.1),
            .56 + i * .055))

    # stats
    for i, (x, value, label, color) in enumerate([
        (66, "13", "PUBLIC REPOSITORIES", BLUE),
        (276, "3+", "YEARS ANDROID INTERNALS", MINT),
        (500, "2023", "INFORMATIKA · UNPAM", VIOLET),
    ]):
        d.add(d.rv(
            txt(x, 596, value, size=30, weight=700, fill=INK) +
            txt(x, 618, label, size=10.5, fill=DIM, weight=600, ls=2.1),
            .74 + i * .06))

    # — portrait ————————————————————————————————————————————————
    cx, cy, r = 950, 296, 146
    port = []
    port.append(f'<circle cx="{cx}" cy="{cy}" r="238" fill="url(#glowWhite)" class="halo"/>')
    port.append(f'<ellipse cx="{cx}" cy="{cy}" rx="196" ry="196" stroke="#BFD9FF" stroke-opacity=".16" stroke-width="1" stroke-dasharray="2 9" class="orbit-rev"/>')
    port.append(f'<ellipse cx="{cx}" cy="{cy}" rx="226" ry="226" stroke="#9CC4FF" stroke-opacity=".10" stroke-width="1" stroke-dasharray="1 14" class="orbit"/>')
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 13}" fill="none" stroke="url(#rimSoft)" stroke-width="1"/>')

    cid = "avatarClip"
    d.d(f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    av = b64(SRC / "avatar.png")
    port.append(f'<image x="{cx - r}" y="{cy - r}" width="{r * 2}" height="{r * 2}" href="data:image/png;base64,{av}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>')
    d.d("""
<linearGradient id="avatarTone" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#3B82F6" stop-opacity=".30"/>
  <stop offset=".55" stop-color="#0EA5E9" stop-opacity=".06"/>
  <stop offset="1" stop-color="#8B5CF6" stop-opacity=".32"/>
</linearGradient>""")
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#avatarTone)" clip-path="url(#{cid})" style="mix-blend-mode:overlay"/>')
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#rim)" stroke-width="4.5"/>')
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 8}" fill="none" stroke="#FFFFFF" stroke-opacity=".14" stroke-width="1"/>')
    d.add(d.rv("".join(port), .16, "rv-s"))

    # sparkle badge (stays alive without drawing attention)
    d.add(d.rv(
        f'<g class="bob" style="animation-delay:1.2s">'
        f'<circle cx="{cx + r - 8}" cy="{cy + r - 18}" r="26" fill="#0A1120" stroke="url(#rim)" stroke-width="1.2"/>'
        + txt(cx + r - 8, cy + r - 9, "✦", size=19, fill=MINT, anchor="middle") +
        '</g>', .34))

    # floating stack chips
    floats = [
        (735, 118, 148, "Kotlin", "kotlin", VIOLET, "fl-a", "0s"),
        (1032, 156, 116, "Figma", "figma", ROSE, "fl-b", "1.4s"),
        (1050, 424, 126, "Laravel", "laravel", ROSE, "fl-c", ".6s"),
        (742, 430, 150, "Android", "android", MINT, "fl-a", "2.1s"),
    ]
    for i, (x, y, w, label, ic, color, cls, delay) in enumerate(floats):
        inner = (
            d.panel(x, y, w, 46, 15, tint=f"{color}14", sweep=False) +
            icon(ic, x + 14, y + 13, 20, fill=color) +
            txt(x + 44, y + 29, label, size=13.5, fill="#E9F2FF", weight=600)
        )
        d.add(f'<g class="{cls}" style="animation-delay:{delay}">'
              f'<g class="rv" style="animation-delay:{.5 + i * .08:.2f}s">{inner}</g></g>')

    # — light ornament ————————————————————————————————————————————
    d.d("""
<linearGradient id="cornerLight" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#BFDBFE" stop-opacity=".55"/>
  <stop offset=".6" stop-color="#7DD3FC" stop-opacity=".06"/>
  <stop offset="1" stop-color="#7DD3FC" stop-opacity="0"/>
</linearGradient>""")
    d.add('<path d="M 0 0 H 420 L 250 640 H 0 Z" fill="url(#cornerLight)" opacity=".22"/>')

    # one slow specular pass, far apart, low contrast
    d.d('<clipPath id="heroClip"><rect width="1200" height="640" rx="36"/></clipPath>')
    d.add('<g clip-path="url(#heroClip)" opacity=".30"><rect x="-220" y="-40" width="210" height="720" '
          'fill="url(#sheen)"><animate attributeName="x" values="-220;1220;-220" dur="26s" '
          'begin="4s" repeatCount="indefinite"/></rect></g>')

    d.save("hero.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 01b · HERO — mobile / iPhone
# ═══════════════════════════════════════════════════════════════════════════
def build_hero_mobile():
    d = Doc(480, 756, "herom", radius=30)
    setup_canvas(d, [
        (60, 10, 210, "#2563EB", .66, "fl-a"),
        (450, 120, 230, "#7C3AED", .52, "fl-b"),
        (430, 740, 210, "#0891B2", .42, "fl-c"),
        (20, 720, 190, "#DB2777", .22, "fl-a"),
    ])

    d.d("""
<linearGradient id="avatarTone" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#3B82F6" stop-opacity=".30"/>
  <stop offset=".55" stop-color="#0EA5E9" stop-opacity=".06"/>
  <stop offset="1" stop-color="#8B5CF6" stop-opacity=".32"/>
</linearGradient>""")

    d.add(d.rv(pill(d, 114, 34, 252, 40, "OPEN TO COLLABORATE", accent=MINT, size=11.5, dot=True), .04))

    cx, cy, r = 240, 194, 90
    port = [f'<circle cx="{cx}" cy="{cy}" r="150" fill="url(#glowWhite)" class="halo"/>',
            f'<ellipse cx="{cx}" cy="{cy}" rx="120" ry="120" stroke="#BFD9FF" stroke-opacity=".16" stroke-width="1" stroke-dasharray="2 8" class="orbit-rev"/>',
            f'<ellipse cx="{cx}" cy="{cy}" rx="140" ry="140" stroke="#9CC4FF" stroke-opacity=".10" stroke-width="1" stroke-dasharray="1 12" class="orbit"/>']

    cid = "avm"
    d.d(f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    port.append(f'<image x="{cx - r}" y="{cy - r}" width="{r * 2}" height="{r * 2}" href="data:image/png;base64,{b64(SRC / "avatar.png")}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>')
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#avatarTone)" clip-path="url(#{cid})" style="mix-blend-mode:overlay"/>')
    port.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#rim)" stroke-width="3.5"/>')
    d.add(d.rv("".join(port), .12, "rv-s"))

    d.add(d.rv(
        txt(240, 340, "RIFKILLAH", size=44, weight=800, fill="url(#nameGrad)",
            anchor="middle", ls=-.8) +
        txt(240, 370, "MULIYA AL-FARIS", size=15, weight=600, fill="#D8E7FF",
            anchor="middle", ls=4.4, opacity=.8),
        .22))

    phrases = [("I craft interfaces.", BLUE), ("I craft systems.", CYAN),
               ("I craft stories.", VIOLET), ("I craft experiences.", MINT)]
    rotator = []
    for i, (phrase, color) in enumerate(phrases):
        rotator.append(txt(240, 414, phrase, size=18, fill=color, weight=600, anchor="middle",
                           cls="rot rot0" if i == 0 else "rot",
                           style=f"animation-delay:{i * 3.25:.2f}s"))
    d.add(d.rv("".join(rotator), .30))

    d.add(d.rv(
        txt(240, 450, "From fan blades to Liquid Glass.", size=13, fill=MUTED,
            anchor="middle"),
        .38))
    d.add(line(64, 482, 416, 482, "#FFFFFF", 1, .10))
    d.add('<g opacity=".5"><rect x="64" y="481" width="110" height="2" fill="url(#sheen)">'
          '<animate attributeName="x" values="64;300;64" dur="9s" repeatCount="indefinite"/></rect></g>')

    # chips, two centred rows
    rows = [
        [(117, 96, "UI/UX", BLUE), (225, 138, "ANDROID ROM", MINT)],
        [(117, 128, "MULTIMEDIA", VIOLET), (257, 106, "WEB DEV", CYAN)],
    ]
    n = 0
    for row_i, row in enumerate(rows):
        y = 504 + row_i * 52
        for x, w, label, color in row:
            d.add(d.rv(
                d.panel(x, y, w, 40, 20, tint=f"{color}18", sweep=False) +
                f'<circle cx="{x + 18:g}" cy="{y + 20:g}" r="3" fill="{color}"/>' +
                txt(x + 31, y + 25, label, size=10.5, fill="#E7F0FF", weight=600, ls=.9),
                .46 + n * .06))
            n += 1

    d.add(line(64, 628, 416, 628, "#FFFFFF", 1, .10))

    for i, (x, value, label, color) in enumerate([
        (120, "13", "REPOS", BLUE),
        (240, "3+", "YRS ANDROID", MINT),
        (360, "2023", "UNPAM", VIOLET),
    ]):
        d.add(d.rv(
            txt(x, 674, value, size=24, weight=700, fill=INK, anchor="middle") +
            txt(x, 694, label, size=8.5, fill=DIM, weight=600, ls=1.6, anchor="middle"),
            .68 + i * .06))

    d.add(d.rv(
        txt(240, 736, "TANGERANG · INDONESIA · UTC+7", size=8.5, fill=DIM,
            anchor="middle", ls=1.6, family=MONO),
        .86))
    d.save("hero-mobile.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 02 · SECTION HEADERS
# ═══════════════════════════════════════════════════════════════════════════
def build_section(slug, index, title, subtitle, accent, filename):
    d = Doc(1200, 132, f"sec-{slug}", radius=28)
    setup_canvas(d, [
        (1000, -40, 300, accent, .18, "fl-b"),
        (80, 150, 240, accent, .10, "fl-a"),
    ])
    d.add(d.panel(0, 0, 1200, 132, 28, sweep=True))
    # accent spine
    d.d(f"""
<linearGradient id="spine" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{accent}" stop-opacity="0"/>
  <stop offset=".25" stop-color="{accent}" stop-opacity=".95"/>
  <stop offset=".75" stop-color="{accent}" stop-opacity=".65"/>
  <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
</linearGradient>""")
    d.add('<rect x="38" y="34" width="2.5" height="64" rx="1.2" fill="url(#spine)" class="glowp"/>')
    # a pulse of light runs down the spine, like a signal indicator
    d.d('<clipPath id="spineClip"><rect x="38" y="34" width="2.5" height="64" rx="1.2"/></clipPath>')
    d.add('<g clip-path="url(#spineClip)"><rect x="37" y="34" width="5" height="16" rx="2" '
          'fill="#FFFFFF">'
          '<animate attributeName="y" values="34;94;34" dur="5.2s" repeatCount="indefinite"/>'
          '<animate attributeName="opacity" values="0;.85;.85;0" keyTimes="0;.16;.84;1" '
          'dur="5.2s" repeatCount="indefinite"/></rect></g>')

    d.add(d.rv(txt(62, 74, title, size=35, weight=800, fill=INK, ls=-.4), .05))
    d.add(d.rv(txt(63, 100, subtitle, size=10.5, fill=DIM, weight=600, ls=3.1), .13))
    d.add(d.rv(txt(1160, 106, index, size=84, weight=800, fill="#FFFFFF",
                   anchor="end", opacity=.055, ls=-2), .08))
    d.add(d.rv(
        f'<circle cx="1104" cy="36" r="3.4" fill="{accent}" class="dotpulse"/>' +
        txt(1090, 41, "LIQUID GLASS / 2026", size=8.5, fill=DIM, weight=600,
            ls=1.8, anchor="end", family=MONO),
        .18))
    d.save(filename)


def build_sections():
    build_section("about", "01", "About", "WHO I AM  ·  WHAT I DO  ·  WHERE I'M GOING", BLUE, "sec-about.svg")
    build_section("experience", "02", "Experience", "CONTENT  ·  SOCIAL  ·  WEB  ·  PUBLIC SERVICE", CYAN, "sec-experience.svg")
    build_section("journey", "03", "Journey", "FAN BLADES  →  RANGE CIRCUITS  →  LIQUID GLASS", VIOLET, "sec-journey.svg")
    build_section("stack", "04", "Stack", "TOOLS I THINK WITH EVERY SINGLE DAY", CYAN, "sec-stack.svg")
    build_section("work", "05", "Work", "SELECTED REPOSITORIES  ·  REAL SHIPPED CODE", MINT, "sec-work.svg")
    build_section("lab", "06", "GitHub Lab", "SIGNALS  ·  STREAKS  ·  CONTRIBUTION WEATHER", ROSE, "sec-lab.svg")
    build_section("beyond", "07", "Beyond Code", "THE HOBBIES THAT KEEP THE CURIOSITY ALIVE", AMBER, "sec-beyond.svg")
    build_section("connect", "08", "Connect", "ONE MESSAGE AWAY  ·  COLLABORATION WELCOME", BLUE, "sec-connect.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 03 · KEYWORD MARQUEE
# ═══════════════════════════════════════════════════════════════════════════
def build_marquee():
    d = Doc(1200, 92, "marquee", radius=24)
    setup_canvas(d, [
        (120, 46, 260, "#2563EB", .18, "fl-a"),
        (1080, 46, 260, "#7C3AED", .16, "fl-b"),
    ])
    d.d("""
<linearGradient id="edgeFade" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".07" stop-color="#FFFFFF" stop-opacity="1"/>
  <stop offset=".93" stop-color="#FFFFFF" stop-opacity="1"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<mask id="edgeMask"><rect width="1200" height="92" fill="url(#edgeFade)"/></mask>""")
    d.add(d.rv(d.panel(0, 0, 1200, 92, 24, sweep=False), .02, "rv-s"))

    items = [
        ("UI/UX DESIGN", BLUE),
        ("ANDROID CUSTOM ROM", MINT),
        ("MULTIMEDIA", VIOLET),
        ("WEB DEVELOPMENT", CYAN),
        ("PHOTOGRAPHY", ROSE),
        ("SHORT FILM", AMBER),
        ("URBAN FARMING", MINT),
        ("LIQUID GLASS", BLUE),
    ]
    half = []
    for label, color in items:
        half.append(f'<tspan fill="{color}" font-weight="700">{esc(label)}</tspan>')
        half.append('<tspan fill="#4B5D77" font-weight="400">   ✦   </tspan>')
    half = "".join(half)
    body = half + half
    d.add(f'<g mask="url(#edgeMask)"><g class="mq" style="animation-duration:56s">'
          f'<text x="0" y="55" font-family="{FONT}" font-size="14.5" letter-spacing="4.2" '
          f'fill="{MUTED}">{body}</text></g></g>')
    d.add(txt(24, 30, "WHAT I DO", size=8, fill=DIM, weight=700, ls=2.2, family=MONO, opacity=.0))
    d.save("marquee.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 04 · TECH STACK RAILS
# ═══════════════════════════════════════════════════════════════════════════
STACK_ROWS = [
    [
        ("HTML5", "html5", "#FB923C"), ("CSS3", "css", "#60A5FA"),
        ("JavaScript", "javascript", "#FACC15"), ("TypeScript", "typescript", "#60A5FA"),
        ("Java", "openjdk", "#FB7185"), ("Python", "python", "#60A5FA"),
        ("C++", "cplusplus", "#93C5FD"), ("PHP", "php", "#A5B4FC"),
        ("Laravel", "laravel", "#FDA4AF"), ("Kotlin", "kotlin", "#A78BFA"),
    ],
    [
        ("Android", "android", "#6EE7B7"), ("Figma", "figma", "#FDA4AF"),
        ("Photoshop", "adobephotoshop", "#7DD3FC"), ("Premiere Pro", "adobepremierepro", "#C4B5FD"),
        ("After Effects", "adobeaftereffects", "#C4B5FD"), ("Illustrator", "adobeillustrator", "#FCD34D"),
        ("Git", "git", "#FB923C"), ("GitHub", "github", "#E2E8F0"),
        ("Linux", "linux", "#FCD34D"), ("Docker", "docker", "#60A5FA"),
    ],
    [
        ("MySQL", "database", "#7DD3FC"), ("Tailwind", "tailwindcss", "#67E8F9"),
        ("React", "react", "#67E8F9"), ("Next.js", "nextdotjs", "#E2E8F0"),
        ("Node.js", "nodedotjs", "#6EE7B7"), ("VS Code", "visualstudiocode", "#60A5FA"),
        ("Android Studio", "androidstudio", "#6EE7B7"), ("Blender", "blender", "#FB923C"),
        ("Firebase", "firebase", "#FCD34D"), ("Vercel", "vercel", "#E2E8F0"),
    ],
]


def _stack_tile(d, x, y, size, label, ic, color):
    out = [d.panel(x, y, size, size, 24, tint=f"{color}10", sweep=False)]
    out.append(icon(ic, x + size / 2 - 17, y + 19, 34, fill=color))
    out.append(txt(x + size / 2, y + size - 15, label, size=9, fill="#D8E5F6",
                   anchor="middle", weight=600, ls=.2))
    return "".join(out)


def build_stack():
    d = Doc(1200, 436, "stack", radius=32)
    setup_canvas(d, [
        (120, 40, 330, "#0891B2", .38, "fl-a"),
        (1060, 400, 360, "#7C3AED", .34, "fl-b"),
    ])
    d.add(d.rv(d.panel(0, 0, 1200, 436, 32, sweep=False), .02, "rv-s"))
    d.d("""
<linearGradient id="edgeFadeV" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".055" stop-color="#FFFFFF" stop-opacity="1"/>
  <stop offset=".945" stop-color="#FFFFFF" stop-opacity="1"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>
<mask id="edgeMaskV"><rect width="1200" height="436" fill="url(#edgeFadeV)"/></mask>""")

    tile, step, width = 96, 118, 1180
    ys = [34, 162, 290]
    speeds = [50, 63, 56]
    for r, row in enumerate(STACK_ROWS):
        seq = "".join(_stack_tile(d, i * step, ys[r], tile, *row[i]) for i in range(len(row)))
        twin = f'<g transform="translate({width} 0)">{seq}</g>'
        cls = "mq" if r % 2 == 0 else "mq-rev"
        delay = f"-{r * 6}s"
        d.add(f'<g mask="url(#edgeMaskV)"><g class="{cls}" style="animation-delay:{delay};'
              f'animation-duration:{speeds[r]}s">{seq}{twin}</g></g>')

    # a single slow light pass across the whole rail
    d.d('<clipPath id="stackClip"><rect width="1200" height="436" rx="32"/></clipPath>')
    d.add('<g clip-path="url(#stackClip)" opacity=".28"><rect x="-240" y="0" width="220" height="436" '
          'fill="url(#sheen)"><animate attributeName="x" values="-240;1240;-240" dur="18s" '
          'begin="3s" repeatCount="indefinite"/></rect></g>')

    # top + bottom hairlines for a machined edge
    d.add(line(24, 0.8, 1176, 0.8, "url(#topLine)", 1.2, .5))
    d.save("stack.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 05 · FEATURED PROJECT — Matfess
# ═══════════════════════════════════════════════════════════════════════════
def build_featured():
    d = Doc(1200, 560, "matfess", radius=34)
    setup_canvas(d, [
        (120, 80, 380, "#059669", .30, "fl-a"),
        (1080, 80, 400, "#7C3AED", .30, "fl-b"),
        (760, 560, 380, "#0891B2", .22, "fl-c"),
    ])
    d.add(d.rv(d.panel(0, 0, 1200, 560, 34, sweep=True), .02, "rv-s"))

    d.add(d.rv(txt(64, 92, "FEATURED CASE STUDY  ·  2026", size=11.5, fill=MINT, weight=700, ls=3.4, family=MONO), .08))
    d.add(d.rv(txt(61, 176, "Matfess", size=70, weight=800, fill="url(#nameGrad)", ls=-1.2), .14))
    d.add(d.rv(txt(64, 214, "A Liquid Glass study companion for Android.", size=19, fill=MUTED) +
                   txt(64, 240, "Built to make campus life feel lighter.", size=19, fill=MUTED, opacity=.72), .22))

    chips = [("Kotlin", 116), ("SQLite", 108), ("Retrofit", 118), ("Liquid Glass", 150)]
    x = 64
    for i, (label, w) in enumerate(chips):
        d.add(d.rv(
            d.panel(x, 262, w, 36, 18, tint="#6EE7B715", sweep=False) +
            f'<circle cx="{x + 17:g}" cy="280" r="2.8" fill="{MINT}"/>' +
            txt(x + 28, 285, label, size=11.5, fill="#E4F0FF", weight=600),
            .30 + i * .06))
        x += w + 10

    bullets = [
        "18 screens · notes, tasks, schedule, GPA, Pomodoro",
        "Offline-first SQLite core + two REST integrations",
        "Light / dark Liquid Glass UI with spring motion",
    ]
    for i, b in enumerate(bullets):
        y = 344 + i * 36
        d.add(d.rv(
            f'<circle cx="70" cy="{y - 5:g}" r="3.4" fill="{MINT}" opacity=".9"/>' +
            txt(86, y, b, size=15.5, fill="#C6D5E8"),
            .50 + i * .07))

    # CTA
    d.add(d.rv(
        d.panel(64, 456, 292, 52, 26, tint="#6EE7B71B", sweep=True) +
        txt(88, 488, "Explore the repository", size=14.5, fill=INK, weight=600) +
        txt(330, 489, "↗", size=17, fill=MINT, anchor="end", weight=700) +
        txt(64, 538, "github.com/rifkillah/Matfess", size=10.5, fill=DIM, ls=1.2, family=MONO),
        .2))

    # phone mockup — floats and breathes, never spins
    px, py, pw, ph = 828, 38, 308, 484
    sx, sy, sw, sh = px + 17, py + 17, pw - 34, ph - 34
    cid = "screenClip"
    d.d(f'<clipPath id="{cid}"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="32"/></clipPath>')
    d.d("""
<linearGradient id="phoneGlare" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".22"/>
  <stop offset=".45" stop-color="#FFFFFF" stop-opacity=".03"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
</linearGradient>""")

    phone = []
    phone.append(f'<rect x="{px - 6}" y="{py + 10}" width="{pw}" height="{ph}" rx="48" fill="#000000" opacity=".45"/>')
    phone.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="46" fill="#0A1020" stroke="url(#rim)" stroke-width="1.6"/>')
    phone.append(f'<rect x="{px + 8}" y="{py + 8}" width="{pw - 16}" height="{ph - 16}" rx="39" fill="#05080F" stroke="#FFFFFF" stroke-opacity=".08"/>')
    phone.append(f'<image x="{sx}" y="{sy}" width="{sw}" height="{sh}" href="data:image/jpeg;base64,{b64(SRC / "matfess-card.jpg")}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>')
    phone.append(f'<path d="M {sx:g} {sy:g} H {sx + sw * .70:g} L {sx + sw * .30:g} {sy + sh:g} H {sx:g} Z" fill="url(#phoneGlare)" clip-path="url(#{cid})"/>')
    # glare that travels down the screen, like a real reflection
    phone.append(f'<g clip-path="url(#{cid})"><rect x="{sx:g}" y="{sy - 150:g}" width="{sw}" height="130" '
                 f'fill="url(#sheen)" opacity=".38">'
                 f'<animate attributeName="y" values="{sy - 150};{sy + sh};{sy - 150}" dur="9s" '
                 f'begin="2s" repeatCount="indefinite"/></rect></g>')
    phone.append(f'<rect x="{px + pw / 2 - 34:g}" y="{py + 12:g}" width="68" height="7" rx="3.5" fill="#000000" opacity=".55"/>')
    phone.append(f'<rect x="{px + pw / 2 - 18:g}" y="{py + ph - 12:g}" width="36" height="3" rx="1.5" fill="#FFFFFF" opacity=".22"/>')
    d.add(f'<g class="rv-s" style="animation-delay:.18s">'
          f'<g class="bob" style="animation-delay:.6s">'
          f'<g class="tilt" style="transform-origin:982px 280px">'
          f'{"".join(phone)}</g></g></g>')

    # floating spec chips (kept in the free gutter so they never cover the UI)
    for i, (x, y, w, label, color, cls) in enumerate([
        (684, 68, 116, "Kotlin", VIOLET, "fl-a"),
        (684, 120, 96, "SQLite", CYAN, "fl-b"),
        (684, 470, 124, "REST API", MINT, "fl-c"),
    ]):
        inner = (
            d.panel(x, y, w, 40, 13, tint=f"{color}16", sweep=False) +
            f'<circle cx="{x + 15:g}" cy="{y + 20:g}" r="2.6" fill="{color}"/>' +
            txt(x + 26, y + 25, label, size=11.5, fill="#E6EFFF", weight=600)
        )
        d.add(f'<g class="{cls}" style="animation-delay:.7s">'
              f'<g class="rv" style="animation-delay:{.4 + i * .1:.2f}s">{inner}</g></g>')

    d.save("featured-matfess.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 06 · BEYOND CODE — four glass hobby tiles
# ═══════════════════════════════════════════════════════════════════════════
STROKE_ICONS = {
    "camera": '<rect x="3" y="6.5" width="18" height="13.5" rx="3.2"/>'
              '<circle cx="12" cy="13.4" r="4.1"/>'
              '<path d="M8.4 6.5 9.6 4.2h4.8l1.2 2.3"/>',
    "leaf": '<path d="M20.2 3.8c-8.4 0-14.4 4.2-14.4 10.6a4.4 4.4 0 0 0 4.4 4.4c6.4 0 10-6.6 10-15z"/>'
            '<path d="M4 20.2c2.2-5.4 6.2-9 11.4-11.2"/>',
    "film": '<rect x="3" y="5" width="18" height="14" rx="2.4"/>'
            '<path d="M7.4 5v14M16.6 5v14M3 9.4h4.4M3 14.6h4.4M16.6 9.4H21M16.6 14.6H21"/>',
    "pen": '<path d="M12.5 20H21"/>'
           '<path d="M16.6 3.4a2.2 2.2 0 0 1 3.1 3.1L7.4 18.8 3.2 20l1.2-4.2z"/>',
}


def build_hobby_tiles():
    for name, color in [("camera", BLUE), ("leaf", MINT), ("film", VIOLET), ("pen", AMBER)]:
        d = Doc(140, 140, f"hobby-{name}", radius=36)
        setup_canvas(d, [
            (30, 10, 130, color, .40, "fl-a"),
            (120, 140, 120, color, .22, "fl-b"),
        ], grid=False)
        d.add(d.rv(d.panel(0, 0, 140, 140, 36, sweep=True), .02, "rv-s"))
        d.add(f'<circle cx="70" cy="62" r="42" fill="{color}" class="halo"/>')
        i = list(STROKE_ICONS).index(name)
        d.add(d.rv(
            f'<g class="bob" style="animation-delay:{i * .55:.2f}s">'
            f'<g transform="translate(34 34) scale(3)" stroke="{color}" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round" fill="none" opacity=".95">'
            f'{STROKE_ICONS[name]}</g></g>', .18))
        d.add(d.rv(txt(70, 122, "0" + str(i + 1), size=9,
                       fill=DIM, ls=2.4, anchor="middle", family=MONO), .32))
        d.save(f"hobby-{name}.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 07 · SOCIAL BADGES
# ═══════════════════════════════════════════════════════════════════════════
SOCIALS = [
    ("instagram", "Instagram", "#E1306C", "@rifklh.faris_"),
    ("linkedin", "LinkedIn", "#38BDF8", "in/rifkillahmaf"),
    ("github", "GitHub", "#E2E8F0", "github.com/rifkillah"),
    ("tiktok", "TikTok", "#22D3EE", "@rfklhhh_"),
    ("x", "X / Twitter", "#F8FAFC", "@Rfklh_Alfaris"),
    ("youtube", "YouTube", "#FB7185", "@rifkiiii_lahh"),
    ("pinterest", "Pinterest", "#F43F5E", "pin.it/19sbrqNYb"),
    ("threads", "Threads", "#E2E8F0", "@rifklh.faris_"),
    ("discord", "Discord", "#818CF8", "discord.gg/r2CYJydn"),
    ("brainly", "Brainly", "#34D399", "brainly.co.id/20537154"),
]


def build_socials():
    """144×52 glass chip: five per row on desktop, two per row on a phone."""
    (A / "social").mkdir(parents=True, exist_ok=True)
    W, H = 144, 52
    for idx, (slug, label, color, handle) in enumerate(SOCIALS):
        d = Doc(W, H, f"soc-{slug}", radius=14)
        d.d(f"""
<linearGradient id="socBg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#101A2C" stop-opacity=".96"/>
  <stop offset=".55" stop-color="#0A1120" stop-opacity=".96"/>
  <stop offset="1" stop-color="#0C1424" stop-opacity=".96"/>
</linearGradient>
<radialGradient id="socGlow" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{color}" stop-opacity=".30"/>
  <stop offset="1" stop-color="{color}" stop-opacity="0"/>
</radialGradient>
<clipPath id="socClip"><rect width="{W}" height="{H}" rx="14"/></clipPath>""")
        d.add(f'<rect width="{W}" height="{H}" rx="14" fill="url(#socBg)"/>')
        d.add(f'<circle cx="{W - 16}" cy="6" r="38" fill="url(#socGlow)"/>')
        # soft brand halo behind the icon plate
        d.add(f'<circle cx="21" cy="26" r="16" fill="{color}" class="halo" style="animation-delay:{idx * .45:.2f}s"/>')
        d.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="url(#rim)" stroke-width="1"/>')
        d.add(f'<path d="M 14 1.5 H {W - 14}" stroke="url(#topLine)" stroke-width="1" opacity=".5"/>')
        # icon plate
        d.add(f'<rect x="8" y="13" width="26" height="26" rx="8" fill="{color}" fill-opacity=".10" stroke="{color}" stroke-opacity=".28"/>')
        if slug == "brainly":
            d.add(txt(21, 33, "b", size=16, fill=color, weight=800, anchor="middle"))
        else:
            d.add(icon(slug, 14, 19, 13, fill=color, folder="brands"))
        d.add(txt(42, 27, label, size=12, fill="#EAF2FF", weight=600, ls=.1))
        d.add(txt(42, 40, handle, size=7, fill=DIM, weight=500, ls=.3, family=MONO))
        # light travels across the row, chip after chip
        d.add(f'<g clip-path="url(#socClip)" opacity=".45"><rect x="-70" y="-6" width="68" height="{H + 12}" '
              f'fill="url(#sheen)"><animate attributeName="x" values="-70;144;-70" dur="8s" '
              f'begin="{1.2 + idx * .35:.2f}s" repeatCount="indefinite"/></rect></g>')
        d.save(f"social/{slug}.svg")


# ═══════════════════════════════════════════════════════════════════════════
# 08 · FOOTER
# ═══════════════════════════════════════════════════════════════════════════
def build_footer():
    d = Doc(1100, 300, "footer", radius=36)
    setup_canvas(d, [
        (120, 60, 360, "#2563EB", .32, "fl-a"),
        (980, 40, 360, "#7C3AED", .32, "fl-b"),
        (550, 320, 420, "#0891B2", .22, "fl-c"),
    ], grid=False)
    d.add(d.rv(d.panel(0, 0, 1100, 300, 36, sweep=True), .02, "rv-s"))
    d.add(d.rv(
        txt(550, 78, "“", size=76, fill=BLUE, anchor="middle", opacity=.28, family="Georgia,serif"),
        .08))
    d.add(d.rv(
        txt(550, 130, "If you cannot bear the rigors of learning,", size=22, fill="#DCE8FA",
            anchor="middle", weight=500, ls=.1) +
        txt(550, 162, "you will endure the torment of foolishness.", size=22, fill="#DCE8FA",
            anchor="middle", weight=500, ls=.1),
        .16))
    d.add(d.rv(
        txt(550, 196, "—  IMAM ASH-SHAFI'I", size=9.5, fill=DIM, anchor="middle", ls=3.2, family=MONO),
        .26))
    d.add(line(120, 224, 980, 224, "#FFFFFF", 1, .10))
    d.add('<g opacity=".5"><rect x="120" y="223" width="180" height="2" fill="url(#sheen)">'
          '<animate attributeName="x" values="120;800;120" dur="10s" begin="1s" repeatCount="indefinite"/></rect></g>')
    d.add(d.rv(
        f'<circle cx="76" cy="258" r="4" fill="{MINT}" class="dotpulse"/>' +
        txt(92, 262, "THANKS FOR STOPPING BY", size=9.5, fill=MUTED, weight=600, ls=2.6, family=MONO),
        .34))
    d.add(d.rv(
        txt(550, 262, "✦", size=12, fill=BLUE, anchor="middle", opacity=".7"),
        .40))
    d.add(d.rv(
        txt(1024, 262, "github.com/rifkillah", size=9.5, fill=MUTED, weight=600,
            ls=1.4, anchor="end", family=MONO),
        .46))

    # travelling light along the top rim
    d.add('<g clip-path="url(#footerClip)"><rect x="-200" y="-30" width="120" height="80" fill="url(#sheen)" opacity=".55">'
          '<animate attributeName="x" from="-200" to="1280" dur="12s" repeatCount="indefinite"/></rect></g>')
    d.d('<clipPath id="footerClip"><rect width="1100" height="300" rx="36"/></clipPath>')
    d.save("footer.svg")


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Building Liquid Glass assets…")
    build_hero()
    build_hero_mobile()
    build_sections()
    build_marquee()
    build_stack()
    build_featured()
    build_hobby_tiles()
    build_socials()
    build_footer()
    print(f"done · {len(list(A.rglob('*.svg')))} svg files in assets/")
