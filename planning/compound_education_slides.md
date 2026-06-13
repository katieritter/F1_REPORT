# Tyre Compound Education Slides — Concept

A short educational insert (2–3 slides) explaining what F1 tyre compounds actually
are, for either report (or a standalone explainer). Adds depth beyond abstract
SOFT/MEDIUM/HARD labels and ties into the existing relative-compound caveat.
Reuses the pit-wall design system. Domain notes belong in `knowledge_base/`.

## Slide 1 — Anatomy of an F1 Tyre
- Cross-section visual: **tread compound** (the part everyone means by "compound")
  sits on top of the **casing/plies**, **steel belts**, and **bead**.
- Teaching point: the compound is only the rubber tread blend, not the whole tyre.
- Compound ingredients: natural + synthetic **rubber polymers**, **carbon black**
  and **silica** (reinforcing fillers), **sulfur** (vulcanisation / cross-linking),
  **oils/plasticisers**, antioxidants. Blend ratios set hardness, grip, thermal
  range and wear. (Exact Pirelli recipes are confidential.)

## Slide 2 — The Compound Spectrum (C1–C6)
- Gradient bar from **hardest/most durable** to **softest/grippiest**.
- Trade-offs across the range: grip ↑ as you go softer, durability ↓, and the
  **working-temperature window** shifts (softer = lower/narrower).
- Failure modes to illustrate: **graining** (surface tears when too cold/sliding),
  **blistering** (sub-surface overheating), **thermal degradation**, abrasive wear.
- ⚠️ VERIFY the exact current range/naming for the report's season (Pirelli
  expanded the softest end in recent years; confirm whether 2025 is C1–C6 / C0–C6
  and which is softest before publishing).

## Slide 3 — Relative Labelling + Wets
- How Pirelli selects **three** of the range each weekend and re-labels them
  SOFT / MEDIUM / HARD for that event → why a "soft" differs race to race.
  (This is the caveat the strategy reports already flag — now explained.)
- Slick vs **intermediate** vs **full wet**: tread patterns and water-clearance;
  slick = no tread (max contact patch); inters/wets disperse water, with crossover
  decisions on a drying track.

## Build notes
- Pure layout/illustration pages — likely hand-built SVG/CSS cross-section and a
  CSS gradient spectrum bar (no data charts needed), or simple matplotlib diagrams.
- Could live as an appendix in the season report, or its own short explainer deck.
