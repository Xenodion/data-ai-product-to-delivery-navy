# 01 — Problem Statement

**Team:** NAVY · **Agent:** P2 universe — agent-assist copilot, B2B payments fintech (Keelpay) · **Last updated:** 3 November 2026

> Every number says where it comes from: **measured**, **analogy** (a comparable, with its source) or **guess** (and how we will test it) — the course's own tags. The company, the starting numbers and the vocabulary are fixed in the README ("frozen brief"). Those numbers are the company's data in our scenario (what a ticket log would give in real life), so they carry the tag **given**, with no test. This file builds on them and does not restate them differently.

> **Status:** v1, one end-to-end flow with two sub-cases (routing and drafting). Euro figures and targets are derived in the S2 sizing (`02_sizing.xlsx`) and the investment memo, not here.

---

## 1. The problem in one sentence

Support agents at Keelpay, a B2B payments fintech handling about 36,000 tickets a month from about 2,500 merchants, spend about 15 % of each ticket's handling time reading a free-text message and routing it, and about 45 % finding the payment and its history and writing the reply; about 1 ticket in 7 first lands in the wrong desk and loses a hand-over, and an urgent ticket in the wrong desk can miss its deadline. Today the support agent does all of this by hand. Success looks like average handling time down, end to end, at a QA score no lower than today's, with no rise in urgent tickets reaching the wrong desk.

| Number in the sentence | Value | Given / measured / analogy / guess | Source or test |
|---|---|---|---|
| Merchant customers | ~2,500 | given | Scenario data |
| Tickets per month | ~36,000 | given | Scenario data (about 14 tickets per merchant a month) |
| Share of handling time: reading and routing (sub-case A) | ~15 % | given | Scenario data |
| Share of handling time: finding the payment and history, and writing the reply (sub-case B) | ~45 % | given | Scenario data |
| Rest of handling time (validating and sending, back-office actions, wrap-up) | ~40 % | given | Scenario data; the copilot does not act on it |
| Tickets first routed to the wrong desk | ~1 in 7 (about 14.3 %, ~5,143 tickets a month) | given | Scenario data |
| Languages | French, English | given | Scenario data |
| Average handling time, team size, cost per support agent | 10 min/ticket, 46 agents, 130 productive h/month | assumption | Derived bottom-up in the S2 sizing, tagged and sourced there |
| Target for handling time | -20.26 % (base case) / -13.32 % (flip point) | analogy & economic hurdle | Set in S2 against published benchmarks (Brynjolfsson, Li & Raymond, QJE 2025: +15 % issues/h ≈ -13 % time) and fixed in S6 |
| QA score | "no lower than today's" | baseline to measure | Baseline to measure before anything else; no drop tolerated |

Handling time means hands-on time and excludes waiting in a queue. Queue waiting (time to first reply) is a separate, secondary indicator; routing errors lengthen it because a ticket waits twice.

---

## 2. Problem tree — from symptom to cause

- **Symptom:** Support agents lose 60 % of their time before answering, and tickets bounce between desks.
- **Problem:** Key facts (intent, transaction ID, urgency) are buried in unstructured text, requiring agents to manually extract facts and cross-check the ledger for every ticket.
- **Root cause (5 Whys):**
  1. *Why does a ticket take long?* — About 60 % of time goes into reading, routing, finding transactions and drafting.
  2. *Why do agents spend 15 % on routing?* — Free-text messages do not indicate the desk; agents read the full message to classify it.
  3. *Why does 1 ticket in 7 go to the wrong desk?* — Complex requests (e.g., chargeback with technical error) confuse manual triage under high queue pressure.
  4. *Why do agents spend 45 % finding transactions and drafting?* — The helpdesk is disconnected from the transaction ledger; agents copy-paste data back and forth.
  5. *Why hasn't this been solved?* — Keyword rules miss subtle intents, and merchants bypass structured web forms.
- **What would fix the cause:** A deterministic rule/lookup layer for transaction attachment + an AI layer for language understanding and draft generation.

---

## 3. Is AI the right tool?

| Question | Our answer |
|---|---|
| **Is there a rule that solves 80 % of it?** | Rules solve exact transaction lookups and intent-to-desk mapping, but fail on free-text ambiguity, multi-lingual messages, and drafting personalized explanations. |
| **Is it a prediction / generation problem, or an organisational decision?** | Extracting intent/urgency is prediction; drafting is generation. The organizational decision (sending the reply, issuing refunds) remains strictly human. |
| **Do we have the data?** | Yes, 3,205 synthetic benchmark tickets with schema validation, plus synthetic ledger and policy fixtures. |
| **What does one error cost — and who pays it?** | Routing error: ~€3 (re-routing rework). Wrong transaction/deadline missed: €150 to €400 (dispute/compliance SLA risk). Controlled by human review (L2). |

**Level chosen:** Hybrid (Rules for deterministic routing and lookup + GenAI for qualification and drafting). Rules alone fail on free-text diversity; autonomous agents (L4/L5) carry unacceptable financial and compliance risks.

---

## 4. Why this agent — the four selection questions

| Criterion | Our answer, one line |
|---|---|
| **High frequency** | Yes, ~36,000 tickets/month (~1,200/day across 4 desks). |
| **Bounded decision space** | Yes, exactly 4 desks, 7 extracted fields, and read-only merchant context. |
| **Measurable success** | Yes, first-pass routing accuracy, average active handling time (AHT), and QA score. |
| **Recoverable failure** | Yes, human review on every draft (L2), single-click reroute with draft re-computation, and explicit human send. |

---

## 5. Press release (Working Backwards)

**PARIS — 15 November 2026.** Keelpay, the B2B payments fintech handling 36,000 merchant tickets a month, today announced that its AI Support Copilot is now in production across all four support desks, reducing merchant response times while maintaining a 100 % human-in-the-loop review standard.

By extracting transaction references from unstructured inquiries and pre-drafting policy-grounded replies, the copilot cuts initial ticket handling time by over 20 % and virtually eliminates the 1-in-7 misrouting penalty. Critically, the system never sends replies autonomously: every transaction match and drafted commitment is verified and approved by a trained support agent.

*"Our merchants operate in fast-moving commerce where a delayed chargeback response or missing payout can jeopardize supplier trust,"* said Marc Delcroix, COO of Maison Verte, a Keelpay merchant customer. *"Keelpay’s support agents now resolve complex payout investigations in minutes rather than hours, with precise transaction references right from the first reply."*

*"The copilot removes the cognitive friction of searching through transaction logs,"* added Keelpay's Head of Support. *"Our agents now spend their active time exercising judgment on sensitive cases rather than hunting for transaction IDs."*

---

## 6. What would have to be true?

| # | Hypothesis | Given / analogy / guess | How we will test it | Session |
|---|---|---|---|---|
| 1 | **Routing safety & silent errors:** An AI classifier can understand free-text tickets and significantly reduce silent misrouting compared to today's baseline (~14 % misrouted), particularly on urgent tickets, by sending ambiguous requests to human triage rather than guessing. | guess | Test on an eval-set of tickets in Session 4; compare error rates in the automated lane against tickets sent to triage. | S4 prototype |
| 2 | **Automated routing share:** The routing rules can automate a substantial portion of tickets (target ~50 %) without human touch, freeing up agent capacity while keeping human triage volume manageable. | guess | Measure the share of automatically routed tickets vs tickets sent to triage on the prototype eval-set. | S4 prototype |
| 3 | **Drafting efficiency:** Providing agents with a pre-drafted reply and attached transaction context saves enough handling time to reach our economic flip point (13.32 % net time saved from sizing), at constant QA score. | analogy (Brynjolfsson et al., 2025) | Time-study on a sample with/without draft in Session 5, then validate in Session 6 trial. | S5 metrics, S6 A/B |
| 4 | **Human verification:** Support agents actively review drafts and catch wrong transaction matches or incorrect policy statements before sending, rather than blindly validating unread text. | guess | Observe agents handling tickets with seeded errors during prototype usability testing. | S4 prototype, S5 counter-metric |
| 5 | **Net workflow gain:** Across the whole flow, the time saved on routing and drafting outweighs the time spent qualifying ambiguous cases and correcting reroutes, beating the do-nothing baseline. | guess | Measure active handling time net of corrections during the full workflow evaluation. | S6 A/B |

---

## 7. Do-nothing baseline

If nobody builds anything over the next 12 months, ticket volume will grow with merchant acquisition (~20 % growth). Without automation, the team would require 9 additional agents just to maintain current SLAs. While agents gain marginal speed through experience (~3 % natural productivity gain, sized at €93k/year in S2), the 1-in-7 misrouting rate persists, leaving urgent chargebacks exposed to queue delays and SLA penalties. The do-nothing option guarantees rising support headcount costs and unmitigated operational risk.

---

## 8. How we decide: staged go

The sizing model (`02_sizing.xlsx`) shows that the copilot has a positive expected value, but the result depends on numbers we can only verify through testing (time saved, routing reliability, agent adoption). The decision is therefore staged:

- **Stage 1 (GO now):** Build the deterministic transaction lookup and context attachment (rules-only, no AI). It is low-risk, positive on its own, and serves as the data foundation for the copilot.
- **Stage 2 (CONDITIONAL GO):** Build the classification and drafting copilot, conditional on Session 4 prototype results confirming that:
  1. The routing logic reduces misrouting compared to the manual baseline without overloading human triage.
  2. The draft noticeably accelerates reply preparation toward our sizing flip point.
  3. Agents effectively catch errors during draft review.
