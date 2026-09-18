# Mobile notes — meadowlark-models

Source for the Insect column: Critic Models `CRITIQUE-FLYER0-MODELS-v0.md` via `MOBILE-NOTES-INSECT-DRAFT.md` (CEO green-light merge, 2026-09-18).

## Insect / Flyer-0 gaps vs X1 / Burrito

1. Three always-on banners + header + toolbar eat vertical space before the canvas on ~390px — cramped schematic.
2. No aspect-aware initial frame / portrait FOV bump (X1/Burrito have this).
3. Insect missing from success-criteria checklist table.

## Required fixes (Insect)

- **Chrome diet (≤820px):** collapse nature/eng banners into one “why this flyer” chip; keep weapons disclaimer accessible.
- **Canvas:** `min-height` ~48–52dvh; sidebar ≤30–32dvh stacked below.
- **Camera:** portrait FOV bump when aspect < ~0.85; frame whole two-wing schematic on load / Reset.
- **Touch:** OrbitControls damping + screenSpacePanning + explicit TOUCH rotate/dolly-pan; `touch-action: none`; DPR cap ~1.75 on coarse pointers.
- **Catalog chrome:** Flyer-0 / Flyer-1 Dual-pair / Flyer-2 Resonant piezo stay a compact 3-cell control — do not stack three fat cards above the canvas.

## Success criteria checklist

| Criterion | Burrito | X1 | Insect |
|-----------|---------|-----|--------|
| viewport meta | yes | yes | yes |
| canvas fills usable viewport @ 390px | yes | yes | **required** |
| OrbitControls touch orbit + pinch | yes | yes | **required** |
| initial camera frames whole model on phone | yes | yes | **required** |
| HUD stacks / doesn’t cover scene center | yes | yes | **required** |
| chrome diet (banners compact on narrow) | — | — | **required** |
| catalog switcher usable on narrow | — | — | **required** when chrome ships |
