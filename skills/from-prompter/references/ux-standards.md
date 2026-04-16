# UX Standards for Prompt Generation

When from-prompter generates a prompt in the **UI/UX Polish** category — or any **New Feature Build** with a frontend component — inject the relevant standards below into the prompt's "Best Practices & Recommendations" section.

Don't dump the whole file. Pick the 5-8 most relevant items based on the specific task.

---

## Design Token Foundation

Every UI prompt should establish (or reference existing) tokens:

```
- Colors: primary, secondary, accent, surface, background, text, muted, border, destructive, success
- Spacing: 4px base unit (4, 8, 12, 16, 24, 32, 48, 64)
- Typography: heading (3 sizes), body, small, mono — with line-height and letter-spacing
- Radii: sm (6px), md (12px), lg (16px), full
- Shadows: sm (subtle lift), md (card elevation), lg (modal/dropdown)
- Transitions: fast (150ms), normal (250ms), slow (400ms) — ease-out for enters, ease-in for exits
```

If the codebase already has tokens, reference them. If not, include a minimal set in the prompt.

---

## Interaction Standards (2026 Benchmark)

### Feedback Latency
- Every user action gets visual feedback within 100ms
- Sub-400ms response for all interactions (Doherty Threshold)
- If >400ms, show skeleton/shimmer — never a blank screen or generic spinner

### Loading States (required for every data-fetching component)
- Skeleton screens that match the layout of the loaded content
- Shimmer animation on skeletons (subtle, not distracting)
- Optimistic UI for mutations — show success immediately, reconcile in background

### Transitions
- Page transitions: 250ms ease-out, use shared-element transitions where possible
- Component mount/unmount: fade + slight translate (8-12px)
- Hover states: 150ms, subtle scale (1.02-1.05) or background shift
- Never snap — always animate between states

### Touch Targets
- Minimum 44×44px (WCAG) for interactive elements
- Thumb-zone aware: primary actions in bottom 40% of mobile viewport
- Adequate spacing between adjacent targets (min 8px gap)

### Empty & Error States
- Every list/feed needs an empty state with illustration + action
- Error states: specific message + retry action + fallback content if possible
- Never show raw error codes to users

---

## Visual Design Patterns

### Spacing
- Use the 4px grid consistently — no magic numbers
- Sections: 32-48px between major groups
- Cards: 16-24px internal padding
- Inline elements: 8-12px gaps

### Typography
- Max 2 font families (1 heading, 1 body — or 1 for everything)
- Clear size hierarchy: at least 3 distinct heading sizes
- Body text: 16px minimum on mobile, 1.5 line-height
- Muted text for secondary info (0.6 opacity or dedicated muted color)

### Color
- One ownable brand color — not generic blue
- 60/30/10 rule: 60% neutral, 30% secondary, 10% accent
- Ensure 4.5:1 contrast ratio on all text (AA minimum)
- Dark mode: don't just invert — use dark surfaces with adjusted saturation

### Cards & Containers
- Consistent card styling across the app (same radius, shadow, padding)
- Bento grid for dashboards (varied card sizes creating visual rhythm)
- Clear visual boundaries between content groups (Law of Common Region)

---

## Accessibility Essentials

Always include in UI prompts:
- Semantic HTML (nav, main, section, article, button — not div for everything)
- ARIA labels on interactive elements without visible text
- Keyboard navigation: all interactive elements focusable, logical tab order
- Focus indicators: visible, styled to match design system (not browser default)
- `prefers-reduced-motion`: disable non-essential animations
- Skip links for keyboard users
- Alt text on all images

---

## Responsive Patterns

- Mobile-first CSS (min-width breakpoints)
- Fluid typography: `clamp(1rem, 2.5vw, 1.25rem)` instead of fixed sizes
- Container queries for component-level responsiveness
- Safe area handling for notched/dynamic-island devices: `env(safe-area-inset-*)`
- One-handed reachability on mobile: avoid top-of-screen primary actions

---

## Emotional Design

- Celebration moments: animate success states (confetti, check animations, pulse)
- Contextual microcopy: not "Error 422" but "That email's already in use — try another?"
- Progressive disclosure: show complexity only when users are ready
- Brand personality in key touchpoints (onboarding, empty states, confirmations)
- Zero dark patterns: no trick opt-ins, no shame-based copy, no hidden unsubscribe

---

## Code Quality for UX

Include in prompts for any significant UI work:
- Component variants: every component handles loading, error, empty, and success states
- Design tokens as CSS variables (not hardcoded values)
- Animation system: shared transition utilities, not per-component ad-hoc
- Co-located styles (Tailwind classes or CSS modules alongside components)
- TypeScript for all component props (no `any`)

---

## When to Apply

| Task Type | What to Inject |
|-----------|---------------|
| UI/UX Polish (full) | All relevant sections above |
| New Feature with UI | Interaction Standards + Accessibility + relevant Visual patterns |
| Bug fix with UI impact | Only the specific standard the fix should maintain |
| API/backend only | Skip this file entirely |

Pick standards that are **actionable for the specific task**. A prompt to "add a date picker" doesn't need the full emotional design section — it needs touch targets, keyboard navigation, and transition standards.
