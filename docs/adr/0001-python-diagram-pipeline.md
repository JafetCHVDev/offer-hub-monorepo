# ADR 0001: Python diagram generation pipeline

- **Status:** Accepted
- **Date:** 2026-10-16
- **Issue:** [#1581](https://github.com/OFFER-HUB/offer-hub-monorepo/issues/1581)

## Context

All 24 diagrams in these docs are Mermaid charts, parsed and laid out in the visitor's browser on every page load (`src/components/shared/MermaidDiagram.tsx`). That has no offline/CI verification: a diagram can silently drift from the source it's supposed to document, and there's no artifact to diff in review. We need a base pipeline that generates static SVGs offline, deterministically, with a CI check that fails when a diagram's source changed but its SVG wasn't regenerated.

## Options considered

| Option | Verdict |
|---|---|
| **Graphviz** (`dot`) via the `graphviz` PyPI wrapper | **Chosen.** Deterministic layout for the same input; native SVG output with real `<g class="node">`/`<g class="edge">` elements we can theme with CSS; no browser needed in CI, just the `dot` binary. |
| `diagrams` (mingrammer) | Built for cloud-architecture diagrams with fixed icon sets (AWS/GCP/K8s); defaults to PNG; icons are baked PNGs, not something a token-driven light/dark stylesheet can restyle. Wrong shape for state machines and flow diagrams. |
| matplotlib | Built for charts/plots (axes, data series), not graph layout. Would mean hand-computing node positions — reinventing what Graphviz already does well. |
| Custom SVG (hand-written templates) | No automatic layout; every new diagram means manually computing coordinates. Doesn't scale past a handful of diagrams. |
| Mermaid CLI (`mmdc`) headless render | Keeps using Mermaid's own renderer (via a headless Chromium), so it inherits Mermaid's theming constraints and needs a full browser in CI, not just a `dot` binary. Doesn't solve the "no offline tooling" problem, just moves the same renderer from the browser to CI. |

## Decision

Use Graphviz through the pinned `graphviz` Python wrapper (`scripts/diagrams/requirements.txt`), with `scour` for SVG optimization afterward.

### Token-driven theming, not two files per diagram

Every node/edge gets a semantic CSS class (`oh-node`, `oh-node--terminal`, `oh-edge`) instead of a literal color. A single `<style>` block, injected after the opening `<svg>` tag, defines those classes purely in terms of `var(--token)` references into `src/app/globals.css` — the same custom properties Mermaid diagrams already read via `src/lib/diagram-theme.ts`. The generated SVG is inlined directly into the page DOM (`src/components/docs/StaticDiagram.tsx`), not loaded through an `<img>` tag, so those `var()` references resolve against the page's real, live tokens. One generated file serves both light and dark mode; there is no second "dark" artifact to keep in sync.

### Determinism

Given the same Graphviz version and the same input graph, `dot`'s layout algorithm produces byte-identical output — verified locally by running the pipeline twice and diffing. The Python package version is pinned in `requirements.txt`; the `dot` binary itself comes from the OS package manager (`apt-get install graphviz` in CI, pinned implicitly by the CI runner image), which is the same tradeoff every tool in this pipeline that wraps a system binary makes.

### CI enforcement

A dedicated `diagrams` job in `.github/workflows/ci.yml` installs Graphviz + the pinned requirements, runs `npm run diagrams`, then runs `git diff --exit-code -- public/diagrams`. A non-empty diff (a diagram module changed without regenerating, or any other drift) fails the job.

## Consequences

- Adding a diagram means writing a small Python module (one file per diagram, per the issue's acceptance criteria), not learning a new DSL — plain Python control flow (loops, data tables) builds the graph, which scales better than copy-pasting Mermaid syntax for large/repetitive diagrams.
- No literal color is ever allowed in a diagram module; every fill/stroke must trace back to a token already in `globals.css`. This is enforced by convention/review today, not a lint rule — a future improvement could grep generated SVGs for literal hex values in the CI job.
- This pipeline intentionally does not touch the 24 existing Mermaid diagrams. Migrating them (if ever desired) is a separate, much larger decision in its own PR.
