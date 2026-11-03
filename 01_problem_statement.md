# 01 — Problem and Product Decision

**NAVY · Keelpay · reference date 3 November 2026.** “Given” means fictional scenario input; “assumption” is an estimate to test; “measured” requires an available artifact.

## Problem

At Keelpay, 36,000 monthly tickets require agents to read/assign (15% of active handling time) and search/draft (45%), while one in seven is initially assigned to the wrong desk. Agents currently reconstruct this information manually. Success means lower end-to-end active time at constant QA without hiding missed urgencies or replies grounded in the wrong payment.

| Baseline | Status | Source/test |
|---|---|---|
| 2,500 merchants; 36,000 tickets/month; FR/EN; 15/45/40% of time; 1/7 misassigned | Fictional scenario input | [README](README.md) |
| 10 minutes/ticket; 46 agents; 130 productive hours/month | Assumption | Comparable-team time/capacity study |
| Costs, growth, adoption, savings, serious errors | Assumption or named analogy | [Sizing](02_sizing.xlsx), S4–S6 tests |

## Persona, journey, and stakeholders

**Working persona:** Support Agent on one of four desks, with multiple open cases. They must identify the issue and payment, follow policy, and reply without losing context across tools. Agent skill and available context vary; this is not a one-person interview profile.

| As-is step | Indicative time on 10 min | Pain/risk | To-be |
|---|---|---|---|
| Read and assign | 1.5 min, derived assumption from 15% | Wrong desk; 1/7 scenario input | Qualifier Model plus Routing Node; targeted qualification |
| Find history/payment and draft | 4.5 min, derived assumption from 45% | Wrong payment, unsupported reply | Merchant-scoped Lookup Node, Retrieval Node, draft or clarification |
| Check, back-office action, send, close | 4 min, derived assumption from 40% | Rushed review, incorrect action | Human decision, sources and gates; no financial write by copilot |

Per-error cost and time savings are sizing assumptions, not measured step times. Wait before handling is separate from active time. To-be measurement must include residual reading, qualification, payment selection, editing, and rerouting; it does not assume these disappear.

Support owns rules and quality; Compliance owns sensitive policies and business exposure; NAVY owns contracts, measurement, and recovery; the Support Agent decides on the ticket; the merchant receives a human-reviewed reply. Finance evaluates opportunity cost; DPO/Security review rights, retention, and isolation before a real pilot.

## Problem tree and five whys

Symptom: wasted time and cases changing desks. Problem: useful facts are buried in free text and disconnected from the ledger. Hypotheses to verify: (1) repeated reading/search; (2) unstructured requests; (3) email bypasses forms; (4) restrictive forms may shift cost to merchants; (5) keyword rules and attachment tools are insufficient. These are hypotheses to test with support practice/data, not established causes.

The remedy combines **integration/rules**, which attach context and make deterministic decisions, with **language support**, which reads text and prepares a reply. An autonomous agent choosing tools in a loop is not required.

## Why AI, and where to stop

| Question | Choice |
|---|---|
| Can a rule solve most of this? | It attaches structured references and applies a decision table; free-text variety must be compared with baselines. |
| Predict/generate or decide? | The Qualifier Model classifies and the Drafter Model writes; the Routing Node assigns, and a human approves sending and commitments. |
| What data? | Synthetic benchmark of 3,205 tickets; separate synthetic ledger/KB fixtures for the flow; no real customer data in the demo. |
| What does error cost? | Rework time and possibly a wrong reply or critical delay; category cost assumptions are in sizing. Read-only access and human review do not eliminate risk. |

Compare rules, classical ML, prompted model, and fine-tuned model under the same contract. D-q4 is the best measured candidate against baselines that were run; base Qwen and the prompted alternative comparable to the Drafter Model are not all compared yet. No conclusion that fine-tuning beats prompting is established. Use appropriate validation/holdout for new choices and do not treat consulted test sets as independent confirmation.

The case is frequent, bounded, and measurable: one ticket, seven fields, one desk, read-only context, reviewed reply. Errors can be recovered, but a wrong desk on an urgent case or a wrong payment validated unread remains a residual risk to measure.

## Assumptions to test

| Hypothesis | Test/evidence |
|---|---|
| Qualifier Model merits its place | Compare executed alternatives and prompting; validity, fields, errors, latency/cost on target runtime |
| Rules avoid unnecessary triage | Test desk/priority/payment/draft states, coverage, and post-rule errors; unknown sentiment remains non-blocking |
| Flow reduces human work | Comparable tasks with/without copilot; active time including corrections; blind QA |
| People catch visible errors | Seed controlled errors; observe checking, wrong selection, and unchanged-send acceptance |
| Urgencies are not lost | Detection recall, handling time, escalation; business settings still open |

The 20 S3 cases check the contract; a ~200-case set may explore the flow but cannot certify a 0.1% rare-risk rate. Extraction benchmarks do not provide AHT or reply QA.

## Alternatives and staged decision

No project: experience/macros may improve, and volume may grow. Non-AI alternative: integrate merchant/transaction context. Full copilot: add qualification and drafting, worthwhile only if net gains beat that alternative at constant quality.

GO to build and evaluate the demo; pilot remains conditional on economic, quality, safety, and governance evidence. The active-time threshold comes from sizing under stated assumptions; 90% accuracy or 50% automatic assignment does not replace it. No production deployment is approved.

## Working backwards — launch vision

**Target vision, not a result announcement:** Keelpay provides agents a qualified case and verifiable reply; queues expose wait and unresolved points. Launch is defensible only if measured active time falls at constant QA and urgencies/serious errors stay within agreed limits. Future launch figures and testimonials must come from actual observations; none are invented here.
