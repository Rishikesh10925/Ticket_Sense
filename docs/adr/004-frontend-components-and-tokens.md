# ADR 004: Frontend component library and design tokens

- Status: accepted
- Date: 2026-10-19
- Owner: Aashritha

## Context

Roadmap Week 1 asks the team to "choose the component library and design tokens".
The V1 frontend already has a small in-house component set (`frontend/src/components/`:
Button, Card, FormField, Toast, ConfirmDialog, Timeline, ConfidenceIndicator, charts)
built on CSS custom properties in `frontend/src/styles/tokens.css`, with a dark theme.
The blueprint lists TanStack Query for data fetching.

Options considered:

| Option | For | Against |
|---|---|---|
| Keep in-house components + tokens | Already built, typed, themed, accessible states done; zero new dependencies | We maintain it ourselves |
| MUI / Chakra | Large catalogue | Heavy bundle; restyling to match the existing look costs more than it saves; a migration in the middle of the research weeks |
| shadcn/ui + Tailwind | Modern, copy-in components | Would mean adding Tailwind and rewriting every page's CSS |

## Decision

1. **No external component library.** Keep the in-house components and the CSS
   custom-property tokens in `styles/tokens.css` as the single source of colour, spacing,
   radius and type. New V2 screens (workbench lanes, annotation tool, error-budget
   screen) compose these components.
2. **Lane tokens are added** in Week 4 as `--lane-fast`, `--lane-assisted`,
   `--lane-escalate` (each with a `-bg`), defined for both light and dark themes. Lane
   badges always pair colour with a shape (●, ◐, ○).
3. **TanStack Query is adopted in Week 4** for the queue and workbench, where polling
   and cache invalidation after a review action matter. Existing pages keep their
   `fetch` hooks until they are touched.

## Consequences

- No bundle growth or restyle; frontend effort goes to the research screens (the
  roadmap says the dashboard is not to be overbuilt).
- Accessibility basics (focus states, contrast in both themes, labels) are our
  responsibility; checked in the Week 10 usability pass.
