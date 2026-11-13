# 05 · Metrics — NAVY · Keelpay support copilot

> Session 5 deliverable. Five sections = the five moves of the session. Every number traces to a file already in the repo (`02_sizing.xlsx`, `evals/report_v0.md`) — no new number appears here. Sizing cells are cited as `Sheet!Cell`.
> **Status (13 November 2026):** §3 and §5 written; §1, §2 and §4 wait for `evals/report_v0.md` (the S4 run on the 50 cases of `evals/eval_set_v0.csv`).

## 1 · Place the number — the stack for our agent
`⟨waits for evals/report_v0.md: the S4 number is the level-2 line, and each level's value must trace to the report or the sizing⟩`

| Level | Question | Our metric | Value today (or "not yet") | Produced by | Owner | Clock |
|---|---|---|---|---|---|---|
| 5 Business | does it move the P&L? | | | | | months |
| 4 Product | does the user adopt it and get the job done? | | | | | weeks |
| 3 Guardrails & responsible AI | does it stay inside the lines — for everyone? | | | | | days |
| 2 AI system | does the workflow complete the task? | *our S4 number* | | eval-set + two graders | | hours |
| 1 Model | is the component right? | | | offline eval-set | | seconds |

## 2 · Decide when to stop — the stop criterion
`⟨waits for evals/report_v0.md⟩`

- Component metric and value:
- The level-above metric that stops responding (or the action threshold):
- Cost of the next point (weeks, tokens, labelling, latency):
- What is a **floor**, not a stop (any miss blocks the release):

## 3 · Choose what to protect — the hierarchy, by segment
The primary is the product promise of the brief: **less hands-on time per ticket, at a quality no lower than today**. It is the metric most at risk of being gamed — an agent can go faster by sending drafts unread — so each guardrail and counter-metric below closes one way of winning it wrongly.

| Kind | Metric | Numerator / denominator | Level | Lag | Source & owner |
|---|---|---|---|---|---|
| **Primary (1)** | **Hands-on handling time per ticket**, end to end, copilot-on weeks against copilot-off weeks (queue waiting excluded) | hands-on minutes on tickets closed in the period / tickets closed in the period | 4 Product | weeks (S6 A/B alternates copilot-on and copilot-off weeks for the same agents) | helpdesk timestamps; Head of Support. Base: ~10 min a ticket (`Inputs!G7`), expected cut ≈ 20 % (`Flow!D15`) |
| **Guardrail** | **Urgent tickets routed automatically to the wrong desk** | urgent tickets (urgency `high`) whose first desk is wrong / urgent tickets routed automatically | 3 Guardrails | days (weekly audit sample) | Re-router corrections + weekly routing audit; Head of Support. Floor: 0 (brief success criterion) |
| **Guardrail** | **Uncaught serious errors added by the copilot**: a wrong payment, amount, status or deadline that reaches a merchant, or an urgent ticket left in the wrong desk | serious errors found in the weekly QA sample and in complaints / tickets handled with the copilot | 3 Guardrails | days to weeks | QA sample + seeded errors (hypothesis 4); Head of Compliance. Bar: no worse than the sizing base per category — 0.05 % payment status, 0.12 % disputes, 0.08 % technical and compliance (`Flow!D19:D21`) |
| **Guardrail** | **QA score of sent replies** | sum of QA scores on the weekly sample / replies scored | 4 Product | weeks | existing QA rubric of the support team; Head of Support. Bar: not lower than in copilot-off weeks (baseline measured first, `01_problem_statement.md` §1) |
| **Counter-metric** | **Repeat contact within 7 days** — the merchant writes again on the same issue (Goodhart on handling time: closing fast without solving) | tickets followed by a new ticket on the same issue within 7 days / tickets closed | 4–5, lagging | 1 week | helpdesk thread links; Head of Support |
| **Counter-metric** | **Drafts on the wrong payment validated unread** — approved with no edit, the payment later found wrong (Goodhart on draft acceptance: automation bias) | drafts approved unedited whose transaction was wrong / drafts approved unedited | 3–4, lagging | weeks (found by the QA sample, seeded errors or a merchant's reply) | QA sample + seeded wrong drafts; Head of Compliance |

- **Segments reported** (from the S3 data audit, `governance.md` Session 3): language (French · English · other) · desk (payments · disputes · technical / API · compliance · Re-router) · ticket difficulty (clean · hard: vague wording, odd reference, thread, injection) · urgency (`high` · other) · agent seniority (new · experienced — the published gain concentrates on novices, `03_user_research.md`).
- **Fairness metrics, named:** *selection-rate parity* — does each language get a draft (rather than a hand-over) at the same rate? — and *equal error rates across segments* — is the Re-router correction rate, and the serious-error rate, the same for French and English tickets?
- **Harm threshold** that stops the rollout, per segment, with its owner *(copied into `governance.md`, Session 5)*: if, for any language or desk, the **repeat-contact rate within 7 days** is higher in copilot-on weeks than in copilot-off weeks for two consecutive weeks, or the **Re-router correction rate** rises above today's misroute rate (1 in 7, `Flow!D26`), drafting drops to "context only" (no draft) on that segment until the gap is explained. Owner: Head of Support, with the Head of Compliance for disputes and compliance; reviewed monthly.
- **How it could be gamed → the repair:** agents send drafts unread to cut handling time → the QA-score guardrail, the "validated unread" counter-metric and seeded wrong drafts catch it; tickets are closed before the issue is solved → the 7-day repeat-contact counter-metric catches it; hard tickets are pushed to the Re-router to keep the error rate low → selection-rate parity by segment and the share of tickets handed over catch it.

## 4 · Derive the business metrics — three, with expected effects (the oral)
`⟨waits for evals/report_v0.md: the expected effects derive from the S4 number × the cost line; the baselines below are the sizing cells we will use⟩`

| Business metric | Baseline (from `02_sizing.xlsx`) | Expected effect (from `evals/report_v0.md` × the cost line) | Lag | Read date | It is a hypothesis about… |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | *(at least one stated as a non-effect with a stop band)* |

Candidate baselines: agent cost per ticket €7 (`Inputs!D9`) and volume 36,900 tickets a month (`Inputs!D6`); misroutes 1 in 7 today (`Flow!D26`), 8 % on copilot-handled tickets (`Flow!D27`), €3 per hand-over (`Flow!D28`); AI cost €0.005 per ticket (`Flow!D24`).

The tree (component → product → business): `⟨after the report⟩`

## 5 · Make the judge trustworthy — the evaluation plan
- **Eval-set v1:** `evals/eval_set_v1.csv`, 100 cases (200 in production), stratified by language, desk, urgency and difficulty, with disputes near a deadline oversampled; inputs drafted with an AI assistant and tagged in every row, labels written by hand before any run. The 30-case sample fixed in `evals/README.md` is the golden set that never changes.
- **Grading guideline:** `evals/README.md` — verdicts PASS / FAIL / ESCALATE, six binary criteria with boundary examples, written on 13 November before anyone grades. Two graders on the same 30 rows: agreement = `⟨after grading⟩` %.
- **Judge:** model `⟨to choose: a family other than the drafter's mistralai/mistral-nemo⟩`, prompt in `evals/judge_prompt.txt` (the closed rubric of the optional Judge, node 11 of flow v2); human–judge agreement on the same 30 = `⟨after grading⟩` %; known biases: `⟨after grading⟩`; re-aligned on `⟨date⟩`.
- **Cadence:** eval-set + judge at every change of model, prompt, rule or threshold; human QA sample weekly.
- *Optional, not graded* — red rows: `evals/adversarial_v0.csv`; assertions: `evals/promptfooconfig.yaml`.
