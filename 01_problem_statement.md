# 01 — Problem statement

**Team:** NAVY · **Agent:** P2 universe — agent-assist copilot, B2B payments fintech (Keelpay) · **Last updated:** 30 October 2026

> Every number says where it comes from: **measured**, **analogy** (a comparable, with its source) or **guess** (and how we will test it) — the course's own tags. The company, the five starting numbers and the vocabulary are fixed in the README ("frozen brief"): the five numbers are the company's data in our scenario (what a ticket log would give in real life), so they carry the tag **given**, with no test. This file builds on them and does not restate them differently.

> **Status:** rebuilt on the frozen brief. Costs in euros, team size and handling time are not here on purpose: they are derived bottom-up in the S2 sizing (`02_sizing.xlsx`) from the five starting numbers. The earlier version of this file (800 merchants, 12,000 tickets, 40 % reading) is superseded.

## 1. The problem in one sentence
Support agents at Keelpay, a B2B payments fintech handling about 20,000 tickets a month from about 1,500 merchants, spend roughly 45 % of each ticket's handling time understanding a free-text message, finding the payment it refers to, checking what was said before and routing it to the right desk, and about 1 ticket in 7 first lands in the wrong desk and loses a hand-over; today the support agent does all of this by hand before any answer is written. Success looks like average handling time down at a QA score no lower than today's, with no rise in urgent tickets reaching the wrong desk.

| Number in the sentence | Value | Given / measured / analogy / guess | Source or test |
|---|---|---|---|
| Merchant customers | ~1,500 | given | Scenario data (the company's own figure) |
| Tickets per month | ~20,000 | given | Scenario data (the company's own figure) — about 13 tickets per merchant a month |
| Share of handling time spent understanding, finding the payment and routing | ~45 % | given | Scenario data (the company's own figure) |
| Tickets first routed to the wrong desk | ~1 in 7 (about 15 %, ~2,900 tickets a month) | given | Scenario data (the company's own figure) |
| Languages | French, English | given | Scenario data (the company's own figure) |
| Average handling time, team size, cost per support agent | not set here | — | Derived bottom-up in the S2 sizing, tagged and sourced there |
| Target for handling time | not set here | — | Set in S2 against published benchmarks (e.g. Brynjolfsson, Li & Raymond, QJE 2025, arXiv:2304.11771: +15 % issues resolved per hour for support agents) and fixed as a minimum detectable effect in S6 |
| QA score | "no lower than today's" | not known yet | Baseline to measure before anything else; no number invented |

## 2. Problem tree — from symptom to cause
- **Symptom** (what people complain about): support agents lose much of their time before they can answer, and some tickets bounce between desks.
- **Problem** (what is actually going wrong): the important facts of a ticket (what it is about, which payment, how urgent) are buried in free text, so a person has to extract them and route by hand on every ticket.
- **Root cause** (5 Whys — each answer is a hypothesis; check it in three short interviews with support agents):
  1. Why does a ticket take long before the answer starts? — About 45 % of handling time goes into understanding the message, finding the payment, checking history and routing (see section 1).
  2. Why so much understanding? — The merchant writes "my payout is missing" or forwards an email thread; the type of request, the payment and the urgency are not in any field.
  3. Why are they not in a field? — Most tickets arrive by email, and the helpdesk form is bypassed. *Check: share of tickets by channel, and how often the existing category field is filled correctly.*
  4. Why not force a structured form? — A mandatory form works for portal tickets but not for email, which merchants prefer and which carries the urgent cases (a forwarded chargeback notice, a compliance request). Making it mandatory moves the cost to the merchant and risks losing the channel. *Check: ask whether a mandatory form was tried and what happened.*
  5. Why has it not been solved? — Keyword routing rules exist but break on free-text variety, two languages and forwarded threads; misrouting is only visible as an internal hand-over, so nobody prices it. *Check: look for "reassigned tickets" in the helpdesk reports; if it is reported, this Why is wrong.*
- **What would fix the cause:** two layers. (a) A **rule / integration**: attach the merchant's recent transactions, open disputes and last tickets to the ticket by merchant ID, date and amount, and use any structured fields already present — a tooling fix, not AI. (b) What a rule cannot do: read the free text in two languages, decide what the request is, which payment it means and how urgent it is, and say "I cannot tell" when it is unclear — that is the **language model** layer. Fix (a) is also the copilot's lookup layer, so it is built anyway.

## 3. Is AI the right tool?
| Question | Our answer |
|---|---|
| Is there a rule that solves 80 % of it? | A rule solves the part that is already structured: portal tickets with a category, tickets quoting a transaction ID, known senders. It cannot read an email that says "the money from last Tuesday is not there", in French or English, nor tell a dispute with a deadline from a plain status question. We assume rules cover well under half of the tickets; test: run a keyword and ID-match baseline on a labelled sample and count. It is the baseline to beat and the first layer of the product. |
| Is it a prediction / generation problem, or an organisational decision? | Mostly a prediction problem (what is the request, which payment, how urgent, which desk), then generation (the draft). The decisions — refund, dispute outcome, what to promise the merchant — stay with the support agent; the copilot executes none of them. |
| Do we have the data — which, how much, who owns it? | In the fictional company: tickets, transactions and merchant accounts, owned by the fintech. In our project: no real data, so we build a synthetic ticket set with gold labels (type, payment, urgency, desk) written by a teammate who does not tune the model. Coverage of rare dispute types and of English-language tickets is the weak point. |
| What does one error cost — and who pays it? | Two worst errors. (1) An urgent ticket in the wrong desk: a dispute deadline or compliance hold is missed, and the merchant or Keelpay pays. (2) A draft built on the wrong payment: the merchant acts on wrong information. Both look like a handled ticket, which is the trap. Because a support agent validates every ticket and reply (L2) and the copilot marks what it cannot determine as `UNDEFINED`, the error is recoverable, but a confident wrong reading is worse than no reading. Cost per error is priced in the S2 sizing. |

**Level chosen:** a small fine-tuned language model reading the text and returning a structured JSON, followed by fixed rules (a decision tree on the JSON), at L2. Not an AI agent in v1.

**What the fine-tuned model has to beat, in order.** Each rung is kept only if the one below fails.
1. **Deterministic rules and classical ML (no LLM).** Keyword and ID rules, structured fields, a text classifier. This is the main alternative. We assume it is not enough because the facts are in free natural language (two languages, forwarded threads, vague wording), but we do not take that for granted: the first bar is to **beat this rung on the held-out gold set**.
2. **A prompted LLM through an external API**, with structured-output libraries forcing valid JSON. Expect it to match the fine-tuned model on accuracy, so we do not claim a performance win. The case against it rests on two things: **cost** (every ticket is paid per call, forever, versus a small model that we host ourselves, locally or in our own cloud account, with a fixed cost) and **data governance** (every ticket, with merchant and payment data, would leave for an external provider; region, retention, no-training terms, a processing agreement). Honest caveat: at ~20,000 tickets a month a small API model may cost very little per ticket, and a hosted endpoint has fixed costs, so the cost argument can fail. The S2 sizing computes both options per month, the break-even volume, and what the governance constraint is worth; if neither cost nor governance favours the fine-tuned model, we recommend the prompted API.
3. **The fine-tuned small model**, self-hosted. Kept only if it is within a stated accuracy margin of rung 2 and wins on cost or on keeping the data in-house.

**Criticality score (proposed, to agree).** On top of the model's JSON, fixed rules compute a criticality score from a few fields: amount above a threshold, `urgency` high, `intent` dispute or compliance, a stated deadline, or a combination. A high score puts a visible alert on the ticket and requires the support agent to go through the evidence in detail before validating (L2 stays for every ticket; the score decides where to slow down). Two cautions: the score is only as good as the model's reading, so a missing or `UNDEFINED` amount on a dispute counts as critical by default; and thresholds are business parameters kept in configuration, set with the Head of Support and the Head of Compliance.

## 4. Why this agent — the four selection questions
| Criterion | Our answer, one line |
|---|---|
| High frequency — is the work done every day or every hour? | Yes: ~20,000 tickets a month, about 900 per working day, and every one is read, matched and routed. |
| Bounded decision space — can we list its tools and outcomes on one slide? | Yes: read the message, return one JSON, route through a fixed decision tree, read-only lookups of the matching transactions, one output (a pre-filled case and a draft, or an `UNDEFINED` flag), no write tool and no send tool. |
| Measurable success — can we say in one sentence whether it succeeded on one ticket? | Yes: the JSON matches the gold label (type, payment, urgency), the ticket reaches the right desk first time, and the support agent sends the draft with only minor edits. |
| Recoverable failure — if it is wrong, is the damage limited and reversible? | Yes at L2, because a support agent validates every ticket and reply; the residual risk is a wrong reading validated unread (automation bias), which we track as a counter-metric. |

## 5. Press release (Working Backwards)
*One paragraph, dated launch day: who it is for, what changed for them, one number, one customer quote.*

**Keelpay gives its support agents a copilot that reads the ticket first — and nothing goes out unreviewed.** *Launch day, October 2027 (target: 12 months from now).* Keelpay, the B2B payments platform used by about 1,500 merchants in France and Belgium, today announced that every ticket now reaches its support agents already read: the copilot has worked out what the merchant is asking, found the payment concerned, routed the ticket to the right desk and prepared a draft, and where it cannot tell, it says so instead of guessing. The support agent opens the ticket, sees what the copilot read, edits and sends; the copilot never writes to a merchant itself. Tickets landing in the wrong desk fell from about 1 in 7 to [target set in S2], and average handling time fell by [target set in S2], with the QA score unchanged. "I wrote that my payout from last Tuesday was missing, in two lines of email, and the reply named the exact transfer and the day it would land," said a finance manager at an online homeware merchant. "My team now spends its time on the cases that need judgement, not on working out what each message is about," said Keelpay's Head of Support.

## 6. What would have to be true?
| # | Hypothesis | Measured / analogy / guess | How we will test it | Session |
|---|---|---|---|---|
| 1 | The fine-tuned model clears three bars in order. (a) It beats deterministic rules and classical ML on a held-out gold set (accuracy per field, urgent tickets sent to the wrong desk, share left `UNDEFINED` rather than wrong). (b) It is within a stated margin of a prompted API LLM on the same set. (c) It costs less per month at our volume than the API option, or keeps the data in-house where the API option cannot (S2 sizing). | guess | Synthetic ticket set (French and English, at least a third hard cases: vague wording, several similar payments, forwarded threads), gold labels written by a teammate who does not tune the model. Run all three rungs; compare accuracy, and cost per month including training, hosting, maintenance and re-evaluation. | S2 sizing (cost), S4 prototype, LLMOps sub-project |
| 2 | Understanding really is ~45 % of handling time and the copilot cuts handling time at constant quality. | 45 %: given · size of the cut: analogy (see section 1) | Time-study on a sample of tickets with and without the copilot (split understanding / locating / routing / writing), scored by a QA rubric; then pre-register the copilot-on vs copilot-off comparison, alternating weeks for the same support agents, with its minimum detectable effect and sample size. | S5 metrics, S6 A/B |
| 3 | Support agents do not validate a wrong reading unread: a large share of seeded wrong readings (wrong payment, wrong desk, missing urgency) are caught or corrected before the ticket moves on. | guess | Seed wrong readings among correct ones across several testers acting as support agents; count how many are accepted as-is. The sample is small, so the result is indicative, not significant. | S4 prototype, S5 counter-metric |

## 7. Do-nothing baseline
What happens in 12 months if nobody builds anything? (It is not zero: the team gets faster, the documentation improves, volumes grow.)

Ticket volume grows with the merchant base, so the time spent understanding and routing grows with it, partly offset by support agents getting faster with experience and better macros. About 1 ticket in 7 keeps bouncing between desks, so urgent tickets (dispute deadlines, compliance holds) keep a standing risk of waiting in the wrong queue, with no safety net beyond a colleague noticing. The team needs more capacity just to hold today's response times, or replies get slower. The growth and the efficiency gain are priced with low / base / high ranges in the S2 sizing; no number is fixed here.
