# Flow v2 frontend UX

Updated 10 November 2026. The frontend is a local support-agent workspace backed by the flow API. It is not an analytics source of truth; business state and action eligibility come from the API.

## Navigation

The console has two primary destinations in a collapsible left rail: **Dashboard** and **Workspace**. Workspace has queue tabs for **Re-routing**, **Ticket review**, and **Errors**, keeping navigation stable while allowing agents to switch work queues quickly. The compact top bar carries product, local environment, flow version, and API health.

## Dashboard

The dashboard polls `GET /api/v1/overview`. It uses only `total`, `by_status`, `queues`, `simulated_sends`, `oldest_waiting_seconds`, and `ratios.human_review_rate` from that response.

It shows four headline counts, a directed workflow graph, a status breakdown, and the human queue rate. The graph separates automated processing from human control and outcomes, shows SQL and Text Search as independent parallel tools, and links human/error queue nodes to their workspaces. Motion is restrained and conditional: active work animates the flow path, while non-empty human queues highlight the relevant checkpoint. Reduced-motion preferences disable decorative animation. Only API-provided queue/status counts appear; intermediate node counts, timings, or quality scores must not be inferred from business-state totals. This borrows the animated graph idea from [Flowyboard](https://www.flowyboard.com/) while keeping the map tied to our actual API contract. The current SVG is intentionally unchanged until its diagram update is scheduled.

Synthetic ticket injection remains available in a collapsed panel for local demos.

## Ticket workspaces

At desktop widths, the workspace has three functional regions, in a restrained support-console layout:

1. **Inbox, left:** searchable queue summaries with status, subject, desk and priority; oldest-first order and cursor pagination come from the API.
2. **Ticket and draft, center:** incoming message, current reply draft, and controls for the actions permitted by `allowed_actions`. Re-routing asks for a target desk and reason. Approval is disabled when the agent has unsaved edits, which must be saved first. Before sending, the Support Agent explicitly chooses **send and leave open** or **send and close**; neither option is preselected. The distinct **close without reply** action requires a reason.
3. **Context and history, right:** merchant/desk/priority/state, qualifier result, routing signals, evidence sources and facts, policy findings, draft versions, prior turns, and node lifecycle events.

On narrow screens, the inbox, ticket/draft, and context stack vertically. Queue and detail data refresh by polling; the UI does not assume that a submitted action has completed until the refreshed ticket state arrives.

## Interaction constraints

- `allowed_actions` is the sole source for which human action buttons are shown. The backend remains authoritative and can reject stale ticket versions or invalid transitions.
- All displayed states and counts come from ticket snapshots or the overview endpoint. No sample metrics are shown in the agent dashboard.
- Human decisions use amber emphasis; approval and simulated-send actions use green; errors use red. Color is paired with labels, status text, and icons so it is not the sole signal.
- Error tickets expose investigation details but no unsupported recovery action. A recovery workflow needs an API contract before it can be added to the UI.
- Replies are simulated; the interface does not deliver external messages.
- The selected send disposition is clearly shown in the confirmation control and ticket history. Sent-open, sent-closed, and manually closed without a reply have distinct labels and dashboard counts.

## Remaining acceptance work

- Review keyboard navigation, visible focus, and screen-reader announcements on dashboard, graph queue links, and ticket actions.
- Exercise the complete API-backed flow at desktop and mobile widths, including empty queues, paging, action conflicts, policy blocks, and asynchronous status changes.
- Verify both send dispositions, close-without-reply, audit/history rendering, and distinct overview counts for each outcome.
- Add per-node counts/latency only after the API exposes a well-defined persisted metric response; do not derive them from current business status.
