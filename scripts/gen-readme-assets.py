#!/usr/bin/env python3
"""Generate the README visuals for dsh-lc-doc-check.

Outputs (idempotent overwrite):
  docs/assets/dsh-lc-doc-check-hero-{zh,en}-{light,dark}.webp
      1440x576 hero drawn with Pillow. Left column: kicker, two-line title,
      two value lines, one subtitle, one meta line, footer. The right column
      is this repository's own figure: one row of the presentation checklist
      (the quickstart row 1, whose docType / requirement cells are empty), the
      two date comparisons that share the header's expiryAt (the quickstart
      values 2026-03-20 and 2026-03-15 against 2026-04-10), and the real run
      counts 0 error / 1 warn / 2 skipped with the two skipped reasons.
  docs/assets/dsh-lc-doc-check-flow-v5-{light,dark}.svg
      1100x660 hand-written SVG. Grammar: three reading-scope swimlanes, not
      five boxes in a row. Lane A is the credit header (lcNo, beneficiary,
      currency, expiryAt; LC-006 and LC-007); lane B is the per-row pass
      (docType, requirement, presented, discrepancy; LC-001, LC-002, LC-005)
      and the two date comparisons that share expiryAt (LC-003, LC-004);
      lane C is the cross-row pass (LC-008 unique docType). The right column
      is the two-outlet report: issues[] (the real LC-001 finding at row 1 /
      docType) and skipped[] (the real LC-005 and LC-008 reasons). Differences
      that do not fire leave no entry; an empty issues[] is not a pass.

Design parameters
-----------------
* GitHub renders the 1440px hero at ~880px. Title 82px, subtitle 25px, meta
  20px, so displayed sizes stay above 48 / 15 / 12px. The 1100px SVG is
  checked at native size in headless Chrome; node text is >=13px and every
  annotation >=11px. No string is drawn before it is measured: an overflow
  raises instead of being clipped.
* Palette: light #f9f6fd -> #e4eaf8, dark #131a2a -> #0c1016; family accent
  #4B67B4 (dark #8496f5); radius 18-22; soft shadows.
* Fonts: msyh.ttc / msyhbd.ttc / consola.ttf.
* Nothing is invented: the empty cells, dates, finding, skip reasons and
  counts are the real output of lib/index.mjs on
  samples/quickstart/input/LC-001-unsafe.json (checked 2026-11-06).

Run once:  python scripts/gen-readme-assets.py
Requires:  Python 3.10+, Pillow, and the Windows fonts above.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")
os.makedirs(OUT, exist_ok=True)

FONT_CJK = r"C:\Windows\Fonts\msyh.ttc"
FONT_CJK_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"

for _path in (FONT_CJK, FONT_CJK_BOLD, FONT_MONO):
    if not os.path.exists(_path):
        raise SystemExit(f"FATAL: font missing: {_path}")

NAME = "dsh-lc-doc-check"
HERO_W, HERO_H = 1440, 576
FLOW_W, FLOW_H = 1100, 660

# ---------------------------------------------------------------------------
# Palette (family accent + the light/dark page grounds from the brief)
# ---------------------------------------------------------------------------
SKIN = {
    "light": dict(
        bg_from="#f9f6fd", bg_to="#e4eaf8",
        card="#ffffff", card_edge="#e6e2ef",
        band="#f5f2fb", edge="#e7e4f0",
        text="#141419", sub="#4d5261", faint="#737a8c",
        accent="#4B67B4", accent_soft="#ece7f9",
        cyan="#0f766e", cyan_bg="#e6f4f1",
        warn="#b45309", warn_bg="#fdf0e7", warn_edge="#e8c9ab",
        good="#15803d", good_bg="#e9f6ee",
        dot="#cfc8e2",
        shadow=(28, 22, 54, 42),
    ),
    "dark": dict(
        bg_from="#131a2a", bg_to="#0c1016",
        card="#1b2231", card_edge="#2e374b",
        band="#242d42", edge="#1e2636",
        text="#f0f3f9", sub="#a8b1c4", faint="#838ca0",
        accent="#8496f5", accent_soft="#242d42",
        cyan="#5eead4", cyan_bg="#17342f",
        warn="#e0a85a", warn_bg="#35271b", warn_edge="#5b4227",
        good="#4ade80", good_bg="#16301f",
        dot="#2a3448",
        shadow=(0, 0, 0, 110),
    ),
}

# ---------------------------------------------------------------------------
# Hero copy. Only the two languages get their own raster; the flow SVG shares
# its English structure labels across all five READMEs.
# ---------------------------------------------------------------------------
HERO = {
    "zh": dict(
        kicker="DEEPSEEK HARNESS · dsh-lc-doc-check",
        title_lines=["信用证交单", "逐条核对"],
        value=["八条规则只读一份交单核对表", "差异落到行号、栏名与应填内容"],
        sub="只核齐备与两项日期，不判是否构成不符点。",
        meta="lc_doc_check · LC-001…008 · JSON/YAML",
        foot="Apache-2.0 · 社区插件 · 无网络 · 不调模型",
        spec_kicker="交单核对表 · 第 1 行",
        spec_chip="LC-001 · warn",
        header=[("lcNo", "LC2026-0018", "mono"), ("beneficiary", "某某出口有限公司", "cjk"),
                ("currency", "USD", "mono"), ("expiryAt", "2026-04-10", "mono")],
        row_labels=["单据种类", "信用证要求", "提交情况"],
        row_keys=["docType", "requirement", "presented"],
        row_value="已提交一式三份，\n已注明信用证号与合同号",
        empty_note="LC-001 · 两栏皆空 → docType、requirement 至少应填一项",
        date_title="两条日期比较 · 共用表头 expiryAt",
        date_labels=["交单日", "最迟装运日"],
        date_note="同一天视为不晚于；有效期先查行、再查表头",
        run_title="本次样例 · 真实输出",
        run_nums=["0", "1", "2"],
        run_labels=["error", "warn", "skipped"],
        run_detail="LC-001 · 第 1 行 · docType",
        run_skip="skipped：LC-005 values 未配置 · LC-008 无 docType 列",
        note="边界：不解读条款，不比对「要求」与「提交情况」两栏。",
    ),
    "en": dict(
        kicker="DEEPSEEK HARNESS · dsh-lc-doc-check",
        title_lines=["Presentation", "checklist"],
        value=["Eight rules over one presentation checklist", "Each difference gets a row and a field"],
        sub="Completeness and two dates — no verdict.",
        meta="lc_doc_check · LC-001…008 · JSON/YAML",
        foot="Apache-2.0 · community plugin · offline · no model calls",
        spec_kicker="PRESENTATION CHECKLIST · ROW 1",
        spec_chip="LC-001 · warn",
        header=[("lcNo", "LC2026-0018", "mono"), ("beneficiary", "某某出口有限公司", "cjk"),
                ("currency", "USD", "mono"), ("expiryAt", "2026-04-10", "mono")],
        row_labels=["docType", "requirement", "presented"],
        row_keys=["", "", ""],
        row_value="submitted in triplicate,\ncredit & contract nos. noted",
        empty_note="LC-001 · both cells empty → docType / requirement must be filled",
        date_title="Two date comparisons · one shared expiryAt",
        date_labels=["presented", "latest shipment"],
        date_note="same day counts as not later; row first, then header",
        run_title="ONE RUN · REAL OUTPUT",
        run_nums=["0", "1", "2"],
        run_labels=["error", "warn", "skipped"],
        run_detail="LC-001 · row 1 · docType",
        run_skip="skipped: LC-005 values unset · LC-008 no docType",
        note="Boundary: no reading of terms, no comparison of the two columns.",
    ),
}

# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------
_FONT_CACHE: dict[tuple[int, str], ImageFont.FreeTypeFont] = {}


def font(size: float, kind: str) -> ImageFont.FreeTypeFont:
    key = (max(1, int(round(size))), kind)
    if key not in _FONT_CACHE:
        path = {"cjk": FONT_CJK, "cjk_bold": FONT_CJK_BOLD, "mono": FONT_MONO}[kind]
        _FONT_CACHE[key] = ImageFont.truetype(path, key[0], index=0)
    return _FONT_CACHE[key]


def tw(text: str, size: float, kind: str) -> float:
    return font(size, kind).getlength(text)


def fit(text: str, kind: str, max_width: float, preferred: float, minimum: float) -> float:
    size = preferred
    while size > minimum and tw(text, size, kind) > max_width:
        size -= 0.5
    if tw(text, size, kind) > max_width:
        raise SystemExit(f"FATAL: text does not fit ({kind}, {max_width}px): {text!r}")
    return size


def require(text: str, size: float, kind: str, max_width: float, label: str) -> None:
    width = tw(text, size, kind)
    if width > max_width:
        raise SystemExit(f"FATAL: {label} overflows: {width:.1f} > {max_width}px: {text!r}")


# ---------------------------------------------------------------------------
# Raster helpers
# ---------------------------------------------------------------------------
def gradient(width: int, height: int, top: str, bottom: str) -> Image.Image:
    top_rgb = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5))
    bottom_rgb = tuple(int(bottom[i:i + 2], 16) for i in (1, 3, 5))
    strip = Image.new("RGB", (1, height))
    pixels = strip.load()
    for y in range(height):
        t = y / max(1, height - 1)
        pixels[0, y] = tuple(
            round(top_rgb[i] * (1 - t) + bottom_rgb[i] * t) for i in range(3)
        )
    return strip.resize((width, height)).convert("RGBA")


def glow(img: Image.Image, cx: int, cy: int, radius: int, color: str, alpha: int) -> Image.Image:
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius], fill=(*rgb, alpha)
    )
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    return Image.alpha_composite(img, layer)


def dots(img: Image.Image, step: int, color: str, alpha: int) -> Image.Image:
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(step // 2, img.height, step):
        for x in range(step // 2, img.width, step):
            d.ellipse([x, y, x + 1.7, y + 1.7], fill=(*rgb, alpha))
    return Image.alpha_composite(img, layer)


def card(
    img: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str,
    edge: str,
    shadow: tuple[int, int, int, int],
    blur: int = 18,
    dy: int = 8,
) -> Image.Image:
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        [x0, y0 + dy, x1, y1 + dy], radius, fill=shadow
    )
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img = Image.alpha_composite(img, layer)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius, fill=fill, outline=edge, width=1)
    return img


def pill(
    d: ImageDraw.ImageDraw,
    x: float,
    y: float,
    text: str,
    size: float,
    kind: str,
    fg: str,
    bg: str,
    pad_x: float = 10,
    height: float | None = None,
) -> float:
    box_h = height if height is not None else round(size * 1.75)
    width = tw(text, size, kind) + pad_x * 2
    d.rounded_rectangle([x, y, x + width, y + box_h], box_h / 2, fill=bg)
    d.text((x + pad_x, y + box_h / 2), text, font=font(size, kind), fill=fg, anchor="lm")
    return width


def dash_line(
    d: ImageDraw.ImageDraw,
    points: list[tuple[float, float]],
    color: str,
    width: int = 1,
    dash: int = 5,
    gap: int = 4,
) -> None:
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if length == 0:
            continue
        ux, uy = (x1 - x0) / length, (y1 - y0) / length
        pos = 0.0
        while pos < length:
            end = min(pos + dash, length)
            d.line(
                [x0 + ux * pos, y0 + uy * pos, x0 + ux * end, y0 + uy * end],
                fill=color,
                width=width,
            )
            pos += dash + gap


def arrow_head(
    d: ImageDraw.ImageDraw,
    x: float,
    y: float,
    direction: str,
    color: str,
    size: float = 5,
) -> None:
    if direction == "right":
        d.polygon([(x, y), (x - size, y - size), (x - size, y + size)], fill=color)
    elif direction == "left":
        d.polygon([(x, y), (x + size, y - size), (x + size, y + size)], fill=color)
    elif direction == "down":
        d.polygon([(x, y), (x - size, y - size), (x + size, y - size)], fill=color)
    elif direction == "up":
        d.polygon([(x, y), (x - size, y + size), (x + size, y + size)], fill=color)


def chip(
    d: ImageDraw.ImageDraw,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    value: str,
    s: dict,
    *,
    label_size: float = 9.5,
    value_size: float = 13,
    value_kind: str = "mono",
    accent: str | None = None,
) -> None:
    edge = accent if accent is not None else s["card_edge"]
    d.rounded_rectangle([x, y, x + width, y + height], 10, fill=s["band"], outline=edge, width=1)
    d.text((x + 12, y + 9), label, font=font(label_size, "mono"), fill=s["faint"])
    require(value, value_size, value_kind, width - 22, f"chip {label}")
    d.text((x + 12, y + 26), value, font=font(value_size, value_kind), fill=s["text"])


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
def hero(lang: str, skin: str) -> None:
    s = SKIN[skin]
    m = HERO[lang]
    img = gradient(HERO_W, HERO_H, s["bg_from"], s["bg_to"])
    img = dots(img, 30, s["dot"], 26 if skin == "light" else 32)
    img = glow(img, 1180, 70, 330, s["accent"], 16 if skin == "light" else 26)
    img = glow(img, 190, 560, 280, s["accent"], 9 if skin == "light" else 18)
    d = ImageDraw.Draw(img)

    left_x, left_w = 76, 606

    # ---- kicker -----------------------------------------------------------
    kicker_size = 17 if lang == "zh" else 16
    require(m["kicker"], kicker_size, "cjk_bold", left_w - 20, "hero kicker")
    pill(d, left_x, 64, m["kicker"], kicker_size, "cjk_bold",
         s["accent"], s["accent_soft"], pad_x=16, height=34)

    # ---- title ------------------------------------------------------------
    title_size = 82
    for line in m["title_lines"]:
        require(line, title_size, "cjk_bold", left_w, "hero title")
    d.text((left_x - 2, 108), m["title_lines"][0], font=font(title_size, "cjk_bold"),
           fill=s["text"])
    d.text((left_x - 2, 200), m["title_lines"][1], font=font(title_size, "cjk_bold"),
           fill=s["text"])
    if title_size * 880 / HERO_W < 48:
        raise SystemExit("FATAL: hero title below 48px displayed")

    # ---- two value lines --------------------------------------------------
    value_size = min(fit(line, "cjk_bold", left_w, 29, 24) for line in m["value"])
    for i, line in enumerate(m["value"]):
        require(line, value_size, "cjk_bold", left_w, f"hero value {i}")
        d.text((left_x, 306 + i * 40), line, font=font(value_size, "cjk_bold"),
               fill=s["text"])

    # ---- subtitle / meta / footer ----------------------------------------
    sub_size = fit(m["sub"], "cjk", left_w, 25, 24.5)
    require(m["sub"], sub_size, "cjk", left_w, "hero subtitle")
    d.text((left_x, 392), m["sub"], font=font(sub_size, "cjk"), fill=s["sub"])
    if sub_size * 880 / HERO_W < 15:
        raise SystemExit("FATAL: hero subtitle below 15px displayed")

    meta_size = fit(m["meta"], "mono", left_w, 20, 20)
    require(m["meta"], meta_size, "mono", left_w, "hero meta")
    d.text((left_x, 438), m["meta"], font=font(meta_size, "mono"), fill=s["sub"])
    if meta_size * 880 / HERO_W < 12:
        raise SystemExit("FATAL: hero meta below 12px displayed")

    d.line([left_x, 482, left_x + left_w - 8, 482], fill=s["edge"], width=1)
    require(m["foot"], 18, "cjk", left_w, "hero footer")
    d.text((left_x, 500), m["foot"], font=font(18, "cjk"), fill=s["faint"])

    # ---- card 1: one checklist row ---------------------------------------
    img = card(img, (752, 60, 1368, 286), 22, s["card"], s["card_edge"], s["shadow"])
    d = ImageDraw.Draw(img)

    d.text((772, 82), m["spec_kicker"],
           font=font(13, "cjk_bold" if lang == "zh" else "mono"), fill=s["accent"])
    chip_w = tw(m["spec_chip"], 10, "mono") + 20
    pill(d, 1348 - chip_w, 76, m["spec_chip"], 10, "mono", s["warn"], s["warn_bg"])

    # header cells, packed left to right
    hx, hy, hh = 772.0, 102.0, 46.0
    widths = [148, 188, 82, 130]
    for index, (label, value, value_kind) in enumerate(m["header"]):
        accent = s["cyan"] if label == "expiryAt" else None
        chip(d, hx, hy, widths[index], hh, label, value, s,
             value_size=12.5 if value_kind == "cjk" else 13,
             value_kind=value_kind,
             accent=accent)
        hx += widths[index] + 8
    if hx - 8 > 1348:
        raise SystemExit("FATAL: hero header chips overflow")

    d.line([772, 162, 1348, 162], fill=s["edge"], width=1)

    # row cells
    cell_y, cell_h = 184, 52
    cell_widths = [116, 244, 192]
    cell_x = [772, 900, 1156]
    for i, label in enumerate(m["row_labels"]):
        d.text((cell_x[i], 172), label,
               font=font(10.5, "mono" if lang == "en" else "cjk"), fill=s["faint"])
        if i < 2:
            d.rounded_rectangle([cell_x[i], cell_y, cell_x[i] + cell_widths[i], cell_y + cell_h],
                                9, fill=s["warn_bg"], outline=s["warn_edge"], width=1)
            d.text((cell_x[i] + cell_widths[i] / 2, cell_y + cell_h / 2), "—",
                   font=font(15, "cjk"), fill=s["warn"], anchor="mm")
        else:
            d.rounded_rectangle([cell_x[i], cell_y, cell_x[i] + cell_widths[i], cell_y + cell_h],
                                9, fill=s["band"], outline=s["edge"], width=1)
            for n, line in enumerate(m["row_value"].split("\n")):
                require(line, 10.5, "cjk", cell_widths[i] - 20, "row value")
                d.text((cell_x[i] + 10, cell_y + 12 + n * 15), line,
                       font=font(10.5, "cjk"), fill=s["text"])
    # canonical field keys after the Chinese column names
    for i, key in enumerate(m["row_keys"]):
        if key == "":
            continue
        d.text((cell_x[i] + tw(m["row_labels"][i], 10.5, "cjk") + 8, 172),
               key, font=font(9.5, "mono"), fill=s["faint"])

    require(m["empty_note"], 10.5, "cjk", 576, "empty note")
    d.text((772, 252), m["empty_note"], font=font(10.5, "cjk"), fill=s["warn"])

    # ---- card 2: the two date comparisons on one shared expiry ------------
    band_box = (752, 300, 1368, 446)
    d.rounded_rectangle(band_box, 16, fill=s["band"], outline=s["card_edge"], width=1)
    d.rounded_rectangle([752, 300, 755, 446], 1.5, fill=s["cyan"])

    d.text((772, 318), m["date_title"],
           font=font(12.5, "cjk_bold" if lang == "zh" else "cjk_bold"), fill=s["text"])

    # geometry: 2026-03-15 .. 2026-04-10 maps onto 880..1258
    base = dt.date(2026, 3, 15)
    span = (dt.date(2026, 4, 10) - base).days
    x_start, x_span = 920.0, 338.0

    def date_x(value: str) -> float:
        year, month, day = (int(part) for part in value.split("-"))
        return x_start + (dt.date(year, month, day) - base).days * x_span / span

    exp_x = date_x("2026-04-10")
    dates = ["2026-03-20", "2026-03-15"]
    rails = [354, 386]
    for index, (label, value, rail_y) in enumerate(zip(m["date_labels"], dates, rails)):
        d.text((772, rail_y - 9), label, font=font(11, "cjk"), fill=s["sub"])
        marker_x = date_x(value)
        d.line([marker_x, rail_y, exp_x - 10, rail_y], fill=s["good"], width=2)
        arrow_head(d, exp_x - 4, rail_y, "right", s["good"], 5)
        d.ellipse([marker_x - 5, rail_y - 5, marker_x + 5, rail_y + 5],
                  fill=s["cyan"], outline=s["card"], width=2)
        d.text((marker_x + 8, rail_y - 16), value, font=font(9.5, "mono"), fill=s["sub"])
        d.text(((marker_x + exp_x) / 2, rail_y - 17), "≤", font=font(13, "cjk_bold"),
               fill=s["good"], anchor="ms")

    # shared expiry line and axis
    dash_line(d, [(exp_x, 330), (exp_x, 398)], s["cyan"], 1, 5, 4)
    d.text((exp_x, 324), "2026-04-10", font=font(10.5, "mono"), fill=s["cyan"], anchor="ms")
    d.line([date_x("2026-03-15"), 406, exp_x, 406], fill=s["edge"], width=1)
    for value in ("2026-03-15", "2026-04-10"):
        tick_x = date_x(value)
        d.line([tick_x, 406, tick_x, 411], fill=s["faint"], width=1)
        d.text((tick_x, 414), value[5:], font=font(10, "mono"), fill=s["faint"], anchor="ms")

    require(m["date_note"], 10, "cjk", 576, "date note")
    d.text((772, 436), m["date_note"], font=font(10, "cjk"), fill=s["faint"])

    # ---- card 3: real run counts ----------------------------------------
    img = card(img, (752, 458, 1368, 534), 16, s["card"], s["card_edge"], s["shadow"], blur=14, dy=6)
    d = ImageDraw.Draw(img)
    d.text((772, 472), m["run_title"], font=font(10.5, "cjk_bold" if lang == "zh" else "mono"),
           fill=s["accent"])

    for i, (num, label) in enumerate(zip(m["run_nums"], m["run_labels"])):
        nx = 772 + i * 78
        color = s["warn"] if label == "warn" else s["text"]
        d.text((nx, 512), num, font=font(27, "cjk_bold"), fill=color, anchor="ls")
        d.text((nx, 522), label, font=font(9.5, "mono"), fill=s["faint"])

    d.line([1014, 472, 1014, 518], fill=s["edge"], width=1)
    require(m["run_detail"], 10.5, "cjk" if lang == "zh" else "mono", 330, "run detail")
    d.text((1030, 476), m["run_detail"],
           font=font(10.5, "cjk" if lang == "zh" else "mono"), fill=s["text"])
    require(m["run_skip"], 10, "cjk" if lang == "zh" else "mono", 330, "run skipped")
    d.text((1030, 498), m["run_skip"],
           font=font(10, "cjk" if lang == "zh" else "mono"), fill=s["warn"])

    # ---- boundary footnote ----------------------------------------------
    require(m["note"], 12, "cjk", 616, "hero boundary note")
    d.text((752, 556), m["note"], font=font(12, "cjk"), fill=s["faint"])

    path = os.path.join(OUT, f"{NAME}-hero-{lang}-{skin}.webp")
    img.convert("RGB").save(path, "WEBP", quality=90, method=6)
    print(f"wrote {os.path.basename(path)}")


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------
def svg_text(
    x: float,
    y: float,
    content: str,
    size: float,
    fill: str,
    *,
    anchor: str = "start",
    mono: bool = False,
    bold: bool = False,
    spacing: float | None = None,
    opacity: float | None = None,
    rotate: float | None = None,
) -> str:
    family = (
        "Consolas,'Microsoft YaHei',ui-monospace,monospace"
        if mono
        else "'Microsoft YaHei','Segoe UI','PingFang SC','Noto Sans CJK SC',sans-serif"
    )
    attrs = [
        f'x="{x:g}"', f'y="{y:g}"', f'fill="{fill}"',
        f'font-family="{family}"', f'font-size="{size:g}"',
    ]
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if bold:
        attrs.append('font-weight="700"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing:g}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity:g}"')
    if rotate is not None:
        attrs.append(f'transform="rotate({rotate:g} {x:g} {y:g})"')
    return f"<text {' '.join(attrs)}>{escape(content)}</text>"


def rect(
    x: float, y: float, w: float, h: float, r: float, fill: str,
    stroke: str | None = None, width: float = 1, dash: str | None = None,
    extra: str = "",
) -> str:
    attrs = [f'x="{x:g}"', f'y="{y:g}"', f'width="{w:g}"', f'height="{h:g}"',
             f'rx="{r:g}"', f'fill="{fill}"']
    if stroke is not None:
        attrs += [f'stroke="{stroke}"', f'stroke-width="{width:g}"']
    if dash is not None:
        attrs.append(f'stroke-dasharray="{dash}"')
    if extra:
        attrs.append(extra)
    return f"<rect {' '.join(attrs)}/>"


def svg_pill(
    x: float, y: float, content: str, size: float, fg: str, bg: str,
    *, mono: bool = True, bold: bool = False, pad: float = 8,
    height: float = 20, stroke: str | None = None, dash: str | None = None,
) -> tuple[str, float]:
    width = tw(content, size, "mono" if mono else "cjk") + pad * 2
    shape = rect(x, y, width, height, height / 2, bg, stroke, 1, dash)
    label = svg_text(x + width / 2, y + height / 2 + size * 0.34, content, size, fg,
                     anchor="middle", mono=mono, bold=bold)
    return shape + label, width


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    parts: list[str] = []
    W, H = FLOW_W, FLOW_H

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">'
    )
    parts.append(
        '<title id="title">dsh-lc-doc-check — three reading scopes over one presentation checklist</title>'
    )
    parts.append(
        '<desc id="desc">Lane A reads the credit header (lcNo, beneficiary, currency, expiryAt) '
        'with LC-006 and LC-007. Lane B reads every row (docType, requirement, presented, '
        'discrepancy) with LC-001, LC-002 and LC-005, and compares presentedAt and latestShipment '
        'against the same expiryAt with LC-003 and LC-004. Lane C compares docType across rows '
        'with LC-008. On the right, findings enter issues[] and checks that cannot run enter '
        'skipped[] with their reason; an empty issues list is not a pass.</desc>'
    )
    parts.append("<defs>")
    parts.append(
        f'<linearGradient id="bg" x1="0" y1="0" x2="0.15" y2="1">'
        f'<stop offset="0" stop-color="{s["bg_from"]}"/>'
        f'<stop offset="1" stop-color="{s["bg_to"]}"/></linearGradient>'
    )
    parts.append(
        f'<radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{s["accent"]}" stop-opacity="0.16"/>'
        f'<stop offset="1" stop-color="{s["accent"]}" stop-opacity="0"/></radialGradient>'
    )
    parts.append(
        '<filter id="soft" x="-20%" y="-20%" width="140%" height="150%">'
        f'<feDropShadow dx="0" dy="5" stdDeviation="8" flood-color="#241d38" '
        f'flood-opacity="{"0.10" if skin == "light" else "0.45"}"/></filter>'
    )
    parts.append(
        f'<marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{s["faint"]}"/></marker>'
    )
    parts.append("</defs>")

    parts.append(rect(0, 0, W, H, 22, "url(#bg)"))
    parts.append(f'<circle cx="960" cy="72" r="268" fill="url(#glow)"/>')

    # ---- header -----------------------------------------------------------
    parts.append(svg_text(44, 60, NAME, 30, s["text"], mono=True, bold=True))
    parts.append(
        svg_text(44, 88,
                 "One presentation checklist, read in three scopes — differences only.",
                 13.5, s["sub"])
    )
    badge_text = "rules/lc-doc-check.yaml · v2026.1"
    badge_w = tw(badge_text, 11, "mono") + 26
    parts.append(rect(1056 - badge_w, 32, badge_w, 28, 14, s["accent_soft"]))
    parts.append(svg_text(1056 - badge_w + 13, 50.4, badge_text, 11, s["accent"], mono=True))

    parts.append(
        svg_text(44, 116, "IN · file / material · JSON or YAML · header + rows[]",
                 11, s["faint"], mono=True)
    )
    parts.append(
        svg_text(1056, 116, "OUT · issues[] + skipped[] · markdown + reportJson",
                 11, s["faint"], mono=True, anchor="end")
    )
    parts.append(f'<line x1="44" y1="130" x2="1056" y2="130" stroke="{s["edge"]}" stroke-width="1"/>')

    # ---- lane A: header ---------------------------------------------------
    parts.append(rect(44, 146, 616, 116, 18, s["card"], s["card_edge"], 1.2,
                      extra='filter="url(#soft)"'))
    parts.append(svg_text(66, 170, "A · 表头 HEADER", 13, s["accent"], bold=True))
    parts.append(svg_text(640, 170, "4 fields · 2 rules", 11, s["faint"],
                          mono=True, anchor="end"))

    chips = [
        ("lcNo", "LC2026-0018", 150, 13, "mono", None),
        ("beneficiary", "某某出口有限公司", 190, 12.5, "cjk", None),
        ("currency", "USD", 84, 13, "mono", None),
        ("expiryAt", "2026-04-10", 130, 13, "mono", s["cyan"]),
    ]
    cx = 64.0
    for label, value, width, size, kind, accent in chips:
        parts.append(rect(cx, 184, width, 44, 10, s["band"],
                          accent if accent is not None else s["card_edge"], 1))
        parts.append(svg_text(cx + 10, 199, label, 11, s["faint"], mono=True))
        if tw(value, size, kind) > width - 20:
            raise SystemExit(f"FATAL: flow header chip overflow: {value!r}")
        parts.append(svg_text(cx + 10, 219, value, size, s["text"], mono=(kind == "mono")))
        cx += width + 8
    if cx - 8 > 642:
        raise SystemExit("FATAL: flow lane A chips overflow")

    pill_a, wa = svg_pill(64, 236, "LC-006 · headerPresence · lcNo + beneficiary",
                         11, s["sub"], s["band"], stroke=s["card_edge"], height=19)
    parts.append(pill_a)
    pill_b, wb = svg_pill(64 + wa + 10, 236, "LC-007 · pattern · ^[A-Z]{3}$",
                          11, s["sub"], s["band"], stroke=s["card_edge"], height=19)
    parts.append(pill_b)
    parts.append(svg_text(642, 249.5, "0 差异", 11, s["good"], anchor="end"))

    # ---- lane B: per-row --------------------------------------------------
    parts.append(rect(44, 276, 616, 212, 18, s["card"], s["card_edge"], 1.2,
                      extra='filter="url(#soft)"'))
    parts.append(svg_text(66, 300, "B · 逐行 ROW", 13, s["accent"], bold=True))
    parts.append(svg_text(640, 300, "every row · 5 rules", 11, s["faint"],
                          mono=True, anchor="end"))

    columns = [
        ("单据种类", "docType", 64, 110, "商业发票"),
        ("信用证要求", "requirement", 182, 180, "商业发票一式三份…"),
        ("提交情况", "presented", 370, 150, "已提交一式三份…"),
        ("不符点", "discrepancy", 528, 114, "无不符点"),
    ]
    for label, key, x, width, value in columns:
        parts.append(svg_text(x, 320, label, 13, s["sub"], bold=True))
        parts.append(svg_text(x, 334, key, 11, s["faint"], mono=True))
        if tw(value, 12.5, "cjk") > width:
            raise SystemExit(f"FATAL: flow column value overflow: {value!r}")
        parts.append(svg_text(x, 352, value, 12.5, s["text"]))

    # LC-001 covers two columns, so its tag spans both of them.
    wc = 298
    parts.append(rect(64, 366, wc, 19, 9.5, s["band"], s["card_edge"], 1))
    parts.append(svg_text(73, 379.5, "LC-001 · docType / requirement", 11, s["sub"], mono=True))
    pill_d, wd = svg_pill(370, 366, "LC-002 · presence", 11, s["sub"], s["band"],
                          stroke=s["card_edge"], height=19)
    parts.append(pill_d)
    pill_e, we = svg_pill(505, 366, "LC-005 · enum", 11,
                          s["warn"], s["warn_bg"], stroke=s["warn_edge"], height=19)
    parts.append(pill_e)
    parts.append(svg_text(505 + we + 8, 379.5, "skipped", 11, s["warn"], mono=True))

    # date block
    parts.append(rect(56, 396, 592, 82, 12, s["band"], s["card_edge"], 1))
    pill_f, wf = svg_pill(68, 408, "LC-003 · date", 11, s["cyan"], s["cyan_bg"],
                          stroke=s["cyan"], height=19)
    parts.append(pill_f)
    parts.append(svg_text(68 + wf + 10, 421.5,
                          "交单日 2026-03-20 ≤ 有效期 2026-04-10", 12, s["text"]))
    parts.append(svg_text(68 + wf + 10 + 244, 421.5, "✓", 12, s["good"], bold=True))

    pill_g, wg = svg_pill(68, 438, "LC-004 · date", 11, s["cyan"], s["cyan_bg"],
                          stroke=s["cyan"], height=19)
    parts.append(pill_g)
    parts.append(svg_text(68 + wg + 10, 451.5,
                          "最迟装运日 2026-03-15 ≤ 有效期 2026-04-10", 12, s["text"]))
    parts.append(svg_text(68 + wg + 10 + 268, 451.5, "✓", 12, s["good"], bold=True))

    # shared-expiry bracket: both comparisons point at the same header field
    bracket_x = 470
    parts.append(f'<path d="M{bracket_x} 414 h8 M{bracket_x} 414 v32 M{bracket_x} 446 h8" '
                 f'stroke="{s["cyan"]}" stroke-width="1.4" fill="none"/>')
    parts.append(svg_text(bracket_x + 14, 422, "shared expiryAt", 11, s["cyan"], mono=True))
    parts.append(svg_text(bracket_x + 14, 436, "同一天视为不晚于", 11, s["faint"]))
    parts.append(svg_text(636, 465, "有效期先查行、再查表头", 11, s["faint"], anchor="end"))

    # ---- lane C: cross-row ------------------------------------------------
    parts.append(rect(44, 500, 616, 80, 18, s["card"], s["card_edge"], 1.2,
                      extra='filter="url(#soft)"'))
    parts.append(svg_text(66, 524, "C · 跨行 CROSS-ROW", 13, s["accent"], bold=True))
    parts.append(svg_text(640, 524, "1 rule", 11, s["faint"], mono=True, anchor="end"))

    for i, x in enumerate((64, 170)):
        parts.append(rect(x, 532, 94, 22, 11, s["band"], s["card_edge"], 1))
        parts.append(svg_text(x + 47, 547, f"第 {'i' if i == 0 else 'j'} 行 docType",
                              11, s["sub"], mono=False, anchor="middle"))
    parts.append(svg_text(274, 547, "≡", 13, s["faint"], anchor="middle"))
    pill_h, wh = svg_pill(290, 532, "LC-008 · unique · docType", 11, s["sub"], s["band"],
                          stroke=s["card_edge"], height=20)
    parts.append(pill_h)
    parts.append(svg_text(290 + wh + 10, 546, "忽略空格后相同 → 报重复",
                          11, s["faint"]))
    parts.append(svg_text(66, 570, "本次 skipped：材料没有「docType」列，本条不适用",
                          11, s["warn"]))

    # ---- report column ----------------------------------------------------
    parts.append(rect(704, 146, 352, 434, 18, s["card"], s["card_edge"], 1.2,
                      extra='filter="url(#soft)"'))
    parts.append(svg_text(722, 171, "REPORT", 13.5, s["accent"], bold=True))
    parts.append(svg_text(1038, 171, "ruleset v2026.1", 11, s["faint"],
                          mono=True, anchor="end"))

    for i, (num, label, color) in enumerate((
        ("0", "error", s["text"]),
        ("1", "warn", s["warn"]),
        ("2", "skipped", s["warn"]),
    )):
        x = 722 + i * 88
        parts.append(svg_text(x, 224, num, 30, color, mono=True, bold=True))
        parts.append(svg_text(x, 240, label, 11, s["faint"], mono=True))

    parts.append(svg_text(1038, 200, "issueCount 1", 11, s["faint"], mono=True, anchor="end"))
    parts.append(svg_text(1038, 216, "skippedCount 2", 11, s["faint"], mono=True, anchor="end"))
    parts.append(f'<line x1="722" y1="256" x2="1038" y2="256" stroke="{s["edge"]}" stroke-width="1"/>')

    # issues
    parts.append(svg_text(722, 282, "issues[] · 1", 12, s["accent"], mono=True, bold=True))
    chip_i, wi = svg_pill(1038 - (tw("LC-001 · warn", 10.5, "mono") + 16), 268,
                          "LC-001 · warn", 10.5, s["warn"], s["warn_bg"], height=19)
    parts.append(chip_i)
    parts.append(svg_text(722, 304, "row 1 · column docType", 11, s["faint"], mono=True))
    parts.append(svg_text(722, 328, "第 1 行 docType、requirement 都为空", 13, s["text"]))
    parts.append(svg_text(722, 348, "docType、requirement 至少应填写一项", 11.5, s["sub"]))
    parts.append(svg_text(722, 368, "fix：补填两栏之一，不判断条款含义", 11, s["faint"]))
    parts.append(f'<line x1="722" y1="384" x2="1038" y2="384" stroke="{s["edge"]}" stroke-width="1"/>')

    # skipped
    parts.append(svg_text(722, 410, "skipped[] · 2", 12, s["accent"], mono=True, bold=True))
    chip_j, wj = svg_pill(722, 424, "LC-005", 10.5, s["warn"], s["warn_bg"], height=18)
    parts.append(chip_j)
    parts.append(svg_text(722 + wj + 8, 437, "values 未配置：取值口径由本机构规定",
                          11, s["sub"]))
    chip_k, wk = svg_pill(722, 458, "LC-008", 10.5, s["warn"], s["warn_bg"], height=18)
    parts.append(chip_k)
    parts.append(svg_text(722 + wk + 8, 471, "材料没有「docType」列，本条不适用",
                          11, s["sub"]))
    parts.append(f'<line x1="722" y1="496" x2="1038" y2="496" stroke="{s["edge"]}" stroke-width="1"/>')

    parts.append(svg_text(722, 518, "8 条均非 direct → error 恒为 0", 11, s["faint"]))
    parts.append(svg_text(722, 538, "空 issues 不等于通过", 12, s["warn"], bold=True))
    parts.append(svg_text(722, 556, "结论留给审核人", 11, s["faint"]))

    # ---- exits from the three lanes into one report bus ------------------
    bus = 678
    parts.append(
        f'<path d="M660 376 H{bus} M660 442 H{bus} M660 548 H{bus}" fill="none" '
        f'stroke="{s["faint"]}" stroke-width="1.1" stroke-dasharray="4 4" opacity="0.75"/>'
    )
    parts.append(
        f'<path d="M{bus} 282 V548" fill="none" stroke="{s["faint"]}" '
        f'stroke-width="1.1" opacity="0.55"/>'
    )
    parts.append(
        f'<path d="M{bus} 282 H700" fill="none" stroke="{s["faint"]}" stroke-width="1.2" '
        f'marker-end="url(#arrow)"/>'
    )
    parts.append(
        f'<path d="M{bus} 410 H700" fill="none" stroke="{s["faint"]}" stroke-width="1.2" '
        f'marker-end="url(#arrow)"/>'
    )

    # ---- footer -----------------------------------------------------------
    parts.append(
        f'<circle cx="49" cy="604" r="4" fill="{s["good"]}"/>'
        f'<text x="58" y="608" fill="{s["faint"]}" font-family="\'Microsoft YaHei\',sans-serif" '
        f'font-size="11">执行且无差异</text>'
        f'<circle cx="164" cy="604" r="4" fill="{s["warn"]}"/>'
        f'<text x="173" y="608" fill="{s["faint"]}" font-family="\'Microsoft YaHei\',sans-serif" '
        f'font-size="11">命中 issues[]</text>'
        f'<circle cx="280" cy="604" r="4" fill="none" stroke="{s["faint"]}" stroke-width="1.2"/>'
        f'<text x="289" y="608" fill="{s["faint"]}" font-family="\'Microsoft YaHei\',sans-serif" '
        f'font-size="11">未执行 skipped[]</text>'
    )
    parts.append(
        svg_text(1056, 608, "read-only · no network · no model call · original file untouched",
                 11, s["faint"], mono=True, anchor="end")
    )
    parts.append(
        svg_text(44, 634,
                 "只核核对表自身：不解读信用证条款、不把「信用证要求」与「提交情况」做实质比对、不判是否构成不符点。",
                 11.5, s["sub"])
    )

    parts.append("</svg>")
    svg = "\n".join(parts) + "\n"
    ET.fromstring(svg)
    return svg


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for lang in ("zh", "en"):
        for skin in ("light", "dark"):
            hero(lang, skin)
    for skin in ("light", "dark"):
        svg = flow_svg(skin)
        path = os.path.join(OUT, f"{NAME}-flow-v5-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        print(f"wrote {os.path.basename(path)}")


if __name__ == "__main__":
    main()
