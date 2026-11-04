# 03 — User research · Keelpay Support Copilot

> Three conversations (20 min each) + one usability test of our prototype with two of them.
> Mom Test rules (Rob Fitzpatrick): ask about past behaviour, not opinions; never pitch; never ask “would you use…?”.
> Classmates played the roles of support agents/leads in our scenario (stated explicitly below).

---

## Who we talked to

| # | Who (role, company type — no personal data) | Real user or classmate in role? | Date | Interviewer · note-taker |
|---|---|---|---|---|
| 1 | Tier-1 Support Agent (handling payment inquiries & refunds) | Classmate in role | 28 Oct 2026 | Alexandre · Vincent |
| 2 | Support Team Lead (managing shared inboxes & escalation queues) | Classmate in role | 29 Oct 2026 | Nahel · Yoni |
| 3 | Technical & Disputes Support Specialist (chargebacks & API webhooks) | Classmate in role | 29 Oct 2026 | Vincent · Alexandre |

---

## Interview guide (adapt it — keep it about the past)

1. Tell me about the last time you handled an ambiguous ticket with no transaction reference. What happened, step by step?
2. What was the hardest part? How long did it take to identify the right transaction or desk?
3. When a ticket was misrouted to your queue, what did you do? Who did you contact?
4. How do you verify drafted answers when dealing with time-sensitive disputes (chargebacks)?
5. If you could change one thing in that moment of your daily routine, what would it be?

*Avoided:* “Would you use an AI that…?” · “Do you like this idea?” · “How much would you pay?”

---

## What we heard (facts, in their words)

| # | Quote or observed behaviour | Which part of our brief it confirms or contradicts |
|---|---|---|
| 1 | *“When a merchant gives no transaction ID, searching by amount gives 3 or 4 candidates. I have to open each in a separate tab to compare timestamps, which burns 3 to 5 minutes.”* | **Confirms** sub-case B: the need for pre-filtered transaction candidates with distinguishing facts (date, status, customer name) directly in the case card. |
| 2 | *“A single total ticket count in the queue doesn't tell me what is burning. I need to see how long each ticket has been waiting and open the oldest urgent one first.”* | **Contradicts** our initial simple queue badge: supports adding visible queue waiting time (FIFO) and highlighting time in current step. |
| 3 | *“If I realize a ticket was assigned to the wrong desk, I hate losing the context when reassigning it. And the draft should be re-prepared for the new team.”* | **Confirms** our recovery design: a 1-click desk correction invalidates the previous draft and triggers a new draft for the target desk while keeping ticket history. |
| 4 | *“I would never let any tool send an email about money or chargebacks automatically without my final review.”* | **Confirms** hard L2 human review and explicit human send button: no autonomous send tool. |

---

## Usability test — one task, think aloud, don't help

**Prototype link:** `prototype/copilot_panel/index.html` (see `03_prototype_link.md`)  
**Task given:** *"Ticket #K-24121 came in this morning. Inspect what the copilot extracted, select the matching transaction candidate, review the cited draft, and confirm send."*

| Tester | Role | What they did, step by step | Where they hesitated or failed | Quote |
|---|---|---|---|---|
| Tester 1 | Support Agent (Payments) | Opened ticket K-24121; checked extracted fields in side panel; hovered on amount to verify source passage; clicked candidate TX-992100; read cited draft; clicked Send. | Hesitated on whether selecting a candidate automatically updated the draft text or required an extra click. | *“I like seeing the candidate transactions side by side, but make it super obvious which one is currently selected in the draft.”* |
| Tester 2 | Support Team Lead | Looked at ticket queue first; looked for waiting time; opened K-24121; checked desk assignment; reviewed cited sources (KB-214); edited one sentence; clicked Send. | Tried to click on the queue priority badge to sort; wondered how long the ticket had been in the queue before opening. | *“The side-by-side view is clean, but show me ticket waiting time directly in the inbox header so I can prioritize oldest tickets first.”* |

---

## Desirability gate — do they want it?

- [x] **2 of 2 finished the task without help** — both successfully qualified the candidate transaction and simulated send in under 3 minutes.
- [x] **They told us what they did last time, not what they would do** — conversations focused on past handling of unreferenced payouts and chargeback deadlines.
- [x] **At least one said “I want this before…”** — Tester 1: *“I want this before the Black Friday peak; finding matching payouts by hand is our biggest bottleneck.”*
- [x] **Our out-of-scope list grew; our success criterion did not move** — confirmed strictly out-of-scope: autonomous sending and ledger write tools.

**Decision:** GO to Session 4 build. The test validates the 3-panel layout (queue / ticket / copilot panel) and provides the two direct user-driven modifications incorporated into v2:
1. Displaying visible waiting time and oldest-first queue ordering.
2. Distinct visual highlighting and confirmation for selected transaction candidates before drafting.
