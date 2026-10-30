# 01 — Problem statement

**Team:** NAVY · **Agent:** P2 universe — agent-assist copilot, B2B payments fintech (Keelpay) · **Last updated:** 30 October 2026

> Every number says where it comes from: **measured**, **analogy** (a comparable, with its source) or **guess** (and how we will test it) — the course's own tags. The company, the starting numbers and the vocabulary are fixed in the README ("frozen brief"). Those numbers are the company's data in our scenario (what a ticket log would give in real life), so they carry the tag **given**, with no test. This file builds on them and does not restate them differently.

> **Status:** rebuilt on the frozen brief, as one end-to-end flow with two sub-cases (routing and drafting). Costs in euros, team size, handling time and targets are not here on purpose: they are derived bottom-up in the S2 sizing (`02_sizing.xlsx`). The earlier version (800 merchants, 12,000 tickets, 40 % reading, a single drafting copilot) is superseded.

## 1. The problem in one sentence

Support agents at Keelpay, a B2B payments fintech handling about 20,000 tickets a month from about 1,500 merchants, spend about 15 % of each ticket's handling time reading a free-text message and routing it, and about 45 % finding the payment and its history and writing the reply; about 1 ticket in 7 first lands in the wrong desk and loses a hand-over, and an urgent ticket in the wrong desk can miss its deadline. Today the support agent does all of this by hand. Success looks like average handling time down, end to end, at a QA score no lower than today's, with no rise in urgent tickets reaching the wrong desk.

| Number in the sentence | Value | Given / measured / analogy / guess | Source or test |
|---|---|---|---|
| Merchant customers | ~1,500 | given | Scenario data |
| Tickets per month | ~20,000 | given | Scenario data (about 13 tickets per merchant a month) |
| Share of handling time: reading and routing (sub-case A) | ~15 % | given | Scenario data |
| Share of handling time: finding the payment and history, and writing the reply (sub-case B) | ~45 % | given | Scenario data |
| Rest of handling time (validating and sending, back-office actions, wrap-up) | ~40 % | given | Scenario data; the copilot does not act on it |
| Tickets first routed to the wrong desk | ~1 in 7 (about 15 %, ~2,900 tickets a month) | given | Scenario data |
| Languages | French, English | given | Scenario data |
| Average handling time, team size, cost per support agent | not set here | — | Derived bottom-up in the S2 sizing, tagged and sourced there |
| Target for handling time | not set here | — | Set in S2 against published benchmarks (e.g. Brynjolfsson, Li & Raymond, QJE 2025, arXiv:2304.11771: +15 % issues resolved per hour for support agents) and fixed as a minimum detectable effect in S6 |
| QA score | "no lower than today's" | not known yet | Baseline to measure before anything else; no number invented |

Handling time means hands-on time and excludes waiting in a queue. Queue waiting (time to first reply) is a separate, secondary indicator; routing errors lengthen it because a ticket waits twice.

## 2. The flow, and the problem tree

**The flow we specify and build** (one copilot, two sub-cases that depend on each other):
1. **Read:** a fine-tuned model reads the message and returns a structured JSON (request type, payment, amount, urgency); anything it cannot determine is `UNDEFINED`.
2. **Route:** fixed rules (a decision table on the JSON, with a criticality score) send the ticket to a desk. Clear tickets are routed automatically; low-confidence, critical or `UNDEFINED` tickets go to a support agent for triage first.
3. **Look up:** the matching transactions and history are retrieved, read-only and limited to the merchant.
4. **Draft:** a prompted model with retrieval over the desk's policies and read-only database queries writes the reply, citing its sources.
5. **Review and send:** a support agent reads, edits and sends. If the ticket is found misrouted, the agent reroutes it and it is redrafted in the right desk, once; a second reroute goes to human triage.
6. **Feedback:** reroutes and edits are logged and become labels to re-evaluate the model.

Steps 1–2 are sub-case A (routing): shorter, more critical. Steps 3–5 are sub-case B (drafting): longer, relieved by a human who reads every draft. Drafting only pays on tickets that were routed correctly.

**Problem tree**
- **Symptom** (what people complain about): support agents lose much of their time before and while answering, and some tickets bounce between desks.
- **Problem** (what is actually going wrong): the important facts of a ticket (what it is about, which payment, how urgent) are buried in free text, so a person has to extract them, route the ticket and rebuild the context by hand on every ticket.
- **Root cause** (5 Whys — each answer is a hypothesis; check it in three short interviews with support agents):
  1. Why does a ticket take long? — About 60 % of handling time goes into reading and routing, then finding the payment and writing the reply (section 1).
  2. Why so much reading? — The merchant writes "my payout is missing" or forwards an email thread; the type of request, the payment and the urgency are not in any field.
  3. Why are they not in a field? — Most tickets arrive by email and the helpdesk form is bypassed. *Check: share of tickets by channel, and how often the existing category field is filled correctly.*
  4. Why not force a structured form? — A mandatory form works for portal tickets but not for email, which merchants prefer and which carries the urgent cases (a forwarded chargeback notice, a compliance request). Making it mandatory moves the cost to the merchant and risks losing the channel. *Check: ask whether a mandatory form was tried and what happened.*
  5. Why has it not been solved? — Keyword routing rules exist but break on free-text variety, two languages and forwarded threads; misrouting is only visible as an internal hand-over, so nobody prices it; and the ticket is not linked to the merchant's transactions. *Check: look for "reassigned tickets" in the helpdesk reports; if it is reported, this Why is wrong.*
- **What would fix the cause:** (a) a **rule / integration** layer: use any structured field already present and attach the merchant's recent transactions, open disputes and last tickets by merchant ID, date and amount — a tooling fix, not AI; (b) what a rule cannot do: read free text in two languages, decide what the request is, which payment it means and how urgent it is, say "I cannot tell", and write a reply grounded in the merchant's data — the **language model** layer. Layer (a) is also the copilot's lookup, so it is built anyway.

## 3. Is AI the right tool? — step by step

The flow is not one AI decision. For each step we ask what the cheapest tool that works is.

| Step | Tool we assume | Why | Trust level |
|---|---|---|---|
| 1. Read | Language model (options compared below) | Facts sit in free text, two languages | Output checked by the rules in step 2 |
| 2. Route | Fixed rules (decision table) + criticality score | A decision on a few fields is deterministic; no AI needed, and it is explainable | L3, with sampling (to confirm in governance); `UNDEFINED` and critical tickets go to a human |
| 3. Look up | Integration / query | Exact match by ID, date, amount | Read-only |
| 4. Draft | Prompted model + retrieval (policies, past replies) + read-only queries | Generation grounded in the merchant's data; no fine-tuning needed | L2 |
| 5. Review and send | Human | Policy and promises stay with a person | Human only; no send tool |

| Question | Our answer |
|---|---|
| Is there a rule that solves 80 % of it? | Rules solve what is already structured: portal tickets with a category, tickets quoting a transaction ID, known senders. They cannot read an email that says "the money from last Tuesday is not there", in French or English, nor tell a dispute with a deadline from a plain status question. We assume rules cover well under half of the tickets; test: run a keyword and ID-match baseline on a labelled sample. It is the baseline to beat and the first layer of the product. |
| Is it a prediction / generation problem, or an organisational decision? | Prediction for the routing (what is the request, which payment, how urgent, which desk), generation for the draft. The decisions — refund, dispute outcome, what to promise the merchant — stay with the support agent. |
| Do we have the data — which, how much, who owns it? | In the fictional company: tickets, transactions, merchant accounts and desk policies, owned by the fintech. In our project: no real data, so we build a synthetic ticket set with gold labels (type, payment, urgency, desk, reference reply) written by a teammate who does not tune the model. Rare dispute types and English tickets are the weak point. |
| What does one error cost — and who pays it? | Two worst errors, which look like a handled ticket. (1) An urgent ticket in the wrong desk: a dispute deadline or compliance hold is missed. (2) A draft built on the wrong payment: the merchant acts on wrong information. A support agent reads every draft (L2) and `UNDEFINED` makes the copilot say it cannot tell, so errors are recoverable, but a confident wrong reading is worse than none. A misrouted ticket is caught late (when the agent opens the draft), so the criticality score slows down the tickets where lateness hurts. Cost per error is priced in the S2 sizing. |

**Options for step 1 (read).** We do not assume the fine-tuned model wins; it is one of five options, judged on the same held-out gold set.

| Option | What it is |
|---|---|
| A | Deterministic rules (keywords, IDs, structured fields) |
| B | Classical ML or deep learning (text classifier, small fine-tuned encoder) |
| C | Open-source LLM with a system prompt, self-hosted, not fine-tuned |
| D | Small fine-tuned LLM, self-hosted (local or in our own cloud account) |
| E | LLM through an external provider's API, with a system prompt |

*Criteria.* (1) **Effectiveness:** accuracy per field, urgent tickets sent to the wrong desk, share left `UNDEFINED` rather than wrong. (2) **Total monthly cost at 20,000 tickets:** inference, hosting, training, maintenance, re-evaluation, with the break-even volume between options (S2 sizing). (3) **Data and control:** where tickets and payment data go (region, retention, no-training terms, processing agreement), and whether we can pin a model version, roll back, and avoid a third party retiring the model.

*Decision rule.* Keep the cheapest option that clears the effectiveness bar and meets the data constraint. A is the main alternative and we assume it is not enough because the facts are in free natural language, but we measure it. Structured-output tools make C and E produce valid JSON, so we expect them to match D on accuracy and do not claim a performance win. D is defended on two comparisons: against E on cost and on keeping tickets in-house; against C by showing a small fine-tuned model matches or beats a larger prompted one at a lower serving cost. Honest caveat: at ~20,000 tickets a month an API call may cost very little per ticket and a hosted endpoint has fixed costs, so the cost argument can fail. If neither cost nor data control favours D, we recommend the cheapest prompted option (C or E).

**Criticality score (proposed, to agree).** On top of the JSON, fixed rules compute a score from a few fields and context: amount above a threshold, `urgency` high, `intent` dispute or compliance, a stated deadline, an open dispute on the merchant, or a combination. A high score puts a visible alert on the ticket, asks a human to confirm the routing before any draft, and requires a detailed review before sending. Caution: the score depends on the model's reading, so a missing or `UNDEFINED` amount on a dispute counts as critical by default. Thresholds are business parameters kept in configuration, set with the Head of Support and the Head of Compliance.

## 4. Why this agent — the four selection questions

| Criterion | Our answer, one line |
|---|---|
| High frequency — is the work done every day or every hour? | Yes: ~20,000 tickets a month, about 900 per working day, and every one is read, routed and answered. |
| Bounded decision space — can we list its tools and outcomes on one slide? | Yes: read the message, return one JSON, route through a fixed table, read-only lookups and retrieval, one output (a pre-filled case and a cited draft, or an `UNDEFINED` flag), no write tool and no send tool. |
| Measurable success — can we say in one sentence whether it succeeded on one ticket? | Yes: the ticket reaches the right desk first time, the draft cites the right payment, and the support agent sends it with only minor edits, faster than the baseline. |
| Recoverable failure — if it is wrong, is the damage limited and reversible? | Yes with a human on every draft and a bounded reroute loop; the residual risks are an urgent ticket waiting in the wrong desk and a wrong reading validated unread (automation bias), both tracked as counter-metrics. |

## 5. Press release (Working Backwards)

*One paragraph, dated launch day: who it is for, what changed for them, one number, one customer quote.*

**Keelpay gives its support agents a copilot that reads, routes and drafts — and nothing goes out unreviewed.** *Launch day, October 2027 (target: 12 months from now).* Keelpay, the B2B payments platform used by about 1,500 merchants in France and Belgium, today announced that every ticket now reaches the right desk already read: the copilot works out what the merchant is asking, finds the payment concerned, prepares a reply with its sources cited, and where it cannot tell, it says so instead of guessing. The support agent sees what the copilot read, edits and sends; the copilot never writes to a merchant itself. Tickets landing in the wrong desk fell from about 1 in 7 to [target set in S2], and average handling time fell by [target set in S2], with the QA score unchanged. "I wrote that my payout from last Tuesday was missing, in two lines of email, and the reply named the exact transfer and the day it would land," said a finance manager at an online homeware merchant. "My team now spends its time on the cases that need judgement, not on working out what each message is about," said Keelpay's Head of Support.

## 6. What would have to be true?

| # | Hypothesis | Given / analogy / guess | How we will test it | Session |
|---|---|---|---|---|
| 1 | **Routing (A).** The fine-tuned model (D) is the right choice among A to E: it clears the effectiveness bar and beats A and B; it matches the prompted options C and E on accuracy within a stated margin; and it is cheaper per month at our volume than E and C, or keeps the data in-house where E cannot. | guess | Synthetic ticket set (French and English, at least a third hard cases: vague wording, several similar payments, forwarded threads), gold labels by a teammate who does not tune the model. Run the options; compare accuracy per field and monthly cost including training, hosting, maintenance, re-evaluation. | S2 sizing (cost), S4 prototype, LLMOps sub-project |
| 2 | **Routing, safety.** The rules plus `UNDEFINED` keep urgent tickets out of the wrong desk: the share of urgent tickets routed automatically to the wrong desk is lower than today's, and the share sent to human triage is small enough to leave most of the gain. | guess | On the gold set, measure the share routed automatically, the error rate in that lane, and the share sent to triage, at several thresholds. | S4 prototype |
| 3 | **Drafting (B).** A cited draft cuts the time spent finding the payment and writing the reply, at constant quality, on correctly routed tickets. | slice sizes: given · size of the cut: analogy (section 1) | Time-study on a sample with and without the draft, scored by a QA rubric; then pre-register the copilot-on vs copilot-off comparison, alternating weeks for the same support agents, with its minimum detectable effect and sample size. | S5 metrics, S6 A/B |
| 4 | **Human net.** Support agents do not validate a wrong reading unread: a large share of seeded wrong readings (wrong payment, wrong desk, missing urgency) are caught or corrected before the ticket moves on. | guess | Seed wrong readings among correct ones across several testers acting as support agents; count those accepted as-is. The sample is small, so the result is indicative. | S4 prototype, S5 counter-metric |
| 5 | **End to end.** Across the flow, average handling time falls at constant quality, net of the time spent in triage and on reroutes. | guess | Same A/B as hypothesis 3, on the whole flow; the offline per-step evaluations explain where the gain or loss comes from. | S6 A/B |

## 7. Do-nothing baseline

What happens in 12 months if nobody builds anything? (It is not zero: the team gets faster, the documentation improves, volumes grow.)

Ticket volume grows with the merchant base, so the time spent reading, routing, looking up and writing grows with it, partly offset by support agents getting faster with experience and better macros. About 1 ticket in 7 keeps bouncing between desks, so urgent tickets (dispute deadlines, compliance holds) keep a standing risk of waiting in the wrong queue, with no safety net beyond a colleague noticing. The team needs more capacity just to hold today's response times, or replies get slower. The growth and the efficiency gain are priced with low / base / high ranges in the S2 sizing; no number is fixed here.
