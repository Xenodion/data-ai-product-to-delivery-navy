# Governance — our living file

> Created for Assignment 1, one line added every session. One question at the oral is drawn from this file.
> Answers are provisional: write what you know today, and mark what you still have to check.

## Session 1 — the six questions
| # | Question | Our answer (provisional) | To check with |
|---|---|---|---|
| 1 | **EU AI Act:** which risk tier is our agent in, and why? (minimal · limited — transparency: tell the user it is an AI · high-risk · prohibited) | Minimal to limited risk. It is an internal copilot used by the fintech's own employees; a human reads and sends every reply, so the merchant never talks to the AI. It does not score creditworthiness, decide on onboarding or execute payments, which are the fintech-related uses that would push it towards high-risk. Open point: the KYC / PSD2 flags only inform the agent; if they ever drove a due-diligence decision, the tier would need a new look. | Legal / DPO; reading of Annex III and Art. 50 by the team; the teacher |
| 2 | **Data:** whose data does it use, and on what legal basis? (GDPR art. 6; what the B2B contract allows) | Merchants' account data and tickets, and personal data inside transactions (payers' names, IBAN fragments, merchant staff contacts). Likely basis: performance of the contract (art. 6(1)(b)) for support, or legitimate interest (art. 6(1)(f)); the exact role of the fintech (controller or processor) is not settled. Rule from day one: retrieval is scoped to the merchant of the ticket, so merchant A's data can never reach merchant B's draft. Our own prototype uses synthetic data only. | DPO; the B2B contract clauses; the LLM provider's data-processing terms (region, no training on our data) |
| 3 | **Accountability:** who is accountable when it is wrong — and where is the human? | The human agent who sends the reply remains accountable for what leaves the company; the Head of Support owns the quality of the support outcome; our team, as product owner, owns the copilot's behaviour and its rollback. The human sits between the draft and the merchant on every ticket (L2). An agent can ignore the draft or switch the copilot off for a ticket; a company-wide switch back to "context only" or off is to be designed in S4. | Head of Support (named owner to confirm); S4 for the override switch |
| 4 | **Never:** what must it never do? (our first guardrail) | First guardrail: **never send anything to a merchant** — it drafts, a human sends. Further guardrails to confirm: never state a payment status, amount or date that is not backed by a linked transaction; never promise a refund or a dispute outcome; never give legal or regulatory advice (it flags, the agent or Compliance decides); never use another merchant's data. | The team; Compliance |
| 5 | **Explainability:** explainable to whom — the customer, the support agent, the auditor? | *Agent:* every claim in the draft links to the transaction or past ticket it comes from, with a groundedness score and the "context only" state when evidence is thin. *Merchant:* receives an ordinary human reply that names the transactions concerned; they can ask the agent why. *Auditor:* a log per ticket — retrieved items, draft, final text sent, edits, who sent it, model and prompt version. Retention period of that log is not decided. | DPO; Compliance (retention) |
| 6 | **The people it cannot serve:** what happens to them? | Tickets where evidence is thin (new merchants with little history, rare dispute types, languages or formats we did not test) fall below the threshold and get "context only": a human works them as today, but they could end up slower than assisted tickets. We will report handling time and QA for below-threshold tickets and by merchant segment (size, language, age of account) as a counter-metric, so that a gain on the average cannot hide a loss there. We also report by agent seniority: published results on AI assistance for support agents (Brynjolfsson, Li & Raymond, arXiv:2304.11771) find the gain concentrated among less experienced agents, with small quality declines for the most experienced. The agents are users too: no forced use, and no target that blames them for the tool. | S5 (segments and counter-metrics); Head of Support |

## Session 2 — the cost of error
- Which cost-of-error line is a **legal or reputational** risk, not just money? …
- Who in the company **owns** that risk? …

## Session 3 — data (to come)
## Session 4 — human-in-the-loop points and the override switch (to come)
## Session 5 — counter-metrics and the segments we report (to come)
## Session 6 — protected segments and the harm threshold that stops an experiment (to come)
## Session 7 — accountable owner, rollback authority, incident path (to come)
