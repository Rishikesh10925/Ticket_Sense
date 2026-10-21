# Usability and accessibility pass (Week 10)

- Owner: Aashritha. Roadmap Week 10: "usability pass across the three roles; accessibility basics".
- Scope: the end-user, department-engineer and admin screens in `frontend/src`.

## Automated check

Command (oxlint's JSX accessibility rules, no extra dependency):

```bash
cd frontend
npx oxlint --jsx-a11y-plugin -A all -W jsx-a11y/label-has-associated-control \
  -W jsx-a11y/click-events-have-key-events -W jsx-a11y/no-static-element-interactions \
  -W jsx-a11y/alt-text -W jsx-a11y/anchor-is-valid \
  -W jsx-a11y/no-noninteractive-element-interactions -W jsx-a11y/control-has-associated-label src
```

19 warnings before the pass, 9 after.

### Fixed

| Where | Role | Problem | Fix |
|---|---|---|---|
| `components/ChatWidget.tsx` | engineer, admin | Contacts opened only with a mouse click on a list item | Each contact is a `<button>` |
| `components/NotificationBell.tsx` | admin | Pending approvals opened only with a mouse click | Each item is a `<button>` |
| `pages/admin/AdminApprovals.tsx` | admin | Ticket subject was a clickable `<strong>` | A `<button class="link-button">` |
| `pages/admin/AdminErrorBudget.tsx` | admin | Empty table header for the actions column | Screen-reader-only "Actions" |
| `pages/admin/AdminEngineers.tsx` | admin | Same | Same |

A shared `.sr-only` class was added to `styles/tokens.css`. The new buttons keep their
previous look (CSS reset in the component stylesheets) and get the global
`:focus-visible` ring.

### Kept on purpose (the 9 remaining warnings)

| Where | Why it stays |
|---|---|
| `ConfirmDialog.tsx`, `EndUserHome.tsx` (new-ticket drawer) | Clicking the dimmed backdrop closes the dialog. Keyboard users close it with Escape (handled in both) and with the Cancel or Close button. |
| `charts/DonutChart.tsx` | Hover only highlights a legend entry; the values are always shown as text. |

`autoFocus` on the login email field and the chat message box is also kept: both are the
single obvious first input on their screen.

Focus outlines: the three `outline: none` rules in the stylesheets all replace the outline
with a visible border and focus ring, so no focus indicator is lost.

## Manual walk-through: To be done (needs a person)

These cannot be checked from the code and are left for Aashritha:

- [ ] Keyboard only, each role: log in, reach every main screen, open a ticket, act on it (end user: create a ticket; engineer: accept, edit or escalate a draft in each lane; admin: open an approval, change a threshold), log out.
- [ ] Screen reader smoke test (Windows Narrator or NVDA) on the login page, the engineer queue and the ticket detail page.
- [ ] 200% browser zoom and a 360 px wide window on the same three pages.
- [ ] Note anything confusing in wording or flow for the three roles before the study (Week 11).

Record findings below with the date and who checked.

| Date | Checked by | Finding | Fixed? |
|---|---|---|---|
| | | | |
