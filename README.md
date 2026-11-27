# NAVY — a support copilot that routes and drafts

**Course:** Data & AI Product: From Diagnosis to Delivery (MSA-DAT07-04) · Albert School · shared project with Agentic Workflows & LLMOps
**Cohort:** M2-INTER-2

## Team

| Name | Git handle | Also in the Agentic Workflows team? |
|---|---|---|
| Alexandre Waerniers | Xenodion | yes |
| Vincent Lamy | Vincent-20-100 | yes |
| Nahel Bachiri | nbachiri-oss | yes |
| Yoni Mahieddine | InoyDev | yes |

## Our agent

- **Starting point:** P2 — fintech agent-assist, adapted (see [`00_pitch.md`](00_pitch.md)).
- **The company:** Keelpay, a fictional B2B payments company: about 2,500 merchants in France and Belgium, 36,000 tickets a month in French and English, 46 support agents (assumption, [`02_sizing.xlsx`](02_sizing.xlsx)). One ticket in seven first reaches the wrong desk.
- **The job, in one sentence:** when a merchant ticket arrives, the copilot reads it, sends it to the right desk with deterministic rules, gathers the merchant's own payment facts and the approved help content, and prepares a sourced reply that a support agent checks and sends.
- **Trust level per step:** L3 on routing of clear tickets (with a weekly quality sample); L2 on the draft reply; L1 (human only) on unclear tickets, on sending, and on anything that moves money.
- **One thing it must never do:** send a reply, refund, unfreeze an account or write to the ledger on its own. A person sends every answer.

**Decision ([`08_launch_memo.md`](08_launch_memo.md)):** GO for the course demo (delivered) · CONDITIONAL GO for a Keelpay pilot, which is the A/B test of [`06_ab_protocol.md`](06_ab_protocol.md) · NO-GO for a rollout until that test reads.

## Repository structure

One numbered file per session. Every member authors commits in at least four of the numbered files.

| File | Session | Status |
|---|---|---|
| [`00_pitch.md`](00_pitch.md) | before S3 — own adaptation of P2 | done |
| [`01_problem_statement.md`](01_problem_statement.md) | S1–S2 — Assignment 1 | done |
| [`governance.md`](governance.md) | one section per session, S1 to S8 | done |
| [`02_sizing.xlsx`](02_sizing.xlsx) | S2 — Assignment 2 | done |
| [`02_investment_memo.md`](02_investment_memo.md) | S2 — Assignment 2 | done |
| [`03_product_brief.md`](03_product_brief.md) | S3, final v3 | done |
| [`03_ai_lean_canvas.md`](03_ai_lean_canvas.md), [`03_user_research.md`](03_user_research.md), [`03_prototype_link.md`](03_prototype_link.md) | S3 | done |
| [`04_architecture.md`](04_architecture.md) | S4 | done |
| [`05_metrics.md`](05_metrics.md) | S5 | done |
| [`06_ab_protocol.md`](06_ab_protocol.md) | S6 — prove the effect, decide before | done |
| [`07_operations.md`](07_operations.md) | S7 — watch, contain, own | done |
| [`08_launch_memo.md`](08_launch_memo.md) | S8 | done |
| [`spec.md`](spec.md), [`03_product_brief.md`](03_product_brief.md) | final (v3) | done |
| [`prototype/`](prototype/), [`evals/`](evals/) | from S3–S4 | done |

**Evidence files.** [`evals/`](evals/README.md) holds the eval-sets (v0: 50 cases, v1: 100 cases), the two-grader and judge grading, the eval report and three notebooks: segment fairness (S5), A/B sample size (S6) and monitoring thresholds (S7).

**Prototype.** The first clickable mock-up is in [`prototype/copilot_panel/index.html`](prototype/copilot_panel/index.html). The working copilot (API, front end, models, tests) is the Agentic Workflows deliverable, in [`agentic-workflow-subproject/`](agentic-workflow-subproject/README.md). It runs end to end on our laptop on synthetic tickets, with simulated sends; it is not hosted.

**Data.** Keelpay, its merchants and every ticket are fictional. No real customer data is in this repository.

## Rules

- Commit with your own Git account: the individual question at the oral is about a commit you signed.
- Tag the final version `v1.0` before the first oral of your cohort. No commits after the first oral starts.
