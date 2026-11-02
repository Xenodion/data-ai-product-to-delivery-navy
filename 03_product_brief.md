# 03 — Product brief · Keelpay agent-assist copilot (routing + drafting) · v1

**Team:** NAVY · **Starting point:** P2 universe, redefined (frozen brief in the README) · **Version:** v1 — 2 November 2026

> Built on the README (frozen brief), `01_problem_statement.md` and `02_sizing.xlsx` / `02_investment_memo.md`. Tags: **given** (scenario data), **sizing** (a guess from `02_sizing.xlsx`, tested there), **derived** (arithmetic on those), **measured** (synthetic test tickets, `finetuned_llm_classifier`).

## 1. Problem, user, do-nothing
- **Problem in one sentence (with a number):** at Keelpay (~2,500 merchants, ~36,000 tickets a month, French and English), support agents spend ~15 % of handling time reading a free-text ticket and routing it, and ~45 % finding the payment and writing the reply; ~1 ticket in 7 first lands in the wrong desk, and an urgent one can miss its deadline (given).
- **User (persona):** a Keelpay support agent on one of the four desks (payments status, disputes, technical / API, compliance) — goal: get each ticket to the right desk and answer it on the right payment, without decoding a free-text message and hunting for the transaction by hand (derived from the pain and the job in `00_pitch.md`; the interviews confirm or refine it in v2) — pain: rebuilding each ticket's facts (what, which payment, how urgent) by hand, and receiving tickets meant for another desk (given).
- **Do-nothing baseline:** volume grows with the merchant base and so does the reading, routing and writing time, partly offset by agents getting faster on their own (sizing: about 3 % a year, ≈ €93k); 1 ticket in 7 keeps bouncing between desks (`01` §7, `02_investment_memo.md` §4).

## 2. The process — as-is and to-be
Handling time ≈ 10 min a ticket (sizing guess, Inputs row 7). Minutes per step = the given shares × 10 min. Minutes after = the sizing's base case at full adoption (Flow tab).

| # | Step | Who today | Minutes | Error rate | Cost of an error | Automate / augment / keep human (test it fails) | Trust level | Minutes after | Metric for this step |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Read the ticket | Support agent | 1.5 for steps 1–2 (given 15 %) | counted in step 2: a misread shows up as a misroute | feeds step 2 | **Automate** (model). Passes most tests: well-defined input → output, data can be generated, clear labels. Fails "no long chain of reasoning / background knowledge" on hard tickets → `UNDEFINED` | L1 (the rules check it) | ≈ 0.8 for steps 1–2 (derived: 1.5 × (1 − 55 % auto × 80 % cut)) | Exact match per JSON field; valid JSON ≥ 98.5 % (scoring protocol, amended on 1 November 2026 after the val run; results also reported at 99 %); share sent to triage (`UNDEFINED` / `OTHER`) close to the gold labels' — measured on val, 293 synthetic tickets: 16.0 % against 16.7 % in the labels, 100 % of them rightly sent, 95.9 % of the labelled ones caught |
| 2 | Route to a desk | Support agent | (in step 1) | 1 in 7 first lands in the wrong desk (given) | €3 per hand-over (sizing); an urgent ticket missed: €150 / €400 / €300 by category (sizing) | **Automate with rules**, no ML: a decision table on a few fields. **Keep human** for critical tickets: fails "tolerance for error" | L3 with sampling; critical → a human confirms | (in step 1) | First-pass correct desk; share routed automatically; urgent tickets auto-routed to the wrong desk (target 0) |
| 3 | Find the payment and history | Support agent | 4.5 for steps 3–4 (given 45 %) | not measured today (baseline to measure first, `01` §1; the sizing prices only errors added by the copilot) | a reply on the wrong payment: €150–400 (sizing) | **Automate**, no ML: exact query by merchant, ID, date, amount | L1 (read-only, this merchant only) | ≈ 3.1 for steps 3–4 (derived: 4.5 × (1 − 33 % cut × 92 % correctly routed)) | Right transaction attached |
| 4 | Write the reply | Support agent | (in step 3) | not measured today (QA baseline, `01` §1) | wrong status, amount or deadline told to a merchant: legal and reputational (see below) | **Augment**: a cited draft. Fails "tolerance for error" and "explain the decision", so a person approves | L2 | (in step 3) | Edit rate; drafts on the wrong payment validated unread |
| 5 | Validate, send, back-office, wrap-up | Support agent | 4.0 (given 40 %) | not measured today (QA baseline, `01` §1) | — | **Keep human**: promises, refunds and policy fail "tolerance for error" and need a person who is accountable | Human only (no send tool) | 4.0 (not touched) | QA score; handling time |
| 6 | Log reroutes and edits | — (new) | 0 | — | — | **Automate** (telemetry) | L4 | 0 | Share of reroutes and edits captured as labels |
| | **Total** | | **10** | | | | | **≈ 8.0 (≈ 20 % saved, sizing base)** | |

*The eight tests are Brynjolfsson & Mitchell, "What can machine learning do?", Science (2017) — wording to check against the paper.*

**Where the pain sits (the two steps):** step 2 (route) is short but critical — 1 in 7 misroutes, and urgent tickets can miss a deadline; step 3–4 (find the payment, write) is the largest slice (45 %).
**The way back to a person (designed first):** `UNDEFINED`, low-confidence and critical tickets go to human triage before any draft; the receiving agent reroutes in one click and the ticket is redrafted once; a second reroute goes to triage; an agent can ignore the draft or switch the copilot off on a ticket; the Head of Support can switch the whole system back to "reading only" or off.
**Where the governance line sits:** between route and draft on critical tickets (a human confirms the desk), and between draft and send on every ticket (a human only). Owner of the legal and reputational risk: Head of Compliance (`governance.md`, Session 2).

*Trust levels — L1 suggests · L2 drafts, a person approves · L3 acts on a scope, a person samples · L4 acts alone under a threshold.*

## 3. Features — RICE and MoSCoW
Reach from `02_sizing.xlsx` (36,000 tickets a month; 28,800 for the draft, tickets not sent to triage). Impact, confidence and effort are our judgement.

| Feature | Reach / mo | Impact | Conf. | Effort (wks) | RICE | MoSCoW |
|---|---|---|---|---|---|---|
| Decision table and criticality score | 36,000 | 2.0 | 100 % | 1.5 | 48,000 | MUST |
| Gold set and feedback logger | 36,000 | 1.0 | 80 % | 1.5 | 19,200 | MUST |
| Review screen (case card) | 36,000 | 1.0 | 80 % | 3.0 | 9,600 | SHOULD |
| Router (best of options A–D) | 36,000 | 2.0 | 50 % | 4.0 | 9,000 | MUST |
| Lookup and cited draft | 28,800 | 3.0 | 50 % | 6.0 | 7,200 | MUST |
| *Autonomous replies (flawed)* | 36,000 | 2.0 | 50 % | 5.0 | 7,200 | WON'T |
| Sentiment and tone suggestion | 36,000 | 0.5 | 50 % | 2.0 | 4,500 | COULD |
| *Ledger write access (flawed)* | 7,200 | 2.0 | 50 % | 4.0 | 1,800 | WON'T |

- **MUST (4):** router · decision table and criticality score · lookup and cited draft · gold set and feedback logger.
- **SHOULD:** review screen (case card: each extracted field with the passage it comes from, the lookups already run, the path taken, one-click reroute). **COULD:** sentiment and tone.
- **WON'T this time (dated 31 October 2026):** autonomous replies (no L4 send) · ledger write access (no payout, refund or unfreeze) · external model API (tickets stay in Keelpay's cloud) · dispute arbitration, legal or regulatory advice · voice, chat or a merchant-facing bot.
- **The feature that tests our flip assumption, and why it is a MUST:** the router. It ranks fourth on RICE, but its confidence is the lowest and the whole stage-2 decision rests on it (routing accuracy gates the drafting gain).
- **The cut that hurt the most:** autonomous replies to simple payment-status tickets — the biggest saving, but a wrong payment sent without a person is this product's trap.

## 4. Data *(details in `governance.md`, Session 3)*
Synthetic tickets and a seeded ledger, no real merchant data · ≥ 200 gold tickets labelled by a teammate who does not tune the model, with a guideline · French and English, the four desks, ≥ a third hard cases (English and rare dispute types are the weak point) · in the real company the B2B contract and a legal basis decide what may train · train and test kept apart, retrieval limited to the ticket's merchant · ledger and policies versioned, router re-evaluated at every taxonomy or model change.

## 5. Model — one rung per part
| Part | Rung (1 rules · 2 classical ML · 3 pretrained model · 4 hybrid) | Why the rung below fails |
|---|---|---|
| Read (router) | 3 — fine-tuned small model if it beats the prompted one (options A–D, `01` §3) | Measured on 610 synthetic test tickets (`finetuned_llm_classifier/docs/baseline_results.md`). **Rules** fail: 44.6 % right desk, 33.5 % of urgent tickets in the wrong desk. **Classical ML** (TF-IDF + logistic regression) passes the 90 % bar (91.6 %) but fails the guardrail and the extraction: 6.6 % of urgent tickets in the wrong desk (target 0), amount exact in 80.2 % of tickets, transaction ID in 89.5 %. The model must beat it on those |
| Route + criticality score | 1 — decision table | Nothing below rules; no learning needed for a decision on a few fields |
| Look up | 1 — exact query | Nothing below rules |
| Draft | 3 — prompted model with retrieval | Macros and templates cannot combine this merchant's transactions with the desk's policy in a free-text reply; classical ML does not generate text |
| Log | 1 — telemetry | Nothing below rules |
| **The copilot as a whole** | **4 — hybrid** | |

## 6. Where it lives (integration surface)
Side panel on each ticket in the helpdesk the agent already uses (the S4 prototype is a Streamlit app that mimics it) · speed needed: the reading must be done before an agent opens the ticket — it runs on arrival, while the ticket waits in the queue; measured: about 6 s per ticket for the fine-tuned router on one T4 GPU (293 predictions in 30 min, `finetuned_llm_classifier/docs/compact_variants.md`) · format: the JSON, the case card and the cited draft · fallback: `UNDEFINED` or a copilot failure → the agent works the ticket as today · who sees the log: the agent (per ticket), the Head of Support (weekly audit sample), an auditor (full log).

## 7. Success criterion — one sentence
> By 6 November 2026, on a gold set of ≥ 200 synthetic tickets (French and English, ≥ a third hard), the router and the decision table send **at least 90 %** of tickets to the right desk on the first pass while routing **at least 50 %** automatically — and **no urgent ticket** is routed automatically to the wrong desk.

**How this threshold links to the flip point.** The prototype runs on synthetic tickets, so it can measure routing but not time saved. In the sizing (Flow tab), routing 50 % automatically saves 15 % × 50 % × 80 % = **6.0 %** of handling time, and 90 % correctly routed lets drafting save 45 % × 90 % × the drafting cut. The flip point (**13.5 %**, `02_investment_memo.md` §2) is reached if the cited draft cuts the find-and-write time by **at least ≈ 19 %** (derived; the sizing's base guess is 33 %, measured in S5–S6). Below 90 % or 50 %, the drafting cut needed rises.

## 8. Risks and rollback trigger
- **Top risks:**
  1. An urgent ticket silently routed to the wrong desk.
  2. A draft on the wrong payment validated unread (automation bias).
  3. Time saved below the 13.5 % flip point: the base case (≈ 20 %) sits above the published benchmark (+15 % issues per hour ≈ −13 % time per issue, Brynjolfsson, Li & Raymond, *QJE* 2025).
  4. The fine-tuned router does no better than the prompted model (a valid outcome: we keep the prompted one).
  5. The MVP's temporary hosted model on synthetic tickets is mistaken for the production design (dated exception, `governance.md`, Session 3).
- **Rollback trigger (one line):** switch routing back to proposals only if a weekly audit sample finds an urgent ticket auto-routed to the wrong desk, or incremental serious errors exceed 0.1 % of tickets — owned by the Head of Support.

---
*v2 only — after the users (A3-7, #12)*

## 9. What the users changed
| Change | Evidence (who said / did what) |
|---|---|
| | |

## 10. What they could not decide
…
