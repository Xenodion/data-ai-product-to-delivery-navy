# 03 — Product brief · Keelpay Support Copilot · v2

> Session 3. v1 framed in class; v2 completed after user research and usability testing.
> Built on `01_problem_statement.md`, `02_sizing.xlsx`, `02_investment_memo.md`, and `03_user_research.md`.

**Team:** NAVY · **Starting point:** P2 (Agent-assist copilot, B2B fintech) · **Version:** v2 — 3 November 2026

---

## 1. Problem, user, do-nothing *(from 01)*

- **Problem in one sentence (with a number):** At Keelpay (~2,500 merchants, ~36,000 tickets/month, French & English), support agents spend ~15 % of handling time reading and routing tickets, and ~45 % finding the payment and drafting replies; about 1 ticket in 7 first lands in the wrong desk, and urgent chargebacks risk missing hard deadlines.
- **User (persona):** A Keelpay support agent on one of the four desks (`payments`, `disputes`, `technical_api`, `compliance`) — *Goal:* resolve merchant inquiries quickly on the correct transaction without manual hunting — *Pain:* decoding ambiguous free text, disjointed ledger lookups, and receiving misrouted tickets.
- **Do-nothing baseline:** Ticket volume grows with merchant acquisition (+20 %/year), requiring 9 additional agents to hold SLAs; 1-in-7 tickets continues to bounce between queues with ongoing risk of SLA penalties.

---

## 2. The process — as-is and to-be

Handling time baseline ≈ 10 min/ticket. Minutes per step derived from scenario shares (15/45/40 %). Minutes after reflect our sizing base case (~20 % net time saved across the flow).

| # | Step | Who today | Minutes | Error rate | Cost of an error | Automate / augment / keep human | Trust level | Minutes after | Metric for this step |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Read ticket** | Support agent | 1.5 (with step 2) | Feeds step 2 misrouting | Included in step 2 | **Automate** (Classifier): extract fields; ambiguous/trap tickets go to `UNDEFINED` | L1 (rules verify output) | ≈ 0.8 (steps 1–2) | JSON validity; extraction accuracy on intent/urgency |
| 2 | **Route to desk** | Support agent | (in step 1) | 1 in 7 misrouted (~14.3 %) | ~€3 reroute rework; €150–€400 if urgent deadline missed | **Automate with rules** on clear tickets; **Keep human** for triage (`UNDEFINED`) | L3 (sampled audit); human triage on flag | (in step 1) | First-pass desk accuracy; share auto-routed (~50 %); urgent misroutes |
| 3 | **Find payment & history** | Support agent | 4.5 (with step 4) | Unmatched / wrong transaction | €150–€400 (reputation / dispute penalty) | **Automate** (Lookup Node): exact merchant-scoped ledger query | L1 (read-only, merchant-scoped) | ≈ 3.1 (steps 3–4) | Matching transaction attached; candidate disambiguation |
| 4 | **Draft reply** | Support agent | (in step 3) | Unsupported commitments | Legal & regulatory risk if wrong status/amount quoted | **Augment** (Drafter): cited draft grounded in policy fixtures & transaction context | L2 (human approves every draft) | (in step 3) | Agent edit rate; drafts on wrong payment caught |
| 5 | **Review, edit & send** | Support agent | 4.0 | Human review errors | — | **Keep human**: accountability and customer trust require human approval | Human only (no autonomous send) | 4.0 (unchanged) | QA score; end-to-end active handling time |
| 6 | **Telemetry & feedback** | — (new) | 0 | — | — | **Automate**: log edits, reroutes, and latency | L4 | 0 | Share of edits & reroutes captured for monitoring |
| | **Total** | | **10.0 min** | | | | | **≈ 8.0 min (~20 % saved)** | |

- **Where the pain sits (the two steps):** Step 1–2 (reading and misrouting) and Step 3–4 (hunting transactions and drafting).
- **The way back to a person (designed first):** Any ambiguous extraction routes to human qualification; any draft can be edited; a single-click desk correction invalidates the draft and reroutes; a second reroute transfers to manual triage.
- **Where the governance line sits:** A hard stop before sending. The copilot has **no send tool** and **no financial write tool** (L2).

---

## 3. Features — RICE and MoSCoW

| Feature | Reach / month (from sizing) | Impact (0.25–3) | Confidence (50/80/100 %) | Effort (person-weeks) | RICE | MoSCoW |
|---|---|---|---|---|---|---|
| **Human review & explicit send** | 36,000 | 2.0 | 80 % | 3 | 19,200 | **MUST** |
| **Telemetry & observability** | 36,000 | 1.0 | 80 % | 2 | 14,400 | **MUST** |
| **Qualification & deterministic routing** | 36,000 | 2.0 | 50 % | 5 | 7,200 | **MUST** |
| **Grounded context & cited draft** | 28,800 | 3.0 | 50 % | 6 | 7,200 | **MUST** |
| **Autonomous sending** | 36,000 | 2.0 | 50 % | 5 | 7,200 | **WON'T** |
| **Queue wait-time & FIFO overview** | 36,000 | 0.5 | 80 % | 2 | 7,200 | **SHOULD** |
| **Advanced urgency detection & escalation** | 7,200 | 2.0 | 50 % | 2 | 3,600 | **SHOULD** |
| **Ledger write / refund trigger** | 7,200 | 2.0 | 50 % | 4 | 1,800 | **WON'T** |

- **MUST (4):** (1) Qualification & routing; (2) Grounded context & cited draft; (3) Human review, editing & send gates; (4) Telemetry & evaluation.
- **SHOULD:** Queue wait-time display with oldest-first sorting; advanced urgency badge filtering.
- **COULD:** Richer tone suggestions based on sentiment.
- **WON'T this time (≥ 5 — out-of-scope list):**
  1. Autonomous sending without agent confirmation.
  2. Autonomous ledger actions (refunds, payout unfreezes, balance adjustments).
  3. Automatic splitting of multi-intent tickets.
  4. Customer-facing voice or real-time chat interface.
  5. Sending real customer tickets to external unapproved APIs.
- **The feature that tests our flip assumption, and why it is a MUST:** *Grounded context & cited draft.* It directly targets the 45 % drafting slice to deliver the net handling time savings required to hit our 13.5 % economic flip point.
- **The cut that hurt the most:** Autonomous replies for simple payment-status tickets. It had high reach, but was cut because an autonomous reply on a mismatched payment destroys customer trust.

---

## 4. Data *(from governance.md audit)*

- **Sources:** Synthetic ticket benchmark (3,205 tickets) + synthetic ledger and policy fixtures. No real customer PII.
- **Volume & labels:** 1,922 train, 293 val, 610 natural test, 380 trap test. Hand-labeled eval-set v0 (20 cases).
- **Coverage by segment:** French and English; balanced across payments, disputes, technical, and compliance desks.
- **Legal basis & privacy:** Demo uses synthetic data; production requires GDPR Art. 6 assessment, merchant-level tenant isolation, and a 90-day retention schedule for operational traces.

---

## 5. Model — one rung per part

| Part | Rung (1 rules · 2 classical ML · 3 pretrained model · 4 hybrid) | Why the rung below fails |
|---|---|---|
| **Ticket classifier** | 3 — Pretrained / fine-tuned small language model | Rules and keyword matchers fail on complex phrasing, multilingual text, and multi-sentence context. |
| **Routing decision** | 1 — Deterministic decision table | No learning required; routing policies must be auditable, deterministic, and easily updated by business owners. |
| **Transaction lookup** | 1 — Deterministic database query | Exact database lookup scoped to `merchant_id`; models cannot hallucinate financial records. |
| **Drafting engine** | 3 — Prompted LLM with retrieval augmentation | Static templates cannot combine variable transaction context with policy nuances in natural language. |
| **Telemetry & logging** | 1 — Deterministic logging | Standard telemetry. |
| **Copilot as a whole** | **4 — Hybrid** | Combines deterministic safety and financial accuracy with language understanding. |

---

## 6. Where it lives (integration surface)

- **Surface:** A 3-column side panel embedded in the existing helpdesk workspace (inbox queue on the left, active ticket in the center, copilot assistance card on the right).
- **Speed needed:** Inference must execute while the ticket waits in queue (sub-5s target), so context and draft are ready the instant an agent opens the ticket.
- **Format:** Extracted JSON fields with source highlights, merchant case card, candidate transaction list, and cited draft.
- **Fallback:** If classification fails or returns `UNDEFINED`, the ticket drops seamlessly into standard manual triage.
- **Who sees the log:** Support agents see per-ticket traces; Support Lead reviews weekly QA samples; Compliance has full audit access.

---

## 7. Success criterion — one sentence

> By Session 4 prototype evaluation, on our 20-case eval-set (and scaling to ≥ 200 tickets), the copilot is on track for our **13.5 % net time-saved flip point**: routing at least **50 % of tickets automatically** with misrouting significantly below the 14 % manual baseline, while **0 urgent tickets** are auto-routed to the wrong desk.

---

## 8. Risks and rollback trigger

- **Top risks:**
  1. An urgent chargeback misrouted silently, missing its regulatory defense deadline.
  2. Automation bias: an agent validating a draft grounded in the wrong transaction without reading.
  3. Net handling time saved falling short of the 13.5 % economic flip point due to triage overhead.
- **Rollback trigger (one line):** Instantly revert to manual routing if weekly QA finds urgent tickets auto-routed to the wrong desk, or if post-review serious error rate exceeds 0.1 % — owned by Head of Support.

---

## 9. What the users changed *(v2 post-testing)*

| Change | Evidence (who said / did what) |
|---|---|
| **Visible queue wait time & oldest-first default** | Tester 2 (Support Lead) struggled to identify priority from queue counts alone: *“Show me ticket waiting time directly in the inbox header so I can prioritize oldest tickets first.”* Added wait-time counter and global FIFO ordering. |
| **Explicit transaction candidate confirmation** | Tester 1 (Support Agent) hesitated when multiple matching candidates were listed: *“Make it super obvious which one is currently selected in the draft.”* Added distinct visual candidate tagging and draft re-computation on candidate click. |
| **Draft versioning on desk reroute** | User research feedback: agents noted that reassignment in existing tools wipes draft history. Configured 1-click reroute to archive prior drafts and regenerate fresh drafts for the target desk. |

---

## 10. What they could not decide

- **Acceptable error cost threshold:** Support agents could not determine the exact dollar liability Keelpay can tolerate for a mismatched transaction; this threshold is decided by Finance and Compliance in `02_sizing.xlsx` (€150–€400/error, capped at ≤ 0.1 % serious errors).
- **Model architecture selection:** Users care about interface latency and routing correctness, not whether the extractor is fine-tuned or prompted; this technical trade-off is evaluated in Session 4.
- **Log data retention period:** Support leads wanted indefinite history for training, but GDPR storage limitation (Art. 5) restricts operational retention; Legal/DPO determines the 90-day retention schedule.
