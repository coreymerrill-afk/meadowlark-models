#!/usr/bin/env python3
"""Write /furniture/index.html and /furniture/<slug>/index.html from furniture-data."""

from __future__ import annotations

import html
import json
import re
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
    "plant-stand",
    "tv-console",
    "floating-shelves",
    "cat-enclosure",
    "potting-bench",
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
    "cable_slots": "Cable slots",
    "tv_max_kg": "TV weight limit",
    "pitch": "Shelf pitch",
    "shelf_height": "Shelf height",
    "box_w": "Litter box width",
    "box_d": "Litter box depth",
    "entry_w": "Entry width",
    "entry_h": "Entry height",
    "sill": "Door sill",
    "vents": "Vents",
    "hutch_top": "Hutch top",
    "hutch_depth": "Hutch depth",
    "hutch_shelf_z": "Hutch shelf height",
    "foot": "Foot clearance",
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
    "frame": "Frame",
    "hanger": "Hanger",
}

TOGGLE_ORDER = ["drawer", "casters", "cleat", "hanger"]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def public_text(value: str) -> str:
    """Drop internal note names from copy that is shown on the page."""
    text = str(value)
    text = text.replace(
        "see CUT-SPEED-RESEARCH.md",
        "taken from reported speeds for a 120 W-class diode",
    )
    text = text.replace("CUT-SPEED-RESEARCH.md", "reported diode speeds")
    text = text.replace("SHORTLIST.md: ", "")
    text = re.sub(r"SHORTLIST\.md\s+R\d+", "a survey of similar pieces", text)
    text = text.replace("(not in SHORTLIST.md)", "")
    text = text.replace("is not in SHORTLIST.md", "was not part of that price survey")
    text = text.replace("from SHORTLIST.md", "from a survey of similar pieces for sale")
    text = text.replace("SHORTLIST.md", "a survey of similar pieces for sale")
    text = text.replace("ASSUMPTION :", "Assumption:")
    text = text.replace("ASSUMPTION:", "Assumption:")
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


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


def machine_hours(h) -> str:
    return f"{float(h):.1f} h"


def sheet_machine_minutes(plan: dict, sheet: dict, key: str) -> float:
    profit = plan["profit"]
    scenario = profit["machine_time"]["scenarios"][key]
    path = float(sheet["cut_path_m"])
    total = float(profit["cut_path_m"]) or 1.0
    rate = float(scenario["effective_mm_min"])
    cut = path * 1000.0 / rate if rate else 0.0
    travel = float(scenario.get("travel_min") or 0) * (path / total)
    setup = float(scenario.get("setup_min") or 0) / max(int(plan["sheet_count"]), 1)
    return cut + travel + setup


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
    elif "interior_width" in dims and "interior_depth" in dims and "interior_height" in dims:
        bits.append(
            f"inside {mm(dims['interior_width'])} × {mm(dims['interior_depth'])} × {mm(dims['interior_height'])} mm"
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
    if "top_tier_depth" in dims:
        bits.append(f"top tier {mm(dims['top_tier_depth'])} mm deep")
    if "shelf_pitch" in dims and "shelf_slot_rows" not in dims:
        bits.append(f"shelves {mm(dims['shelf_pitch'])} mm apart")
    if "bay_clear_width" in dims:
        bits.append(f"each bay {mm(dims['bay_clear_width'])} mm wide")
    if "shelf_lengths" in dims:
        lengths = ", ".join(mm(n) for n in dims["shelf_lengths"])
        bits.append(f"shelf lengths {lengths} mm")
    if "shelf_height" in dims:
        bits.append(f"each shelf box {mm(dims['shelf_height'])} mm tall")
    if "worktop_height" in dims:
        bits.append(f"worktop at {mm(dims['worktop_height'])} mm")
    if "foot_clearance" in dims:
        bits.append(f"{mm(dims['foot_clearance'])} mm clear under the feet")
    if "upper_shelf_depth" in dims:
        bits.append(f"upper shelf {mm(dims['upper_shelf_depth'])} mm deep")
    if "bay_width" in dims:
        bits.append(f"lower bay {mm(dims['bay_width'])} mm wide")
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
    if group == "hanger":
        return "Hangers", True
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
        typical = plan["profit"]["machine_hours_mid"]
        cards.append(
            f"""<a class="card" href="/furniture/{esc(slug)}">
  <div class="card-media">
    <img src="/furniture/thumbs/{esc(slug)}.png" width="1280" height="666" alt="3D preview of the {esc(plan['name'])}, assembled in plywood." />
  </div>
  <div class="card-body">
    <h2>{esc(plan['name'])}</h2>
    <p class="pitch">{esc(plan['pitch'])}</p>
    <dl class="stats">
      <div class="wide"><dt>Size</dt><dd>{esc(size_phrase(plan['dimensions_mm']))}</dd></div>
      <div><dt>Sheets</dt><dd>{esc(sheet_word(sheets))}</dd></div>
      <div><dt>Mid price</dt><dd>{esc(money_short(price))}</dd></div>
      <div><dt>Machine time</dt><dd>{esc(machine_hours(typical))} typical</dd></div>
    </dl>
  </div>
</a>"""
        )
    body = f"""<header class="doc-header">
  <p class="crumbs"><a href="/">All models</a></p>
  <h1>Shop furniture</h1>
  <p class="lede">Twelve flat-pack designs in 18 mm plywood, each cut from 4×8 sheets. Open a piece for the model, the cut sheets, and the build. Mid prices are planning estimates, not quotes.</p>
</header>
<main class="wrap">
  <div class="gallery">
    {chr(10).join(cards)}
  </div>
  <p class="site-foot">Meadowlark Models. Machine time is an estimate from reported 120 W-class diode speeds. One timed scrap cut will replace it.</p>
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
        "Twelve flat-pack plywood designs, from a bookcase and a dog crate to floating shelves and a potting bench. Cut sheets, a 3D model, and a build order for each.",
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
    slow_h, typical_h, best_h = profit["machine_time"]["diode_low_mid_high_hours"]
    commercial_h = profit["machine_time"]["commercial_laser"]["hours_sourced_co2"]
    blocks = []
    for sheet in plan["sheets"]:
        n = int(sheet["sheet"])
        title = f"Sheet {n} of {count}"
        png = f"/furniture-data/{plan['slug']}/{sheet['png']}"
        path_m = float(sheet["cut_path_m"])
        best_m = sheet_machine_minutes(plan, sheet, "high")
        typical_m = sheet_machine_minutes(plan, sheet, "mid")
        slow_m = sheet_machine_minutes(plan, sheet, "low")
        path_text = f"{path_m:.2f}".rstrip("0").rstrip(".")
        alt = (
            f"{title} for the {plan['name']}. "
            f"Each part is labelled on a 1220 by 2440 mm plywood sheet."
        )
        blocks.append(
            f"""<article class="sheet">
  <div class="sheet-head">
    <h3>{esc(title)}</h3>
    <p class="sheet-meta">{esc(str(sheet['part_count']))} parts on this sheet. They cover {esc(sheet['coverage_pct'])}% of a 1220 × 2440 mm sheet. Cut path {esc(path_text)} m. About {esc(fmt_min(typical_m))} at the typical diode estimate (best {esc(fmt_min(best_m))}, slow {esc(fmt_min(slow_m))}).</p>
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
  <p>Machine time for the whole unit: about {esc(machine_hours(best_h))} best, {esc(machine_hours(typical_h))} typical, {esc(machine_hours(slow_h))} slow. Based on reported 120 W-class diode speeds, multiple passes at 18 mm. One timed scrap cut will replace this.</p>
  <p>A commercial CO2 flatbed is about {esc(machine_hours(commercial_h))} in the sourced case. That number is an assumption, not a cut on this machine.</p>
  <p>Sheet 1 carries a fit-test coupon: cut it first and try the tab in the slot before you cut the rest. Hover or tap a part below to light it in the model.</p>
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


DIODE_WEAR_PER_HOUR = 1.70

DIODE_COLUMNS = (
    ("high", "Best"),
    ("mid", "Typical"),
    ("low", "Slow"),
)

COMMERCIAL_COLUMNS = (
    ("commercial_co2", "Commercial CO2"),
    ("what_if_10x", "What-if 10×"),
    ("what_if_20x", "What-if 20×"),
)

CALC_SCENARIOS = (
    ("mid", "Typical diode", False),
    ("high", "Best diode", False),
    ("low", "Slow diode", False),
    ("commercial_co2", "Commercial CO2 (assumption)", True),
    ("what_if_10x", "What-if 10× (assumption)", True),
    ("what_if_20x", "What-if 20× (assumption)", True),
)


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


def rate_cells(rates: dict, columns: tuple[tuple[str, str], ...], field: str, kind: str) -> str:
    cells = []
    for key, _label in columns:
        value = float(rates[key][field])
        if kind == "hours":
            text = hours(value)
        elif kind == "pct":
            text = f"{value:.1f}%"
        else:
            text = money(value)
        cls = "num neg" if kind == "money" and value < 0 else "num"
        cells.append(f'<td class="{cls}">{esc(text)}</td>')
    return "".join(cells)


def rate_table(rates: dict, columns: tuple[tuple[str, str], ...], caption: str) -> str:
    heads = "".join(f'<th class="num">{esc(label)}</th>' for _key, label in columns)
    rows = [
        ("Machine time", "machine_hours", "hours"),
        ("Cost per unit", "cogs", "money"),
        ("Gross margin", "gross_margin", "money"),
        ("Gross margin %", "gross_margin_pct", "pct"),
        ("Net after fees and labor", "net_after_fees_and_labor", "money"),
        ("Gross profit per machine hour", "gross_margin_per_machine_hour", "money"),
        ("Net profit per machine hour", "net_after_fees_and_labor_per_machine_hour", "money"),
    ]
    body = "\n    ".join(
        f"<tr><th>{esc(label)}</th>{rate_cells(rates, columns, field, kind)}</tr>"
        for label, field, kind in rows
    )
    return f"""<div class="table-wrap">
<table>
  <caption>{caption}</caption>
  <thead><tr><th></th>{heads}</tr></thead>
  <tbody>
    {body}
  </tbody>
</table>
</div>"""


def render_profit(plan: dict) -> str:
    profit = plan["profit"]
    costs = profit["cost_per_unit_low_mid_high"]
    rates = profit["profit_per_machine_hour_at_mid_price"]
    machine = profit["machine_time"]
    fixed = float(profit["finish_cost"]) + float(profit["packaging_cost"])
    scenarios = []
    options = []
    for key, label, assumption in CALC_SCENARIOS:
        block = machine["scenarios"][key]
        wear = float(block["operating_cost_per_hr"]) if "operating_cost_per_hr" in block else DIODE_WEAR_PER_HOUR
        scenarios.append(
            {
                "id": key,
                "hours": rates[key]["machine_hours"],
                "wearPerHour": wear,
                "assumption": assumption,
            }
        )
        selected = " selected" if key == "mid" else ""
        options.append(f'<option value="{esc(key)}"{selected}>{esc(label)}</option>')
    calc = {
        "sheetCost": profit["sheet_cost_mid"],
        "hardwareCost": profit["hardware_cost"],
        "price": profit["at_price"]["mid"]["price"],
        "laborRate": 25,
        "laborHours": profit["labor_hours"],
        "fixedCost": round(fixed, 2),
        "feeRate": 0.10,
        "defaultScenario": "mid",
        "scenarios": scenarios,
    }
    bands = "".join(
        f'<td class="num">{esc(money(profit["at_price"][band]["price"]))}</td>' for band in ("low", "mid", "high")
    )
    cost_cells = "".join(f'<td class="num">{esc(money(profit["at_price"]["mid"]["cogs_mid"]))}</td>' for _ in range(3))
    hours_cells = "".join(f'<td class="num">{esc(hours(profit["machine_hours_mid"]))}</td>' for _ in range(3))
    commercial_heads = tuple((key, f"{label} (assumption)") for key, label in COMMERCIAL_COLUMNS)
    diode_note = (
        "Based on reported 120 W-class diode speeds, multiple passes at 18 mm. "
        "One timed scrap cut will replace this."
    )
    return f"""<div class="callout">
  <strong>Estimates and assumptions.</strong> Every dollar figure on this page is a planning estimate, not a quote and not a promise. Sheet price, hardware, fees, labor, and machine wear are assumptions. Machine time is based on reported 120 W-class diode speeds, multiple passes at 18 mm. One timed scrap cut will replace this.
</div>
<h3>Diode machine time</h3>
<p>These three columns are the same unit at the mid selling price. Best, typical, and slow are the diode estimates. {esc(diode_note)}</p>
{rate_table(rates, DIODE_COLUMNS, "At the mid selling price. Best is the fast diode case, typical is the planning case, slow is the cautious case.")}
<h3>Commercial laser (assumptions)</h3>
<p>These columns are assumptions, not a cut on this machine. {esc(public_text(machine['commercial_laser']['label']))}</p>
{rate_table(rates, commercial_heads, "Assumption only. Commercial CO2 is the sourced case. The 10× and 20× columns are what-if speeds, not a measured machine.")}
<h3>Selling price, at the typical diode time</h3>
<div class="table-wrap">
<table>
  <caption>Gross margin and net use the mid cost per unit (${esc(f'{float(costs[1]):.2f}')}) and the typical diode time, {esc(hours(profit['machine_hours_mid']))}. A low sheet price would put the cost at {esc(money(costs[0]))}; a high sheet price, {esc(money(costs[2]))}.</caption>
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
<p>{esc(public_text(profit['note_machine_time']))}</p>
<p class="fine">{esc(public_text(profit['assumptions']))}</p>
<p class="fine">Where the price band came from: {esc(public_text(profit['price_band_source']))}</p>
<h3>Try your own numbers</h3>
<p>Change the sheet cost, hardware, selling price, labor rate, or machine time. Finish ({esc(money(profit['finish_cost']))}) and packaging ({esc(money(profit['packaging_cost']))}) stay put. Machine wear follows the machine-time choice: {esc(money(DIODE_WEAR_PER_HOUR))} per hour on the diode estimates, {esc(money(8))} per hour on the commercial assumptions. Fees stay at 10% of the selling price. Labor uses the planned {esc(hours(profit['labor_hours']))} at the rate you type.</p>
<div class="calc">
  <label>Sheet cost, $ <input id="sheet-cost" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['sheet_cost_mid'])}" /></label>
  <label>Hardware cost, $ <input id="hardware-cost" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['hardware_cost'])}" /></label>
  <label>Selling price, $ <input id="selling-price" inputmode="decimal" type="number" min="0" step="0.01" value="{esc(profit['at_price']['mid']['price'])}" /></label>
  <label>Labor rate, $ per hour <input id="labor-rate" inputmode="decimal" type="number" min="0" step="0.5" value="25" /></label>
  <label>Machine time <select id="machine-scenario">{''.join(options)}</select></label>
</div>
<div class="calc-out" id="calc-out" aria-live="polite"></div>
<p class="fine">Still an estimate. {esc(diode_note)} The commercial rows are assumptions, not a cut on this machine.</p>
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
    safety = "\n".join(f"<li>{esc(public_text(item))}</li>" for item in plan["safety"])
    unverified = "\n".join(f"<li>{esc(public_text(item))}</li>" for item in plan["unverified"])
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
  <p class="size-line">{esc(size_sentence(plan['dimensions_mm']))} {esc(sheet_word(sheets))}. Mid retail price {esc(money_short(price))}, an estimate. Typical machine time {esc(machine_hours(plan['profit']['machine_hours_mid']))}.</p>
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
  <div id="model-stage">
    <div class="stage">
      <div id="canvas-wrap">
        <div id="three-loading">Loading the model…</div>
        <div id="three-error" hidden></div>
      </div>
      <p id="rotate-hint" class="rotate-hint" hidden>Rotate your phone for a wider view.</p>
    </div>
    <div class="tool-bar">
      <label class="explode" for="explode">Exploded
        <input id="explode" type="range" min="0" max="100" value="0" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-valuetext="0 percent exploded" />
      </label>
      {render_toggles(parts)}
      <button type="button" class="ghost" id="btn-reset">Reset view</button>
      <button type="button" class="ghost" id="btn-fullscreen">Full screen</button>
      <button type="button" id="btn-exit-fs" hidden>Exit</button>
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
  <p class="site-foot">Meadowlark Models. Numbers on this page are estimates. Machine time is based on reported 120 W-class diode speeds. One timed scrap cut will replace it.</p>
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
