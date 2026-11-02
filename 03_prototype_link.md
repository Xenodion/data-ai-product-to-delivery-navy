# 03 — Prototype link · Keelpay agent-assist copilot

> One clickable prototype of where the copilot lives (the support agent's helpdesk), made in under an hour. It is a question for users, not the product: four synthetic tickets, fictional merchants, no real data.

- **Link:** `prototype/copilot_panel/index.html` in this repository. It is one self-contained HTML file: download it or clone the repo and open it in any browser, with no install and no server.
- **Tool:** other: a static HTML page (HTML, CSS and plain JavaScript in one file), written with an AI coding assistant from the prompt below.
- **Version:** v0.1 (2 November 2026): queue, ticket and copilot panel; four tickets that cover the four paths of the flow (`assets/copilot_flow.png`):
  1. **Routed automatically, cited draft.** #K-24118, a payout returned by the bank.
  2. **The payment cannot be told apart** (French, amount in words, no reference). The agent picks the payment, then the draft is written. #K-24121. **This is the usability-test task.**
  3. **Critical** (forwarded chargeback with a deadline). The agent confirms the desk before any draft. #K-24125.
  4. **`UNDEFINED`** (several requests in one message), sent to human triage. #K-24127.
- **The prompt we used (the brief in three paragraphs):**

```
Paragraph 1 — who uses it and for what job:
A Keelpay support agent (B2B payments fintech, ~36,000 merchant tickets a month in French and
English) on one of four desks: payments, disputes, technical / API, compliance. Job: get each
ticket to the right desk and answer it on the right payment, without decoding a free-text message
and hunting for the transaction by hand. Build a clickable mock of their helpdesk with four
synthetic tickets (fictional merchants), one per path: routed automatically; payment not
identifiable (French, amount in words, no reference); critical (forwarded chargeback with a
deadline); UNDEFINED (several requests in one message).

Paragraph 2 — what is on the screen (panels, buttons, the one thing it must never do):
Three columns: the ticket queue with a routing badge per ticket; the ticket with the passages the
copilot used underlined; the copilot side panel with (1) what the copilot read, as the JSON fields
(intent, sub_intent, transaction_id, amount, currency, urgency, sentiment), each highlighting its
source passage on hover; (2) the path taken through the flow; (3) the case card: merchant,
transactions, linked disputes, last tickets, read-only; (4) the cited draft, editable, with
numbered sources; (5) a one-click reroute; (6) a log. The copilot never sends: only the agent has
a Send button. A switch turns the copilot off for one ticket.

Paragraph 3 — the rules (routing, what is "human only", the trust level):
A decision table routes clear, non-critical tickets automatically (L3, sampled audit). UNDEFINED
or low-confidence tickets go to human triage, nothing guessed. Critical tickets (dispute,
deadline, high urgency) wait for a person to confirm the desk before any draft. Lookups are L1
(read-only, this merchant only); the draft is L2 (the agent approves every reply). A rerouted
ticket is drafted again once; a second reroute goes to human triage. Use blue for what the system
did and amber for what a person does, as in our flow figure.
```

- **How to open it:** the page is not hosted online (GitHub shows its source, not the page). Testers open the file locally in a browser, or we share the folder; nothing to install.
- **Screenshot:** ticket #K-24121, the usability-test task: the reference is `UNDEFINED`, so the copilot shows both €1,250.00 payouts and waits for the agent to pick one before drafting.

  ![Prototype v0.1, ticket #K-24121](assets/prototype_K-24121.png)

- **v0.1, 2 November (after the spec):** the JSON now follows `label_definitions.md` (`delayed_credit`, `missing_payment`, urgency `medium`, `""` for absent fields), and the panel no longer shows a confidence score: the router returns none, its doubt is `UNDEFINED` (`spec.md` §2).

## Known limits of v0.1 (to tell testers)
- **Rerouting a critical ticket** to another desk keeps the same draft text; the real copilot would draft again for the new desk.
- **"Split into separate tickets"** is not built yet.
- **A ticket triaged from `UNDEFINED`** stops at the desk choice; there is no new reading or draft after it.
- **Nothing is saved:** reloading the page resets every ticket.
