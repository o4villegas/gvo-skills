# Recon Checklist — What to Read Before Diagnosing

This checklist ensures you have empirical evidence before forming opinions.
You are running INSIDE the project via Claude Code CLI — use direct filesystem commands.

---

## Environment Check (Always First)

- [ ] Confirm codebase location: Linux FS (`~/...`) vs Windows mount (`/mnt/c/...`)
  - If on `/mnt/c/`, flag as P1 performance issue (slow file watchers, slow HMR)
- [ ] Check available tools: `which node npm npx wrangler git python3`
- [ ] Identify running dev servers: `ss -tlnp 2>/dev/null || lsof -i -P -n 2>/dev/null | grep LISTEN`
- [ ] Note Node version: `node --version` (affects available APIs)
- [ ] Check project root: `ls -la` — identify entry points, configs, READMEs

---

## Frontend Recon

### Project Structure (Always First)
- [ ] `find . -name "*.tsx" -o -name "*.jsx" -o -name "*.vue" -o -name "*.svelte" | wc -l` — component count
- [ ] `ls src/app/routes/ 2>/dev/null || ls src/routes/ 2>/dev/null || ls pages/ 2>/dev/null` — route count
- [ ] Identify framework: React/Vue/Svelte/Angular/vanilla
- [ ] Identify meta-framework: Next.js/Remix/Nuxt/SvelteKit/Astro/React Router v7
- [ ] Identify styling: Tailwind/CSS Modules/styled-components/vanilla CSS/Sass
- [ ] Identify component library: shadcn/MUI/Radix/Headless UI/custom/none

### Root & Layout Files
- [ ] Root layout / shell component (global nav, footer, providers)
- [ ] Theme/design token configuration (`tailwind.config.*`, CSS variables file, `theme.ts`)
- [ ] Global styles file (`globals.css`, `index.css`, `app.css`)
- [ ] Font loading configuration

### Navigation & Routing
- [ ] Route definitions (file-based routing tree or route config)
- [ ] Navigation component(s) — header, sidebar, bottom nav, tabs
- [ ] Active state styling on nav items
- [ ] Route transition / page transition animations (if any)
- [ ] Protected route handling (auth guards, redirects)
- [ ] 404 / catch-all route: `find . -name "not-found*" -o -name "404*" -o -name "*catch*" | head -5`

### Core Page Components (Read 3-5 Most Complex)
- [ ] Primary dashboard or home screen
- [ ] A data-heavy list/table view
- [ ] A form-heavy page (settings, create/edit)
- [ ] A detail/profile view
- [ ] Any page with real-time or dynamic content

### Shared Components (Sample the Library)
- [ ] `ls src/components/ui/ 2>/dev/null || ls src/components/ 2>/dev/null` — what exists
- [ ] Button variants (primary, secondary, destructive, ghost, icon)
- [ ] Input / form field components
- [ ] Card / container components
- [ ] Modal / dialog / drawer / sheet
- [ ] Toast / notification / alert
- [ ] Loading indicators (spinner, skeleton, progress bar)
- [ ] Empty state components
- [ ] Error boundary / error display components

### Interaction Pattern Searches
```bash
# Run these searches to gauge interaction quality
grep -r "transition\|animate\|motion\|framer" src/ --include="*.tsx" --include="*.css" -l
grep -r "skeleton\|loading\|Suspense\|pending" src/ --include="*.tsx" -l
grep -r "swipe\|drag\|pan\|pinch\|touch\|gesture" src/ --include="*.tsx" -l
grep -r "optimistic\|useTransition\|startTransition" src/ --include="*.tsx" -l
grep -r "aria-\|role=" src/ --include="*.tsx" -l | wc -l
grep -r "dark:" src/ --include="*.tsx" --include="*.css" -l | wc -l
```

### Assets & Media
- [ ] Image handling: `<img>`, `<Image>`, lazy loading, srcset, WebP/AVIF
- [ ] Icon system: `grep -r "lucide\|heroicon\|icon" package.json`
- [ ] Favicon, OG images, app icons: `ls public/ 2>/dev/null`

---

## Backend Recon (UX-Impacting Only)

### API Shape
- [ ] Sample 2-3 API route handlers or server functions
- [ ] Response envelope pattern (error/loading/pagination metadata?)
- [ ] Error response format (structured codes vs generic 500s)
- [ ] Pagination approach (offset, cursor, page-based)

### Auth & Session
- [ ] Auth mechanism (cookie session, JWT, OAuth provider)
- [ ] Protected route middleware
- [ ] Session expiry handling (graceful re-auth or hard redirect?)

### Data & Performance
- [ ] Database query patterns (N+1? eager loading? streaming?)
- [ ] Caching headers or cache strategy
- [ ] Image/asset CDN configuration

---

## Infrastructure Recon

### Build & Bundle
- [ ] Build tool: `cat package.json | grep -E "vite|webpack|esbuild|turbo"`
- [ ] Code splitting: `grep -r "lazy\|dynamic\|import(" src/ --include="*.tsx" -l`
- [ ] Bundle analysis: `npm run build 2>&1 | tail -20` (if safe to run)

### Deployment
- [ ] Target: `ls wrangler.toml vercel.json netlify.toml 2>/dev/null`
- [ ] Service worker / PWA: `ls public/manifest* public/sw* 2>/dev/null`
- [ ] Edge vs origin rendering

---

## Recon Output (Internal Working Notes)

After scanning, produce this summary for your own use in Phase 2:

```
## Recon Summary
- Stack: [framework] + [styling] + [component lib] + [backend]
- Deployment: [target platform]
- Component count: ~N shared components
- Route count: ~N routes
- Design tokens: yes/no — [where defined]
- Animation system: none / CSS only / Framer Motion / custom
- Loading patterns: spinner / skeleton / none / mixed
- Accessibility posture: strong / partial / minimal / absent
- Key files for diagnostic: [list the 10-15 most important files]
```

Do NOT present this summary to the user — it's your working notes for Phase 2.
