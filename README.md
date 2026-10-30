# NAVY — Keelpay agent-assist copilot

**Course:** Data & AI Product: From Diagnosis to Delivery (MSA-DAT07-04) · Albert School · shared project with Agentic Workflows
**Cohort:** M2-INTER-2

## Team
| Name | Git handle | Also in the Agentic Workflows team? |
|---|---|---|
| Alexandre Waerniers | Xenodion | yes |
| Vincent Lamy | Vincent-20-100 | yes |
| Nahel Bachiri | nahelbachiri-oss | yes |
| Yoni Mahieddine | InoyDev | yes |

## Our agent: the frozen brief (read this first)

> **Source of truth.** This section is the definitive starting brief of NAVY, frozen on 30 October 2026. Every other file must be consistent with it. If a file disagrees (numbers, company, scope), the file is wrong, not this section. Change this section only with the whole team's agreement, then update the files below in the same commit. The earlier version (800 merchants, 12,000 tickets, 40 % reading, 18 agents, "NO-GO") came from the course proposal P2 and is **superseded**.

We keep from the course proposal P2 only the universe: a B2B payments fintech, an agent-assist copilot that drafts and never sends, a human who validates, trust level L2. The company, scale, pain, job, metric and trap are our own.

### Words we use (the course uses "agent" for two different things)

| Term | Means | Not to be confused with |
|---|---|---|
| **Support agent** | A Keelpay employee who handles tickets | an AI agent |
| **Copilot** | The system we specify: a model plus fixed rules plus a screen. It prepares the case and a draft and never sends. It is what the course calls the "Agent's job" | a support agent; an AI agent |
| **Model** | The small fine-tuned language model inside the copilot: it reads the free-text message and returns a structured JSON | the copilot as a whole |
| **AI agent** (agentic) | A system that chooses its own steps and calls tools in a loop. We do not build one in the first version: the copilot follows fixed steps | support agent |
| **Desk** | One of the specialist teams a ticket is routed to (payments, disputes, technical, compliance) | the NAVY project team |
| **Merchant** | A Keelpay customer; the person who writes the ticket | |
| **NAVY team** | Us, the four students | |

### Keelpay · Agent-assist copilot for a B2B payments fintech

| | |
|---|---|
| **Company** | Keelpay: ~1,500 merchant customers (SMEs and mid-size, France and Belgium), ~20,000 tickets a month in French and English, mostly payment status, disputes, technical / API and compliance questions. |
| **Pain** | Tickets arrive as free text, mostly by email. Before a support agent can answer, they must work out what the message is about, find the payment it refers to, check what was said before and pass it to the right desk: about 45 % of handling time. Roughly 1 ticket in 7 first lands in the wrong desk and loses a hand-over. |
| **Copilot's job** | No customer-facing autonomy. Reads the message, structures the key facts (type of request, payment, amount, urgency), routes the ticket to a desk, pre-reads the matching transactions and drafts the reply. The support agent edits and sends. |
| **Trust level** | L2 throughout: a support agent validates every ticket and every reply. |
| **Primary metric** | Average handling time per ticket at constant quality (QA score). Counter-metric: share of urgent tickets that reach the wrong desk. |
| **The trap** | A misread message looks handled: an urgent ticket (dispute deadline, compliance hold) sits in the wrong desk, or a draft is built on the wrong payment. When unsure, the copilot must say so rather than guess. |
| **Innovative angle** | Anything the copilot cannot determine is marked `UNDEFINED` and left to the support agent, not guessed; the support agent can open any ticket and see what the copilot read. Our A/B alternates copilot-on and copilot-off weeks for the same support agents, not for tickets, because the ticket mix changes day to day. |

### Starting numbers (all assumptions, nothing measured)

| Number | Value |
|---|---|
| Merchants | ~1,500 |
| Tickets a month | ~20,000 |
| Share of handling time spent understanding, finding the payment and routing, before the answer is written | ~45 % |
| Tickets first routed to the wrong desk | ~1 in 7 (about 15 %, ~2,900 tickets a month) |
| Languages | French, English |

Every other number (handling time, team size, costs, benefits) is derived bottom-up in the S2 sizing from these five, tagged measured / analogy / assumption, and never copied from the course examples (Paylio, the sample brief).

### Role of the fine-tuned model, and the sub-project

The model is a small language model fine-tuned to read the free-text ticket and return a strict JSON (`intent`, `sub_intent`, `transaction_id`, `amount`, `currency`, `urgency`, `sentiment`); anything ambiguous is `UNDEFINED`. It is built in `/finetuned_llm_classifier` for the Agentic LLMOps course (its own uv project, see its README). The only interface between the copilot and that folder is the JSON schema: no cross imports. Fixed rules (a decision tree on the JSON) route the ticket; `UNDEFINED` always goes to a support agent. A fine-tuned model has to be shown to beat cheaper options (rules, classical ML, a prompted large model) on a held-out set labelled by someone who did not tune it, otherwise we do not use it.

### Rules for anyone (human or AI assistant) editing this repo

- Do not reuse numbers, names or conclusions from the course's example brief, from `docs/` examples, or from earlier versions of our files.
- Do not add scope beyond the table above (no autonomous sending, no AI agent in v1, no extra channels) without team agreement.
- A number without a tag (measured / analogy / assumption) and a test does not belong in the files.

## Repository structure
One numbered file per session. Every member authors commits in at least four of the numbered files.

| File | Session | Status |
|---|---|---|
| `00_pitch.md` | before S3 — only if you bring your own idea | not needed — we start from P2 |
| `01_problem_statement.md` | S1–S2 — Assignment 1 | v1 — numbers updated after S2 research |
| `governance.md` | created for Assignment 1, one line added every session | Sessions 1–2 filled |
| `02_sizing.xlsx` | S2 — Assignment 2 | v1 — filled (NO-GO) |
| `02_investment_memo.md` | S2 — Assignment 2 | v1 — NO-GO |
| `03_product_brief.md` | S3 | to do |
| `04_architecture.md` | S4 | to do |
| `05_metrics.md` | S5 | to do |
| `06_ab_protocol.md` | S6 | to do |
| `07_operations.md` | S7 | to do |
| `08_launch_memo.md` | S8 | to do |
| `spec.md`, `product_brief.md` | final | to do |
| `/prototype`, `/evals` | from S4 | to do |
| `/finetuned_llm_classifier` | Agentic LLMOps course sub-project (own uv environment, see its README) | in progress |

## Rules
- Commit with your own Git account: the individual question at the oral is about a commit you signed.
- Tag the final version `v1.0` before the first oral of your cohort. No commits after the first oral starts.
