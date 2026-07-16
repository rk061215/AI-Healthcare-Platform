# UX Review: AI Healthcare Follow-up Assistant

**Version:** v1.0.0-rc.1  
**Date:** July 2026  
**Reviewer:** Automated UX Audit

---

## 1. Loading Indicators

| Page / Component | Loading State | Details |
|---|---|---|
| Login | ✅ Yes | Spinner in submit button, button disabled |
| Register | ✅ Yes | Spinner in submit button, button disabled |
| Patient Chat | ✅ Yes | `LoadingState` for history, `TypingIndicator` during AI response, spinner in send button |
| Patient Reports | ✅ Yes | `LoadingState` while fetching list, progress bar for upload, `LoadingState` for detail modal |
| Patient Medicines | ✅ Yes | `LoadingState` while fetching, abort controller for cleanup |
| Patient Dashboard | ❌ **Missing** | No loading state — shows `--` placeholders synchronously |
| Patient Appointments | ❌ **Missing** | No loading state — static placeholder page |
| Patient Emergency | ❌ **Missing** | No loading state — static page, no async call wrapper |
| Doctor Dashboard | ❌ **Missing** | No loading state — shows `--` placeholders synchronously |
| Doctor Patients | ❌ **Missing** | No loading state — static placeholder page |
| Doctor Alerts | ❌ **Missing** | No loading state — static placeholder page |
| Doctor Appointments | ❌ **Missing** | No loading state — static placeholder page |
| Demo Page | ✅ Partial | Upload spinner exists, chat loading exists; no skeleton for scenario list loading |

**Assessment:** Pages with actual API calls (chat, reports, medicines) have loading states. Dashboard and placeholder pages lack them because they don't make async calls yet — but when they do, loading states will need to be added.

---

## 2. Progress Bars

| Component | Progress Feedback |
|---|---|
| Report Upload | ✅ Full-featured: progress bar with percentage, indeterminate animation during processing, status badges (Pending/Processing/Completed/Failed) |
| Report Processing | ✅ Badge with spin animation for "processing" status, retry button for failed |
| Chat AI Response | ✅ Typing indicator (bouncing dots + "AI is thinking...") |
| File Drag & Drop | ✅ Visual feedback (border color change, opacity reduction during upload) |

**Assessment:** Upload flow has excellent progress UX. Processing status badges are well-designed with appropriate iconography.

---

## 3. Error Messages

| Area | Quality |
|---|---|
| Login | ✅ Good — shows server error message or fallback "Invalid email or password". Inline validation for email format and required fields. |
| Register | ✅ Good — detailed per-field validation (password rules, email format, phone E.164, date format). Server errors shown via toast. |
| Chat | ✅ Good — "Failed to send message. Please try again." via toast. |
| Reports | ✅ Good — toast for upload/list/delete failures. Inline error display for file validation (type + size). Error message shown in report detail modal. |
| Medicines | ⚠️ Silent failure on list error — errors are swallowed (`setMedicines([])`), no user notification. |
| API Client | ✅ Automatic 401 → token refresh → retry. Logout on refresh failure. |
| Consistent pattern | ✅ All use `sonner` toast with rich colors |

**Assessment:** Error handling is generally good with a consistent toast pattern. The medicines page silently swallows errors, which should show a toast.

---

## 4. Empty States

| Page | Empty State |
|---|---|
| Patient Chat | ✅ "Start a conversation" with description |
| Patient Reports | ✅ "No reports uploaded" with CTA to upload |
| Patient Medicines | ✅ Context-aware: "No active medicines" / "No completed medicines" / "No medicines yet" |
| Patient Appointments | ✅ "No appointments scheduled" |
| Patient Dashboard | ⚠️ Placeholder text but no formal EmptyState component — shows "No medicines scheduled for today" / "No recent alerts" |
| Doctor Dashboard | ⚠️ Same as patient — inline text, not EmptyState component |
| Doctor Patients | ✅ "No patients assigned" |
| Doctor Alerts | ✅ "No alerts" |
| Doctor Appointments | ✅ "No appointments" |
| Demo Chat | ✅ "No questions yet" with suggested questions |

**Assessment:** Most pages have properly designed empty states using the shared `EmptyState` component. Dashboards use inline text which is functional but inconsistent.

---

## 5. Navigation

| Feature | Status |
|---|---|
| Header | ✅ Present on all authenticated pages — contains hamburger (mobile), collapse toggle (desktop), theme toggle |
| Sidebar | ✅ Fixed sidebar with role-specific nav items. Collapsible (desktop) + overlay (mobile). |
| Active States | ❌ **Missing** — No `usePathname()` or active link highlighting in sidebar |
| Mobile Nav | ✅ Hamburger menu with overlay, proper close-on-click behavior |
| Breadcrumbs | ❌ Not implemented |
| Logout | ✅ Accessible from sidebar footer, with API call + local cleanup |
| Auth redirect | ✅ Middleware checks auth cookie + role-based path enforcement |
| Demo navigation | ✅ Step indicator with 5-step wizard, back/next/reset buttons |

**Assessment:** Navigation structure is solid. The missing active link highlighting is a notable UX gap — users can't tell which page they're on.

---

## 6. Mobile Responsiveness

| Aspect | Assessment |
|---|---|
| Approach | Desktop-first with Tailwind responsive prefixes (sm/md/lg) |
| Sidebar | ✅ Hidden on mobile, toggled via hamburger. Overlay backdrop. |
| Grid layouts | ✅ Responsive grids (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`) |
| Chat layout | ✅ Full height, scrollable, input anchored at bottom |
| Auth screens | ✅ Centered card, full-width on mobile (`max-w-md`) |
| Demo page | ✅ Single column, max-width-3xl centered |
| Padding | ✅ Responsive padding (`p-4 lg:p-6`) |
| Known limitation | README acknowledges "mobile optimization is planned" |

**Assessment:** Desktop-first approach works but mobile could be better. The sidebar collapse on desktop is a good touch. The known limitation is documented.

---

## 7. Accessibility

| Aspect | Status |
|---|---|
| Semantic HTML | ⚠️ Mixed — `<main>`, `<nav>`, `<aside>`, `<header>` used in layouts. Pages use `<div>` with headings (`<h1>`) — generally good. |
| ARIA Labels | ✅ Chat page: `role="log"`, `aria-label="Conversation history"`, `aria-live="polite"`, `aria-label` on input and send button. Theme toggle has `aria-label`. |
| Expandable citations | ✅ `aria-expanded` on citation toggle |
| Form labels | ✅ All form inputs have associated `<Label>` components |
| Focus management | ⚠️ Chat page refocuses input after send. Modals don't trap focus. No skip-to-content link. |
| Keyboard navigation | ⚠️ Forms work with keyboard. Sidebar links are Tab-accessible. Modal close buttons exist but no Escape key handler. |
| Color contrast | ⚠️ Uses CSS variables with light/dark modes — relies on Tailwind defaults which generally meet WCAG AA |
| Alt text | ❌ `Avatar` component has alt prop but many uses don't pass meaningful alt text. Images generally lack alt attributes. |
| Reduced motion | ❌ No `prefers-reduced-motion` handling |

**Assessment:** Basic accessibility is present (ARIA on chat, form labels) but there are gaps — no focus trapping in modals, no skip navigation, no Escape key handlers.

---

## 8. Consistency

| Aspect | Assessment |
|---|---|
| Buttons | ✅ Consistent — shared `Button` component with CVA variants (default, destructive, outline, secondary, ghost, link) |
| Cards | ✅ Shared `Card` component with consistent styling (rounded-xl, border, shadow) |
| Badges | ✅ Shared `Badge` component with variants (default, secondary, destructive, outline, success, warning, info) |
| Colors | ✅ CSS variables in globals.css with light/dark mode — consistent across all pages |
| Typography | ✅ Inter font via next/font. Consistent heading hierarchy (text-2xl font-bold tracking-tight, text-muted-foreground for descriptions). |
| Spacing | ✅ Consistent `space-y-6` page layout, `gap-4` grids |
| Empty states | ✅ Shared `EmptyState` component used across most pages |
| Loading states | ✅ Shared `LoadingState` component with spinner + message |
| Icons | ✅ Lucide icons used consistently |
| Toast notifications | ✅ Sonner with `richColors` everywhere |
| Form patterns | ✅ react-hook-form + zod for all forms |

**Assessment:** Excellent visual and behavioral consistency. The shadcn/ui pattern is well-adopted.

---

## Prioritized UX Improvement List

### P0 — Critical (Launch-blocking)

| # | Issue | File | Impact |
|---|---|---|---|
| 1 | **Active nav link highlighting missing** | `doctor/layout.tsx`, `patient/layout.tsx` | Users can't tell current page — fundamental navigation UX |
| 2 | **Modals lack focus trapping and Escape key** | `reports/page.tsx` (delete + detail modals) | Keyboard users trapped, accessibility violation |
| 3 | **No loading state on dashboard pages** | `patient/dashboard/page.tsx`, `doctor/dashboard/page.tsx` | When APIs are wired, users will see stale `--` placeholders |
| 4 | **Medicines page silently swallows errors** | `patient/medicines/page.tsx:53` | Users never know if their data failed to load |

### P1 — High Priority (Before GA)

| # | Issue | File | Impact |
|---|---|---|---|
| 5 | **No skip-to-content / skip navigation link** | Root layout | Accessibility barrier for screen reader users |
| 6 | **Dashboard pages use inline text instead of `EmptyState` component** | Both dashboards | Inconsistent with rest of app |
| 7 | **No `prefers-reduced-motion` support** | globals.css + animations | Can cause discomfort for users with vestibular disorders |
| 8 | **Emergency/Symptom Checker page has no async loading state** | `patient/emergency/page.tsx` | When API is connected, no loading UX |
| 9 | **Login "Forgot password" shows toast instead of linking to a page** | `login/page.tsx:114` | Dead-end UX — should navigate to reset flow |
| 10 | **Report detail modal — close button only, no backdrop click or Escape** | `reports/page.tsx` | Inconsistent dismiss behavior |

### P2 — Nice-to-have (Post-launch)

| # | Issue | File | Impact |
|---|---|---|---|
| 11 | **Breadcrumb navigation** | Both layouts | Helps users understand deep navigation context |
| 12 | **Responsive table/data views for reports grid** | `reports/page.tsx` | Grid works but table view would be useful for many reports |
| 13 | **Skeleton loading instead of spinner** | Shared `LoadingState` | More polished perceived performance |
| 14 | **Drag-and-drop visual feedback could be more prominent** | `reports/page.tsx` | Current dashed border change is subtle |
| 15 | **Demo page confetti overlay is fun but could be gated behind a setting** | `demo/page.tsx` | Can be distracting in professional settings |
| 16 | **No page title/breadcrumb in document `<title>` per page** | Root layout | All pages show "AI Healthcare Assistant" — no dynamic titles |
| 17 | **Search/filter functionality missing from medicines and reports** | Various | Users with many items need filtering |
| 18 | **Toast auto-dismiss too fast on errors** | Global | Users may miss error messages |
| 19 | **No empty state icon customization in dashboards** | Dashboard pages | Could use role-relevant icons (Pill, Calendar, etc.) |
| 20 | **Mobile sidebar could support swipe-to-close gesture** | Both layouts | Better mobile UX |
