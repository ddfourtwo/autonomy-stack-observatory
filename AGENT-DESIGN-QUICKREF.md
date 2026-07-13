# Beoflow — Agent Design Quick Reference

> **GENERATED — DO NOT HAND-EDIT.** Mirrored from the Drafted *Beoflow Design System*
> (Foundations + Anti-Patterns frames) by `beoflow-design-tokens-sync`. To change a value,
> edit the Drafted frame and re-run the sync. Source of truth: the Drafted project, never this file or memory.

## Read this before producing ANY visual / UI artifact

App UI, web UI, **or internal agent-made assets** (Drafted frames, decks, comparison cards, diagrams, mockups, HTML one-pagers). Authoring brand visuals from memory, or shipping an asset that trips an anti-pattern below, is a hard failure.

1. Use the **canonical tokens** below. Never raw hex, never a `.custom(font)` literal, never `muiTheme.ts`, another consumer, or memory.
2. **Peak Orange is the ALERT color only** — never decoration, brand-fill, or a category color. Interactive accent and neutral categories use **Mean Blue**.
3. **Cards** carry a full **1px accent border** (accent also on the icon/label) — never a >1px side-stripe.
4. **Self-check against the NEVER list.** For HTML/web assets run `node beoflow-design/.claude/skills/impeccable/scripts/detect.mjs <file.html>` and fix every hit.

## Always use

- **Canvas:** beoBlacker #121212 base; beoBlack #1E1E1E elevated surface
- **Ink:** beoWhite #F8F6F4 content text
- **Interactive accent:** meanBlue #4A9BB8 — links, toggles, selected state, neutral category color
- **Alert accent:** peakOrange #FF5D29 — ALERT / attention ONLY; never decoration, brand-fill, or category color
- **Type:** Raleway body/headings; IBM Plex Mono labels & units (UPPERCASE); Orbitron rare display; cap families at 3
- **Cards:** 5% white glass surface. The full 1px accent border is ONLY for cards whose border encodes a category (sport/zone/status), with the accent also on the icon/label. For a plain callout/quote use structure (quiet surface, neutral hairline, type), not a colored border + same-hue tint wash. Alert cards use a leading BeoflowIndicator .alert
- **Tokens:** Canonical generated tokens only — never raw hex, never .custom(font) literals, never muiTheme.ts, another consumer, or memory

## Canonical palette

| Token | Hex | Use |
| --- | --- | --- |
| `beoBlacker` | `#121212` | default dark background (base canvas) |
| `beoBlack` | `#1E1E1E` | elevated surface / cards |
| `beoWhite` | `#F8F6F4` | primary text / content ink |
| `peakOrange` | `#FF5D29` | RARE — PRs, achievements, alerts |
| `meanBlue` | `#4A9BB8` | data in range, action links |
| `pimpinPurple` | `#813656` | strength category |
| `biancchiTeal` | `#07B598` | recovery / good / detected; brand green |
| `yoloYellow` | `#FFA60B` | goals, caution, manual |

## Typefaces

| Family | Case | Use |
| --- | --- | --- |
| **Raleway** | mixed | headings (SemiBold), body (Regular), labels, cards |
| **IBM Plex Mono** | uppercase | units, graph labels, buttons, nav, section headers |
| **system-ui** | mixed | all metric values / numbers (data highlight, metric large & secondary) |
| **Orbitron-Black** | uppercase | nav titles, main-view headers, athlete-selector dropdowns |
| **Eurostile Extended Black** | uppercase | explicit special cases only — never part of the structural system |

## Sport colors (one accent per activity type)

`Hybrid #FFCE7A` · `Aerobic #FFDFD4` · `Running #FFAE94` · `Biking #86BED4` · `Skating #8FDBCE` · `Swimming #3593B8` · `Strength #BA688C` · `Other #F8F6F4`

## Zone colors (HR / intensity ramp)

`Z0 (Recovery) #DCDCDC` · `Z1 (Endurance) #20586E` · `Z2 (Tempo) #86BED4` · `Z3 (Threshold) #FFDFD4` · `Z4 (VO2 Max) #FFAE94` · `Z5 (Anaerobic) #FF5D29` · `Z6 (Neuromuscular) #D63A0A` · `Z7 (Max Effort) #834963`

## NEVER (anti-patterns)

| Ban | Severity | Instead |
| --- | --- | --- |
| **Side-stripe accent** — A border-left/border-right (or pseudo-element strip) greater than 1px as a colored accent on a card, row, callout, or alert. | absolute | A full 1px accent border with the accent also on the icon/label; for attention, a leading BeoflowIndicator .alert mark. |
| **Highlight-box callout** — A colored 1px border + a same-hue tint-wash fill on a callout/quote/info box whose border encodes nothing. The generic SaaS 'highlight box'. | beoflow | Use structure: a quiet --surf card with no colored outline, or just type + a neutral hairline. Spend any accent on one element (the source label or a 4x4 mark). Reserve the full 1px accent border for cards whose border encodes a category (sport/zone/status), with the accent also on the icon/label. |
| **Peak Orange as decoration** — Peak Orange used as a brand-fill, a neutral category color, or general decoration (e.g. an orange hero card, an orange column in a comparison). | beoflow | Peak Orange = alert/attention only. Interactive accent and neutral categories use Mean Blue; chrome uses neutral ink. |
| **Em dashes in copy** — An em dash, the HTML entities &mdash;/&#8212;/&#x2014;, or a double hyphen as a sentence separator in body or label copy. | absolute | A comma, colon, semicolon, period, or parentheses. |
| **Hero-metric template** — A big number + tiny label + supporting stats + colored accent as a decorative focal block. | absolute | Label the value in context; let structure carry emphasis, not a giant numeral. |
| **Identical card grid** — Same-sized cards (icon + heading + text) repeated in a uniform grid. Nested cards are always wrong. | absolute | Vary the layout to fit the content, or use a table/list. Cards only when genuinely the best affordance. |
| **Gradient text** — background-clip:text combined with a gradient background. | absolute | A single solid color; emphasis through weight or size. |
| **Decorative glass** — Blur / glassmorphism used as default decoration. | absolute | Glass only on a genuine elevated surface (iOS 26 .glassEffect on cards/sheets), purposeful, never as flourish. |
| **Per-section eyebrow** — A tiny uppercase tracked kicker above every section. | absolute | At most one deliberate kicker. Mono-uppercase is for labels and badges, not a per-section reflex. |
| **Numbered section markers** — 01 / 02 / 03 scaffolding above sections by reflex. | absolute | Numbers only when the section genuinely is an ordered sequence the reader needs. |
| **Marketing buzzwords** — streamline / empower / supercharge / leverage / unleash / seamless / world-class / next-generation / game-changer. | absolute | A specific noun and a verb that says what the product literally does. |
| **Raw hex / font literals** — A hardcoded hex value or a raw .font(.custom("…")) / font-family string in product or showcase surfaces. | beoflow | Canonical tokens: Color.* / BeoflowTypography.* / BeoflowFontName.* (iOS), generated theme modules (web). ds:check enforces it. |
| **Generated raster for a UI graphic** — Using an image generator (fal, Imagen, Midjourney, Recraft, DALL-E) to make a chart, arrow, icon, logo, or data widget. They return clip-art or photographic slop (neon glow, bloom, atmospheric haze, off-token invented colors, fake or garbled data) and hot-link to a URL that rots. | beoflow | These are semantic: hand-author inline SVG/HTML with canonical tokens (open-design frame-data-chart-nyt method for editorial charts). Reserve image generation for genuine photographic atmosphere only, and re-host it, never hot-link a generator URL. |

## Verify before shipping

For any HTML/web asset, run the canonical detector and fix every hit: node beoflow-design/.claude/skills/impeccable/scripts/detect.mjs <file.html>. The detector does not yet decode HTML entities, so also grep for &mdash;/&#8212;/&#x2014; yourself. For app/web product surfaces, npm run ds:check plus the impeccable bans. An asset that trips a ban does not ship, internal or not.

---
_Generated by beoflow-design-tokens-sync from the Drafted Beoflow Design System (drafted-project:704fdbc6-a443-4e70-a922-9d2fde5d9c0e). Edit the frames, not this file._
