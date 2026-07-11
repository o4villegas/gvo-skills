# Frontend aesthetics

> Vendored, self-contained copy for the `fable-flow` skill. Adapted faithfully from the
> `frontend-aesthetics` skill in [jjilli/fable-flow](https://github.com/jjilli/fable-flow) (MIT),
> distilled from https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics
> and pipeline experience. **Cross-reference:** this project's own `rules/web/design-quality.md`
> ("Anti-Template Policy") and `rules/web/performance.md` (Core Web Vitals, bundle budgets) — when
> they conflict, the project rules win; they mostly reinforce each other.

Claude converges on safe, generic frontends unless told not to — the "AI slop" look (Inter on
white, a purple gradient, evenly-timid spacing). Distinctive, polished UI comes from **explicit,
committed choices** on a few dimensions, plus a **visual check** because a green test suite never
sees a layout regression.

## State the design direction before writing code

Pick a cohesive aesthetic that fits the product's *context* and commit to it in one or two
sentences before touching CSS: the mood, the type, the palette, the one motion moment. A security
console, a garden-planning app, and a fintech dashboard should not look like the same starter
template. Decisiveness reads as "designed"; hedging reads as generic.

## The four dimensions to steer explicitly

- **Typography** — the fastest quality signal. Choose distinctive fonts and **avoid Inter, Roboto, Open Sans, Lato, system-ui**. Pair with high contrast (a characterful display against a clean technical sans; add a mono for data). Use **extreme weight ranges** (200 vs 800, not 400 vs 600) and **large size jumps** (3x, not 1.5x). Good picks by mood: code — JetBrains Mono, Space Grotesk; editorial — Fraunces, Playfair Display; distinctive — Bricolage Grotesque, Clash Display; technical — the IBM Plex family.
- **Color** — commit to one cohesive palette via CSS variables. **A dominant color with a sharp accent beats an evenly-distributed, timid spread.** Draw from a real reference (an IDE theme, a cultural aesthetic) rather than a generic wheel. Give the accent a job (brand + one semantic each for ok/attention/alert). Avoid the clichés: purple-on-white gradients, the default Bootstrap/Tailwind blues.
- **Motion** — one well-orchestrated moment beats scattered micro-interactions. Stagger the page-load reveal with `animation-delay`. CSS-only for plain HTML; the Motion library for React when it's already a dependency. Always honor `prefers-reduced-motion`.
- **Backgrounds** — atmosphere, not a flat fill. Layer subtle gradients, a faint texture or grid, a contextual glow that matches the theme. Depth signals care.

The verbatim `<frontend_aesthetics>` steering block is in the cookbook above; paste it into an
implementer prompt when a track's whole job is visual quality.

## "Anyone can use it" is information architecture, not decoration

Intuitiveness comes from structure, not polish. Group navigation by what the user is trying to do
(monitor / review / manage), not by a flat list of every page. Give the app a landing surface that
orients — the one-glance answer to "is everything okay, and what needs me?" — before the detail
views. Friendly labels over jargon. Empty states that teach the next action.

## Pipeline tactics (what makes a redesign land cleanly)

- **Design-system first.** Rewrite the shared tokens and component classes (color, type scale, spacing, the card/row/button/badge vocabulary) before individual pages. When pages already share class names, restyling those classes lifts every page at once — a whole-app redesign becomes one coherent diff instead of N.
- **Preserve the test hooks.** A redesign changes markup; keep the `data-testid`s, ARIA roles, and asserted text stable so the suite stays green through the visual change. Update only the tests whose structure genuinely moved.
- **Self-host fonts for anything local or private.** Bundle the woff2 (e.g. `@fontsource`) instead of a CDN `<link>` — no runtime call home, works offline. Matters for a local-first or privacy-sensitive app.

## Verify what tests can't see

A green suite and a clean build still ship an unconstrained thumbnail, a bar that overflows its
track, text clipped behind a sidebar. **Screenshot the running UI against seeded data** and
actually look at it. A headless browser makes this cheap and scriptable:

```
"/path/to/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=2 --window-size=1440,900 --virtual-time-budget=6000 \
  --screenshot=out.png "http://localhost:<port>/<route>"
```

Serve the built app over a seeded database, capture each key route, and read the images. This is
the frontend equivalent of build-patterns' "one real roundtrip per round" — the reviewer should
do it for any user-facing diff, and report what the pages actually look like, not just that the
build passed.

> **Environment note.** On this Windows + WSL setup, the harness browser tools (chrome-devtools
> MCP, or the built-in preview screenshotter) are the practical way to capture. WSL-served dev
> servers must bind `0.0.0.0` / `--host` to be reachable from the Windows-side browser. WebGL-
> dependent pages need the SwiftShader flags already configured in `.claude.json`.
