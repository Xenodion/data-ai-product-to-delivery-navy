# 03 — Product brief (v1)

**Team:** NAVY · **Agent:** Keelpay agent-assist copilot (routing + drafting) · **Last updated:** 31 October 2026

> Built on the frozen brief (README), the problem statement (`01`) and the sizing (`02_sizing.xlsx`, `02_investment_memo.md`). Minutes below use the sizing's base case; the ~10 minutes of handling time per ticket is a guess (`00_pitch.md`).

## 1. Framing and success criterion

| | |
|---|---|
| **Proposal** | P2 universe, redefined: Keelpay, a B2B payments fintech (see README). |
| **Target user** | The Keelpay support agent who handles merchant tickets (payment status, disputes, technical / API, compliance). |
| **Target trust level** | Routing **L3** (automatic, with sampling and a human for `UNDEFINED` and critical tickets); drafting **L2** (a support agent approves and sends every reply). |
| **The fatal trap** | A misread message looks handled: an urgent ticket (dispute deadline, compliance hold) sits in the wrong desk, or a confident draft is built on the wrong payment. |
| **Constraint** | Tickets carry merchant and payment data and never leave Keelpay's cloud: no external model API, for the router or the drafter. |
| **Do-nothing** | Volume grows with the merchants; reading, routing and writing time grows with it and about 1 ticket in 7 keeps bouncing between desks (`01`, section 7; `02_sizing.xlsx`, do-nothing line). |
| **Decision and owner** | Head of Support and Head of Compliance decide how much routing is automatic and at which thresholds; stage 2 is a conditional go (`02_investment_memo.md`). |
| **Rollback trigger** | Switch routing back to proposals only if an urgent ticket is auto-routed to the wrong desk in a weekly audit sample, or incremental serious errors exceed 0.1 % of tickets; the switch is owned by the Head of Support. |
| **Reference workload** | ~30,000 tickets a month, ~10 minutes of hands-on handling per ticket (guess), 38 support agents (guess). |
| **Where it lives** | Inside the helpdesk the support agent already uses: a side panel on each ticket showing what the copilot read, the path it took, the sources and the draft. The S4 prototype is a Streamlit app that mimics it. |

**Success criterion (one, for the S4 prototype).**
- **Metric:** share of gold-set tickets sent to the right desk on the first pass by the router plus the decision table, while at least half of the tickets are routed automatically (a router that sends everything to triage would pass accuracy alone).
- **Threshold:** at least 90 % first-pass correct (today 6 in 7, about 86 %; the sizing's base case is 92 %, and its flip point on routing is about 90 %) and at least 50 % routed automatically (the sizing assumes 55 %).
- **Guardrail:** no urgent ticket routed automatically to the wrong desk; every doubtful urgent ticket ends as `UNDEFINED` or in triage.
- **Data:** a gold set of at least 200 synthetic tickets, French and English, at least a third hard cases, labelled by a teammate who does not tune the model.
- **Date:** end of S4.

## 2. To-be process and trust level per step

Minutes are the base case of the sizing at full adoption: handling time 10 → 8.55 minutes (−14.5 %).

| Step | As-is (human) | To-be step | Tool / ladder rung | Trust level | Human time after |
|---|---|---|---|---|---|
| **1. Read** | 1.5 min (with step 2) | The router reads the message and returns a JSON (`UNDEFINED` when unsure) | Rung 3: a small fine-tuned model if it beats the prompted one, otherwise the prompted model | **L1**: suggests, the rules in step 2 check it | 0.96 min (with step 2) |
| **2. Route** | (in step 1) | Decision table on the JSON plus a criticality score; clear tickets routed automatically, `UNDEFINED` / low-confidence / critical tickets to human triage | Rung 1: rules | **L3** with sampling | (in step 1) |
| **3. Look up** | 4.5 min (with step 4) | Matching transactions and history, read-only, limited to the merchant | Rung 1: exact query | **L1**: shows the evidence, decides nothing | 3.59 min (with step 4) |
| **4. Draft** | (in step 3) | Cited draft from retrieval over the desk's policies and read-only queries | Rung 3: prompted model with retrieval | **L2** | (in step 3) |
| **5. Review and send** | 4.0 min (with back-office and wrap-up) | A support agent reads, edits, reroutes if the desk is wrong (redrafted once), and sends | Human in the loop | **Human** | 4.0 min |
| **6. Log and feedback** | (in step 5) | Every reading, path, edit and reroute is logged and becomes a label | Rung 1: telemetry | **L4** | 0 min |
| **TOTAL** | **10 min** | | | | **8.55 min (−14.5 %)** |

The model ladder, one rung per part: rules for routing, lookup and logging; a pretrained model for reading and drafting; the router climbs from rules and classical ML to a fine-tuned small model only if the rungs below fail the criterion on the gold set, and only against the prompted open-source model in our own cloud (no external API: tickets never leave Keelpay's cloud).

## 3. The eight candidate features

1. **Router (best of options A–D):** reads the message and returns the JSON, `UNDEFINED` when unsure; the fine-tuned model is the candidate under test.
2. **Decision table and criticality score:** fixed rules on the JSON (required fields per request type, nulls, `UNDEFINED`, amount, urgency, deadline) decide auto-route, triage or critical.
3. **Lookup and cited draft:** deterministic transaction and history lookup, then a draft with retrieved sources and read-only queries, shown in a minimal side panel.
4. **Gold set and feedback logger:** the 200-ticket gold set, plus reroutes and edits logged as labels.
5. **Review screen:** the richer version of the panel: what the copilot read, the path taken, sources side by side, one-click reroute.
6. **Sentiment and tone suggestion:** flags an irritated merchant and suggests a tone.
7. **Flawed feature 1, autonomous replies (L4):** the copilot answers simple payment-status tickets without a person.
8. **Flawed feature 2, ledger write access:** the copilot reopens a payout or applies a refund.

## 4. RICE prioritisation (sorted)

RICE = Reach × Impact × Confidence ÷ Effort (person-weeks). Confidence is 50 %, 80 % or 100 %. All inputs are our judgement.

| Rank | Feature | Reach (/mo) | Impact | Confidence | Effort (wks) | RICE | Decision |
|---|---|---|---|---|---|---|---|
| 1 | Decision table and criticality score | 30,000 | 2.0 | 100 % | 1.5 | **40,000** | **MUST** |
| 2 | Gold set and feedback logger | 30,000 | 1.0 | 80 % | 1.5 | **16,000** | **MUST** |
| 3 | Review screen | 30,000 | 1.0 | 80 % | 3.0 | **8,000** | **SHOULD** |
| 4 | Router (best of A–D) | 30,000 | 2.0 | 50 % | 4.0 | **7,500** | **MUST** |
| 5 | Lookup and cited draft | 24,000 | 3.0 | 50 % | 6.0 | **6,000** | **MUST** |
| 6 | *Autonomous replies (flawed)* | 30,000 | 2.0 | 50 % | 5.0 | **6,000** | **WON'T** |
| 7 | Sentiment and tone suggestion | 30,000 | 0.5 | 50 % | 2.0 | **3,750** | **COULD** |
| 8 | *Ledger write access (flawed)* | 6,000 | 2.0 | 50 % | 4.0 | **1,500** | **WON'T** |

## 5. MoSCoW board

| MUST (4) | SHOULD | COULD | WON'T (out of scope, dated 31 October 2026) |
|---|---|---|---|
| 1. Router, best of A–D *(the routing criterion; the fine-tuned model is the experiment)* | 1. Review screen | 1. Sentiment and tone suggestion | 1. Autonomous replies to merchants (no L4 send) |
| 2. Decision table and criticality score *(the guardrail)* | | | 2. Ledger write access (no payout, refund or unfreeze) |
| 3. Lookup and cited draft *(the L2 core)* | | | 3. External model API (tickets stay in Keelpay's cloud) |
| 4. Gold set and feedback logger *(no eval, no MVP)* | | | 4. Dispute arbitration with the card schemes, legal or regulatory advice |
| | | | 5. Voice or chat channels, a merchant-facing chatbot |

## 6. The two key sentences

**Flip assumption.**
> The two MUST features that carry the flip are the router and the cited draft. The router tests routing: at least 90 % first-pass accuracy with at least half of the tickets routed automatically and no urgent ticket mis-routed, and, if the fine-tuned model is to be kept, that it beats the prompted one by a margin fixed in advance. Together with the draft, this has to bring total time saved to about 14 % of handling time, the point where the copilot beats the rules-only attach in `02_sizing.xlsx` (base case 14.5 %, published benchmark about 13 %). The router is a MUST although it ranks fourth on RICE, because its confidence is low and the whole stage-2 decision depends on it.

**The cut that hurt the most.**
> Autonomous replies to simple "where is my money" tickets: they are the most attractive saving, since a payment-status ticket needs little judgement, but cutting them was necessary because a wrong transaction match sent without a person is the trap of this product, and our routing is already automatic.

## 7. Data, in six lines

1. **Provenance:** synthetic tickets written by the team and a language model, with a seeded merchant and transaction ledger; no real merchant data.
2. **Volume and labels:** at least 200 gold tickets, labelled by a teammate who does not tune the model, with a written guideline.
3. **Coverage:** French and English, the four request types, at least a third hard cases; English and rare dispute types are the weak point.
4. **Rights:** synthetic data, so no personal data; in the real company the B2B contract and a legal basis decide what tickets may train.
5. **Leakage:** train and test separated, and retrieval limited to the merchant of the ticket (merchant A's data never reaches merchant B's draft).
6. **Freshness:** policies and ledger are versioned; the router is re-evaluated at every taxonomy or model change.

## 8. What this brief hands to the next sessions

- `spec.md` (S4): the six steps with inputs, outputs and fallbacks (`UNDEFINED` or confidence below the threshold → triage).
- `04_architecture.md` (S4): the decision table format, the retrieval, the read-only query guardrails, the logs.
- `05_metrics.md`, `06_ab_protocol.md` (S5–S6): the per-step metrics and the copilot-on / copilot-off weeks.
