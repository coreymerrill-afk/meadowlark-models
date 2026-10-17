#!/usr/bin/env python3
"""Write /furniture/index.html and /furniture/<slug>/index.html from furniture-data."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "furniture-data"
OUT = ROOT / "furniture"

ORDER = [
    "bookcase",
    "desk",
    "dog-crate",
    "kitchen-cart",
    "nightstand",
    "retail-display",
    "shoe-bench",
]

PARAM_LABELS = {
    "width": "Width",
    "depth": "Depth",
    "height": "Height",
    "thickness": "Thickness",
    "clearance": "Slot clearance",
    "plinth": "Plinth height",
    "mid_shelf_z": "Mid shelf height",
    "adj_shelves": "Adjustable shelves",
    "dividers": "Dividers",
    "pin_hole": "Pin hole",
    "pin_pitch": "Pin pitch",
    "drawer": "Drawer",
    "drawer_w": "Drawer width",
    "drawer_len": "Drawer length",
    "monitor_shelf": "Monitor shelf",
    "cable_slot": "Cable slot",
    "door_w": "Door width",
    "slat_gap": "Slat gap",
    "slat_bar": "Slat width",
    "tiers": "Tiers",
    "base_depth": "Base depth",
    "step": "Step back each tier",
    "first_z": "First shelf height",
    "sign_h": "Sign height",
    "logo": "Logo",
    "shelves": "Shelves",
    "cushion_recess": "Cushion recess",
    "slatted": "Slatted shelves",
    "cleat": "Cleat",
    "shelf_z": "Shelf height",
}

GROUP_LABELS = {
    "carcass": "Carcass",
    "shelf": "Shelf",
    "drawer": "Drawer",
    "cleat": "Cleat",
    "feet": "Feet",
    "top": "Top",
    "door": "Door",
    "tray": "Tray",
    "option": "Option",
    "sign": "Sign",
}

TOGGLE_ORDER = ["drawer", "casters", "cleat"]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def mm(n) -> str:
    n = float(n)
    if n.is_integer():
        return f"{int(n):,}"
    text = f"{n:.2f}".rstrip("0").rstrip(".")
    return text


def inch(n) -> str:
    text = f"{float(n) / 25.4:.1f}".rstrip("0").rstrip(".")
    return text


def money(n) -> str:
    n = float(n)
    sign = "-" if n < 0 else ""
    return sign + f"${abs(n):,.2f}"


def money_short(n) -> str:
    n = float(n)
    if n.is_integer():
        return f"${int(n):,}"
    return money(n)


def hours(h) -> str:
    text = f"{float(h):.2f}".rstrip("0").rstrip(".")
    return text + " h"


def fmt_min(m) -> str:
    total = int(round(float(m)))
    h, mins = divmod(total, 60)
    if h and mins:
        return f"{h} h {mins} min"
    if h:
        return f"{h} h"
    return f"{mins} min"


def num_text(n) -> str:
    n = float(n) if not isinstance(n, str) else float(n)
    if n.is_integer():
        return str(int(n))
    return f"{n:.2f}".rstrip("0").rstrip(".")


def labelize(name: str) -> str:
    return PARAM_LABELS.get(name) or name.replace("_", " ").capitalize()


def group_label(name: str) -> str:
    return GROUP_LABELS.get(name) or name.replace("_", " ").capitalize()


def main_dims(dims: dict) -> tuple[float, float, float]:
    width = float(dims["width"])
    depth = float(dims["depth"] if "depth" in dims else dims["base_depth"])
    height = float(dims["height"])
    return width, depth, height


def size_phrase(dims: dict) -> str:
    width, depth, height = main_dims(dims)
    return f"{mm(width)} × {mm(depth)} × {mm(height)} mm"


def size_sentence(dims: dict) -> str:
    width, depth, height = main_dims(dims)
    bits = [
        f"{mm(width)} mm wide, {mm(depth)} mm deep, {mm(height)} mm tall "
        f"({inch(width)} × {inch(depth)} × {inch(height)} in)"
    ]
    if "interior_length" in dims:
        bits.append(
            f"inside {mm(dims['interior_length'])} × {mm(dims['interior_width'])} × {mm(dims['interior_height'])} mm"
        )
    elif "interior_width" in dims:
        bits.append(f"inside width {mm(dims['interior_width'])} mm")
    if "door_opening" in dims:
        door = dims["door_opening"]
        bits.append(f"door opening {mm(door[0])} × {mm(door[1])} mm")
    if "plinth_clearance" in dims:
        bits.append(f"{mm(dims['plinth_clearance'])} mm clear underneath")
    if "foot_notch_height" in dims:
        bits.append(f"foot notch {mm(dims['foot_notch_height'])} mm")
    if "knee_bay_clear_width" in dims:
        bits.append(f"knee bay {mm(dims['knee_bay_clear_width'])} mm clear")
    if "top_overhang" in dims:
        bits.append(f"the top overhangs {mm(dims['top_overhang'])} mm")
    if "caster_height" in dims:
        bits.append(f"casters lift the base {mm(dims['caster_height'])} mm")
    if "shelf_slot_rows" in dims:
        bits.append(f"{int(dims['shelf_slot_rows'])} shelf rows, {mm(dims['shelf_pitch'])} mm apart")
    if "tiers" in dims:
        bits.append(f"{int(dims['tiers'])} tiers, top shelf {mm(dims['top_shelf_depth'])} mm deep")
    if "bay_clear_height" in dims:
        bits.append(f"shelf bay {mm(dims['bay_clear_height'])} mm clear")
    return ". ".join(bit[:1].upper() + bit[1:] for bit in bits) + "."


def sheet_word(count: int) -> str:
    return "1 sheet" if count == 1 else f"{count} sheets"


def load(slug: str) -> tuple[dict, dict]:
    plan = json.loads((DATA / slug / "plan.json").read_text())
    parts = json.loads((DATA / slug / "parts.json").read_text())
    return plan, parts


def optional_groups(parts: dict) -> list[str]:
    found = []
    for part in parts["parts"]:
        if part.get("optional") and part["group"] not in found:
            found.append(part["group"])
    if any(part["name"].startswith("FOOT-A") for part in parts["parts"]):
        found.append("casters")
    ordered = [name for name in TOGGLE_ORDER if name in found]
    ordered.extend(name for name in found if name not in ordered)
    return ordered


def toggle_label(group: str) -> tuple[str, bool]:
    if group == "cleat":
        return "Cleat backer", False
    if group == "drawer":
        return "Drawer", True
    if group == "casters":
        return "Casters", True
    return group_label(group), True


def page_shell(title: str, description: str, body: str, extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#1c1712" />
<meta name="description" content="{esc(description)}" />
<link rel="icon" href="data:," />
<title>{esc(title)}</title>
<link rel="stylesheet" href="/furniture/furniture.css" />
{extra_head}</head>
<body>
{body}
</body>
</html>
"""


def render_gallery(designs: list[dict]) -> str:
    cards = []
    for item in designs:
        plan = item["plan"]
        slug = plan["slug"]
        sheets = int(plan["sheet_count"])
        price = plan["profit"]["at_price"]["mid"]["price"]
        cards.append(
            f"""<a class="card" href="/furniture/{esc(slug)}">
  <div class="card-media">
    <img src="/furniture-data/{esc(slug)}/assembly.png" width="1800" height="937" alt="Assembly drawing of the {esc(plan['name'])}." />
  </div>
  <div class="card-body">
    <h2>{esc(plan['name'])}</h2>
    <p class="pitch">{esc(plan['pitch'])}</p>
    <dl class="stats">
      <div class="wide"><dt>Size</dt><dd>{esc(size_phrase(plan['dimensions_mm']))}</dd></div>
      <div><dt>Sheets</dt><dd>{esc(sheet_word(sheets))}</dd></div>
      <div><dt>Mid price</dt><dd>{esc(money_short(price))}</dd></div>
    </dl>
  </div>
</a>"""
        )
    body = f"""<header class="doc-header">
  <p class="crumbs"><a href="/">All models</a></p>
  <h1>Shop furniture</h1>
  <p class="lede">Seven flat-pack designs in 18 mm plywood, each cut from 4×8 sheets. Open a piece for the model, the cut sheets, and the build. Mid prices are planning estimates, not quotes.</p>
</header>
<main class="wrap">
  <div class="gallery">
    {chr(10).join(cards)}
  </div>
  <p class="site-foot">Meadowlark Models. The feed rate behind the cut times is unverified.</p>
</main>
<script>
(function () {{
  var slugs = {json.dumps(ORDER)};
  var h = (location.hash || '').replace(/^#/, '');
  if (h === 'cart') h = 'kitchen-cart';
  if (slugs.indexOf(h) !== -1) location.replace('/furniture/' + h);
}})();
</script>
"""
    return page_shell(
        "Shop furniture — Meadowlark Models",
        "Seven flat-pack plywood designs: bookcase, desk, dog crate, kitchen cart, nightstand, retail display, and shoe bench. Cut sheets, a 3D model, and a build order for each.",
        body,
    )


def render_toggles(parts: dict) -> str:
    chips = []
    for group in optional_groups(parts):
        label, checked = toggle_label(group)
        checked_attr = " checked" if checked else ""
        chips.append(
            f'<label class="chip"><input type="checkbox" data-toggle="{esc(group)}"{checked_attr} /> {esc(label)}</label>'
        )
    return "\n    ".join(chips)


def render_parts_list(plan_sheet: dict, parts: dict) -> str:
    by_name: dict[str, list[dict]] = {}
    for item in plan_sheet["parts"]:
        by_name.setdefault(item["name"], []).append(item)
    used: dict[str, int] = {}
    rows = []
    for part in parts["parts"]:
        if part.get("sheet") != plan_sheet["sheet"]:
            continue
        name = part["name"]
        bucket = by_name.get(name, [])
        index = used.get(name, 0)
        used[name] = index + 1
        number = bucket[index]["number"] if index < len(bucket) else ""
        optional = " <span class=\"badge\">Optional</span>" if part.get("optional") else ""
        rows.append(
            (
                int(number) if number != "" else 999,
                name,
                f"""<li><button type="button" class="part" data-part="{esc(name)}" aria-pressed="false">
  <span class="pn">{esc(number)}</span>
  <span class="pn-name">{esc(name)}{optional}</span>
  <span class="pn-size">{esc(mm(part['width']))} × {esc(mm(part['height']))} mm</span>
  <span class="pn-qty">Qty 1</span>
  <span class="pn-group">{esc(group_label(part['group']))}</span>
</button></li>""",
            )
        )
    rows.sort(key=lambda row: (row[0], row[1]))
    return "\n".join(row[2] for row in rows)


def render_sheets(plan: dict, parts: dict) -> str:
    profit = plan["profit"]
    count = int(plan["sheet_count"])
    slow, mid, fast = profit["machine_minutes_at_100_150_200_mm_per_min"]
    blocks = []
    for sheet in plan["sheets"]:
        n = int(sheet["sheet"])
        title = f"Sheet {n} of {count}"
        png = f"/furniture-data/{plan['slug']}/{sheet['png']}"
        path_m = float(sheet["cut_path_m"])
        mid_min = path_m * 1000 / 150
        alt = (
            f"{title} for the {plan['name']}. "
            f"Each part is labelled on a 1220 by 2440 mm plywood sheet."
        )
        blocks.append(
            f"""<article class="sheet">
  <div class="sheet-head">
    <h3>{esc(title)}</h3>
    <p class="sheet-meta">{esc(str(sheet['part_count']))} parts on this sheet. They cover {esc(sheet['coverage_pct'])}% of a 1220 × 2440 mm sheet. Cut path {esc(f'{path_m:.2f}'.rstrip('0').rstrip('.'))} m, about {esc(fmt_min(mid_min))} at 150 mm per minute.</p>
  </div>
  <div class="sheet-bleed">
    <button type="button" class="sheet-open" data-title="{esc(title)}" aria-label="Open {esc(title)} larger, then pan and zoom">
      <img src="{esc(png)}" width="1800" alt="{esc(alt)}" />
      <span class="zoom-hint">Tap to zoom and pan</span>
    </button>
  </div>
  <ul class="parts">
    {render_parts_list(sheet, parts)}
  </ul>
</article>"""
        )
    summary = f"""<div class="sheet-summary">
  <p><strong>{esc(sheet_word(count))}.</strong> 1220 × 2440 mm, 18 mm plywood. Total cut path {esc(profit['cut_path_m'])} m.</p>
  <p>If the feed is 100, 150, or 200 mm per minute, the machine time is about {esc(fmt_min(slow))}, {esc(fmt_min(mid))}, or {esc(fmt_min(fast))}. The profit table uses the middle figure. That feed rate is an unverified estimate. Sheet 1 carries a fit-test coupon: cut it first and try the tab in the slot before you cut the rest. Hover or tap a part below to light it in the model.</p>
</div>"""
    return summary + "\n" + "\n".join(blocks)


def render_stages(plan: dict) -> str:
    items = []
    for stage in plan["stages"]:
        minutes = stage["minutes"]
        extra = f" ({fmt_min(minutes)})" if minutes >= 60 else ""
        items.append(
            f"""<li>
  <div class="step-no">{esc(stage['step'])}</div>
  <div class="step-body">
    <h3>{esc(stage['title'])} <span class="mins">about {esc(minutes)} min{esc(extra)}</span></h3>
    <p>{esc(stage['detail'])}</p>
  </div>
</li>"""
        )
    total = plan["stage_total_minutes"]
    return f"""<ol class="timeline">
{chr(10).join(items)}
</ol>
<p class="total">About {esc(fmt_min(total))} for all {esc(len(plan['stages']))} stages.</p>"""


def render_materials(plan: dict) -> str:
    materials = plan["materials"]
    rows = []
    total = 0.0
    for item in materials["hardware"]:
        line = float(item["qty"]) * float(item["unit_cost"])
        total += line
        note = item.get("note") or ""
        note_html = f"<br /><span class=\"fine\">{esc(note)}</span>" if note else ""
        rows.append(
            f"<tr><td>{esc(item['item'])}{note_html}</td>"
            f"<td class=\"num\">{esc(num_text(item['qty']))}</td>"
            f"<td class=\"num\">{esc(money(item['unit_cost']))}</td>"
            f"<td class=\"num\">{esc(money(line))}</td></tr>"
        )
    screws = materials.get("screws_counted_from_model") or {}
    screw_bits = ", ".join(f"{esc(name)} × {esc(qty)}" for name, qty in screws.items())
    screw_line = f"<p>Screws counted from the model: {screw_bits}.</p>" if screw_bits else ""
    return f"""<p>{esc(materials['sheet'])}. Thickness {esc(num_text(materials['thickness_mm']))} mm. {esc(sheet_word(int(materials['sheets_required'])))}.</p>
<p>Glue: {esc(materials['glue'])}.</p>
<p>Finish: {esc(materials['finish'])}.</p>
<div class="table-wrap">
<table>
  <thead><tr><th>Hardware</th><th class="num">Qty</th><th class="num">Each</th><th class="num">Line</th></tr></thead>
  <tbody>
    {chr(10).join(rows)}
    <tr><td>Hardware total</td><td></td><td></td><td class="num">{esc(money(total))}</td></tr>
  </tbody>
</table>
</div>
{screw_line}"""


def margin_cells(profit: dict, key: str, as_pct: bool = False) -> str:
    cells = []
    for band in ("low", "mid", "high"):
        value = profit["at_price"][band][key]
        text = f"{float(value):.1f}%" if as_pct else money(value)
        cls = "num"
        if not as_pct and float(value) < 0:
            cls = "num neg"
        cells.append(f'<td class="{cls}">{esc(text)}</td>')
    return "".join(cells)


def render_profit(plan: dict) -> str:
    profit = plan["profit"]
    costs = profit["cost_per_unit_low_mid_high"]
    bands = "".join(
        f'<td class="num">{esc(money(profit["at_price"][band]["price"]))}</td>' for band in ("low", "mid", "high")
    )
    cost_cells = "".join(f'<td class="num">{esc(money(profit["at_price"]["mid"]["cogs_mid"]))}</td>' for _ in range(3))
    hours_cells = "".join(f'<td class="num">{esc(hours(profit["machine_hours_mid"]))}</td>' for _ in range(3))
    slow, mid, fast = profit["machine_minutes_at_100_150_200_mm_per_min"]
    fixed = float(profit["finish_cost"]) + float(profit["packaging_cost"]) + float(profit["machine_wear_cost"])
    calc = {
        "sheetCost": profit["sheet_cost_mid"],
        "hardwareCost": profit["hardware_cost"],
        "price": profit["at_price"]["mid"]["price"],
        "laborRate": 25,
        "laborHours": profit["labor_hours"],
        "fixedCost": round(fixed, 2),
        "machineHours": profit["machine_hours_mid"],
        "feeRate": 0.10,
    }
    return f"""<div class="callout">
  <strong>Estimates and assumptions.</strong> Every dollar figure on this page is a planning estimate, not a quote and not a promise. Sheet price, hardware, fees, labor, and machine wear are assumptions. The feed rate of 100–200 mm per minute is unverified. The maker does not publish a rate for 18 mm plywood, so the hours and the profit per hour move once you time a real cut.
</div>
<div class="table-wrap">
<table>
  <caption>Gross margin and net use the mid cost per unit (${esc(f'{float(costs[1]):.2f}')}). Low and high sheet prices would put the cost at {esc(money(costs[0]))} or {esc(money(costs[2]))}. Machine hours are the middle feed, {esc(hours(profit['machine_hours_mid']))}. At 100 mm/min that is {esc(fmt_min(slow))}; at 200 mm/min, {esc(fmt_min(fast))}.</caption>
  <thead>
    <tr><th></th><th class="num">Low price</th><th class="num">Mid price</th><th class="num">High price</th></tr>
  </thead>
  <tbody>
    <tr><th>Selling price</th>{bands}</tr>
    <tr><th>Cost per unit</th>{cost_cells}</tr>
    <tr><th>Gross margin</th>{margin_cells(profit, 'gross_margin')}</tr>
    <tr><th>Gross margin %</th>{margin_cells(profit, 'gross_margin_pct', as_pct=True)}</tr>
    <tr><th>Net after fees and labor</th>{margin_cells(profit, 'net_after_fees_and_labor')}</tr>
    <tr><th>Machine hours</th>{hours_cells}</tr>
    <tr><th>Gross profit per machine hour</th>{margin_cells(profit, 'gross_margin_per_machine_hour')}</tr>
    <tr><th>Net profit per machine hour</th>{margin_cells(profit, 'net_after_fees_and_labor_per_machine_hour')}</tr>
  </tbody>
</table>
</div>
<p>{esc(profit['note_machine_time'])}</p>
<p class="fine">{esc(profit['assumptions'])}</p>
<p class="fine">Where the price band came from: {esc(profit['price_band_source'])}</p>
<h3>Try your own numbers</h3>
<p>Change the sheet cost, hardware, selling price, or labor rate. Finish (${esc(money(profit['finish_cost']))}), packaging (${esc(money(profit['packaging_cost']))}), and machine wear (${esc(money(profit['machine_wear_cost']))}) stay put, together {esc(money(fixed))}. Fees stay at 10% of the selling price. Labor uses the planned {esc(hours(profit['labor_hours']))} at the rate you type. Machine hours stay at {esc(hours(profit['machine_hours_mid']))}, which still depends on the unverified feed.</p>
<div class="calc">
  <label>Sheet cost, $ <input id="sheet-cost" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['sheet_cost_mid'])}" /></label>
  <label>Hardware cost, $ <input id="hardware-cost" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['hardware_cost'])}" /></label>
  <label>Selling price, $ <input id="selling-price" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['at_price']['mid']['price'])}" /></label>
  <label>Labor rate, $ per hour <input id="labor-rate" inputmode="decimal" type="number" min="0" step="0.5" value="25" /></label>
</div>
<div class="calc-out" id="calc-out" aria-live="polite"></div>
<p class="fine">Still an estimate. If the real cut is slower or faster than 150 mm per minute, machine hours and profit per hour change even when these four numbers do not.</p>
<script type="application/json" id="calc-data">{json.dumps(calc)}</script>"""


def render_parameters(plan: dict) -> str:
    rows = []
    for param in plan["parameters"]:
        rows.append(
            f"<tr><th>{esc(labelize(param['name']))}</th>"
            f"<td>{esc(num_text(param['default']))}</td>"
            f"<td>{esc(param['limits'])}</td></tr>"
        )
    return f"""<p class="prose">These are the knobs for a custom order. The model on this page uses the defaults. Stay inside the limits.</p>
<div class="table-wrap">
<table>
  <thead><tr><th>Parameter</th><th>Default</th><th>Limits</th></tr></thead>
  <tbody>
    {chr(10).join(rows)}
  </tbody>
</table>
</div>"""


def render_safety(plan: dict) -> str:
    safety = "\n".join(f"<li>{esc(item)}</li>" for item in plan["safety"])
    unverified = "\n".join(f"<li>{esc(item)}</li>" for item in plan["unverified"])
    return f"""<h2 id="safety-heading">Safety notes</h2>
<ul class="plain">{safety}</ul>
<h2>Unverified / to test</h2>
<ul class="plain">{unverified}</ul>"""


def render_downloads(plan: dict) -> str:
    slug = plan["slug"]
    links = []
    for sheet in plan["sheets"]:
        href = f"/furniture-data/{slug}/{sheet['dxf']}"
        links.append(
            f"""<a class="file" href="{esc(href)}" download="{esc(sheet['dxf'])}">
  <strong>Sheet {esc(sheet['sheet'])} DXF</strong>
  <span>{esc(sheet['dxf'])} · millimeters, one 1220 × 2440 mm sheet</span>
</a>"""
        )
    links.append(
        f"""<a class="file" href="/furniture-data/{esc(slug)}/parts.json" download="{esc(slug)}-parts.json">
  <strong>Parts file</strong>
  <span>parts.json · the plates the 3D model is built from, with a sheet number on each part</span>
</a>"""
    )
    links.append(
        f"""<a class="file" href="/furniture-data/{esc(slug)}/README.md" download="{esc(slug)}-README.md">
  <strong>README</strong>
  <span>README.md · size, joints, and the check that was run on the model</span>
</a>"""
    )
    return f'<div class="files">{chr(10).join(links)}</div>'


def render_zoom() -> str:
    return """<dialog class="zoom" id="zoom" aria-label="Cut sheet zoom">
  <div class="zoom-bar">
    <p id="zoom-title">Cut sheet</p>
    <button type="button" id="zoom-close">Close</button>
  </div>
  <div class="zoom-stage" id="zoom-stage">
    <img id="zoom-img" alt="" draggable="false" />
  </div>
  <div class="zoom-tools">
    <button type="button" id="zoom-out">Zoom out</button>
    <button type="button" id="zoom-in">Zoom in</button>
    <button type="button" id="zoom-labels">Read labels</button>
    <button type="button" id="zoom-fit">Fit</button>
    <p class="tool-note">Drag to pan. Scroll, pinch, or use the buttons to zoom. Double-click zooms in on that spot.</p>
  </div>
</dialog>"""


def render_design(plan: dict, parts: dict) -> str:
    slug = plan["slug"]
    name = plan["name"]
    sheets = int(plan["sheet_count"])
    price = plan["profit"]["at_price"]["mid"]["price"]
    body = f"""<header class="doc-header">
  <p class="crumbs"><a href="/">All models</a> · <a href="/furniture/">Shop furniture</a></p>
  <h1>{esc(name)}</h1>
  <p class="pitch">{esc(plan['pitch'])}</p>
  <p class="size-line">{esc(size_sentence(plan['dimensions_mm']))} {esc(sheet_word(sheets))}. Mid retail price {esc(money_short(price))}, an estimate.</p>
</header>
<nav class="jumps" aria-label="On this page">
  <a href="#model">Model</a>
  <a class="jump-main" href="#cut-sheets">Cut sheets</a>
  <a href="#build">Build</a>
  <a href="#materials">Materials</a>
  <a href="#profit">Profit</a>
  <a href="#parameters">Parameters</a>
  <a href="#safety">Safety</a>
  <a href="#downloads">Downloads</a>
</nav>
<p class="sr" id="model-status" aria-live="polite"></p>
<section class="block" id="model" aria-labelledby="model-heading">
  <h2 class="sr" id="model-heading">Model</h2>
  <div class="stage">
    <div id="canvas-wrap">
      <div id="three-loading">Loading the model…</div>
      <div id="three-error" hidden></div>
    </div>
    <div class="tool-bar">
      <label class="explode" for="explode">Exploded
        <input id="explode" type="range" min="0" max="100" value="0" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-valuetext="0 percent exploded" />
      </label>
      {render_toggles(parts)}
      <button type="button" class="ghost" id="btn-reset">Reset view</button>
      <p class="tool-note">Drag to turn. Scroll or pinch to zoom. The slider pulls the panels apart, and the view pulls back so the pieces stay in frame.</p>
      <p class="tool-note" id="lit-note" aria-live="polite"></p>
    </div>
  </div>
</section>
<main class="wrap">
  <section class="block" id="cut-sheets" aria-labelledby="sheets-heading">
    <h2 id="sheets-heading">The cut sheets</h2>
    {render_sheets(plan, parts)}
  </section>
  <section class="block" id="build" aria-labelledby="build-heading">
    <h2 id="build-heading">Build stages</h2>
    {render_stages(plan)}
  </section>
  <section class="block" id="materials" aria-labelledby="materials-heading">
    <h2 id="materials-heading">Materials and hardware</h2>
    {render_materials(plan)}
  </section>
  <section class="block" id="profit" aria-labelledby="profit-heading">
    <h2 id="profit-heading">Profit estimate</h2>
    {render_profit(plan)}
  </section>
  <section class="block" id="parameters" aria-labelledby="parameters-heading">
    <h2 id="parameters-heading">Parameters</h2>
    {render_parameters(plan)}
  </section>
  <section class="block" id="safety" aria-labelledby="safety-heading">
    {render_safety(plan)}
  </section>
  <section class="block" id="downloads" aria-labelledby="downloads-heading">
    <h2 id="downloads-heading">Downloads</h2>
    {render_downloads(plan)}
  </section>
  <p class="site-foot">Meadowlark Models. Numbers on this page are estimates. The feed rate is unverified.</p>
</main>
{render_zoom()}
<script src="/x1/vendor/three.min.js"></script>
<script src="/x1/vendor/OrbitControls.js"></script>
<script src="/furniture/viewer.js"></script>
"""
    return page_shell(
        f"{name} — Shop furniture",
        plan["pitch"],
        body,
        "",
    ).replace("<body>", f'<body data-slug="{esc(slug)}">', 1)


def main() -> None:
    designs = []
    for slug in ORDER:
        plan, parts = load(slug)
        if plan["slug"] != slug:
            raise SystemExit(f"{slug} plan slug is {plan['slug']}")
        designs.append({"plan": plan, "parts": parts})
        page = OUT / slug / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(render_design(plan, parts))
        print("wrote", page.relative_to(ROOT))
    (OUT / "index.html").write_text(render_gallery(designs))
    print("wrote furniture/index.html")


if __name__ == "__main__":
    main()
