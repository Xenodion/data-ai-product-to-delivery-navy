# NAVY — Payments support reply copilot

**Course:** Data & AI Product: From Diagnosis to Delivery (MSA-DAT07-04) · Albert School · shared project with Agentic Workflows
**Cohort:** M2-INTER-2

## Team
| Name | Git handle | Also in the Agentic Workflows team? |
|---|---|---|
| Alexandre Waerniers | Xenodion | yes |
| Vincent Lamy | Vincent-20-100 | yes |
| Nahel Bachiri | nahelbachiri-oss | yes |
| Yoni Mahieddine | InoyDev | yes |

## Our agent
- **Starting point:** P2 — Agent-assist copilot for a B2B payments fintech
- **The company:** Keelpay, a B2B payments fintech with ~800 merchant customers, ~12,000 support tickets per month (a high share of "where is my money" and dispute questions) and ~18 support agents (team size not given in the project document: our estimate, see `01_problem_statement.md`)
- **The job, in one sentence:** When a merchant ticket about a payment, a payout or a dispute reaches a support agent, the agent pre-reads the merchant's account, transactions and past tickets and drafts the reply with links to the matching transactions and the PSD2 / KYC constraints flagged, producing a draft that the human agent edits and sends.
- **Trust level per step:**
  - Pre-read the account and match the transaction: **L1** (suggests, shows its evidence)
  - Flag PSD2 / KYC constraints: **L1** (flags, never decides)
  - Draft the reply: **L2** (a human reads and approves every reply); drafts below the groundedness threshold are shown as "context only", not as a reply
  - Send to the merchant: **human only** — the agent has no send tool
- **One thing it must never do:** send anything to a merchant — it drafts, a human sends.

## Repository structure
One numbered file per session. Every member authors commits in at least four of the numbered files.

| File | Session | Status |
|---|---|---|
| `00_pitch.md` | before S3 — only if you bring your own idea | not needed — we start from P2 |
| `01_problem_statement.md` | S1–S2 — Assignment 1 | draft v0 — to review |
| `governance.md` | created for Assignment 1, one line added every session | draft v0 — Session 1 filled |
| `02_sizing.xlsx` | S2 — Assignment 2 | to do |
| `02_investment_memo.md` | S2 — Assignment 2 | to do |
| `03_product_brief.md` | S3 | to do |
| `04_architecture.md` | S4 | to do |
| `05_metrics.md` | S5 | to do |
| `06_ab_protocol.md` | S6 | to do |
| `07_operations.md` | S7 | to do |
| `08_launch_memo.md` | S8 | to do |
| `spec.md`, `product_brief.md` | final | to do |
| `/prototype`, `/evals` | from S4 | to do |

## Rules
- Commit with your own Git account: the individual question at the oral is about a commit you signed.
- Tag the final version `v1.0` before the first oral of your cohort. No commits after the first oral starts.
