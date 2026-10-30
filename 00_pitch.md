# 00 — Bring-your-own pitch (half a page)

> We start from proposal P2 (agent-assist copilot, B2B payments fintech) and redefine the case: company, scale, pain, job and trap are our own. The frozen brief is in the README; this page is its half-page pitch. Figures marked *given* come from the scenario; derived figures are guesses re-computed in the S2 sizing.

**The company:** Keelpay, a B2B payments fintech with ~2,500 merchant customers in France and Belgium, ~36,000 support tickets a month in French and English (mostly by email) and a support team of about 46 agents (guess: 36,000 tickets × ~10 min of hands-on handling ≈ 6,000 hours a month, at ~130 productive hours per agent).

**The pain, as a cost:** About 60 % of handling time goes into reading and routing a free-text message (~15 %, given) and finding the payment and writing the reply (~45 %, given): roughly 3,600 hours a month, the work of about 28 agents, or about €1.4M a year at ~€50k all-in per agent (guess; French customer-adviser job postings, to be sourced in S2). About 1 ticket in 7 (~5,100 a month, given) first lands in the wrong desk and loses a hand-over, and an urgent one (dispute deadline, compliance hold) can miss its deadline.

**Do-nothing baseline:** Volume grows with the merchant base, so the same reading, routing and writing time grows with it, partly offset by agents getting faster. About 1 ticket in 7 keeps bouncing between desks and urgent tickets keep a standing risk of waiting in the wrong queue. The team needs more capacity to hold today's response times, or replies get slower. Priced with ranges in the S2 sizing.

**The agent's job:** When a merchant ticket arrives, the copilot reads it, returns a structured JSON, routes it to the right desk (automatically when clear, to a human triage when unsure or critical), retrieves the matching transactions and history, and drafts a cited reply that a support agent reviews, edits and sends.

**Trust level per step:**
- Read and route (fine-tuned model plus fixed rules): **L3** with sampling; anything undetermined is `UNDEFINED` and goes to a human; critical tickets get a human confirmation of the desk.
- Look up transactions and history: **L1** (read-only, limited to the merchant).
- Draft the reply: **L2** (a support agent reads and approves every reply).
- Send to the merchant: **human only** — the copilot has no send tool.

**One thing it must never do:** send anything to a merchant — it drafts, a human sends.

**Why it is a product decision:** The Head of Support and the Head of Compliance must decide whether to let a model route tickets automatically, at what confidence and criticality thresholds, and how much of the routing to automate given that tickets stay in Keelpay's own cloud (the data constraint), which rules out an external model API. They risk urgent tickets sitting in the wrong desk, a wrong reply validated unread, and regulatory exposure on dispute and compliance questions.

## Checklist (all seven must be ticked)
- [x] A named company type, a ticket volume and a team size
- [x] A pain expressed as a cost
- [x] A do-nothing baseline
- [x] One job in one sentence
- [x] A trust level per step, at least one below L4
- [x] One thing it must never do
- [x] A real decision: someone must decide whether to ship it
