# Product Brief Appendix

Reference: 3 November 2026. RICE estimates below are prioritization judgments, not measured results; revisit after implementation estimates and task observations.

## As-is and target process

Assumption: 10 minutes per ticket; 15/45/40% slices are scenario inputs.

| Step | Indicative as-is | Decision | Why not automate more? | Target measure |
|---|---|---|---|---|
| Read | 1.5 min with assignment | Assist with Qualifier Model | Meaning/ambiguity errors; text is not business truth | Residual time, validity, exact extraction |
| Assign | Within 1.5 min | Automate supported scope with Routing Node rules | Wrong desk causes rework; unsupported intent needs qualification | Qualification time, initial desk, post-rule coverage |
| Search | Within 4.5 min with drafting | Automate lookup, assist selection | Merchant-scoped match; plausible candidate may still be wrong | Search/selection time, conflicts, wrong payments |
| Draft | Within 4.5 min | Augment with grounded draft | Open context and quality not reducible to classification; no unauthorized promise | Editing time, QA, supported claims |
| Review/send/back office | 4 min | Keep human | Accountability and monetary/regulatory consequences | Review time, caught errors, unchanged sends, serious errors |
| Trace | Included in wrap-up | Automate | Deterministic function; does not replace quality evaluation | Event coverage/correlation |

In sizing base, residual A = 1.5 × (1 − 0.55 × 0.80) = 0.84 min; residual B = 4.5 × (1 − 0.33 × 0.92) = 3.134 min; other work = 4 min. Indicative total is 7.974 min on an assisted ticket, an assumption rather than a measurement. Adoption scales overall gain. The experiment must include triage, payment selection, and rework without double-counting savings.

Course ML-potential criteria support automation for bounded, verifiable tasks and assistance where context/judgment matters. JSON validity is verifiable; reply truth/usefulness needs evidence and a QA rubric. Thus rules assign, deterministic lookup retrieves facts, and a human controls sending.

## Eight candidates and RICE

RICE = monthly reach × impact × confidence / person-weeks. Ticket reach includes the agent screen; 28,800 and 7,200 are scope assumptions, not measured distributions. Impact, confidence, and effort are judgments to validate.

| Rank | Feature | Reach | Impact | Confidence | Effort | RICE | Decision |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | Human decision and history | 36,000 | 2 | 80% | 3 | 19,200 | MUST |
| 2 | Evaluation and observability | 36,000 | 1 | 80% | 2 | 14,400 | MUST |
| 3 | Qualification/assignment | 36,000 | 2 | 50% | 5 | 7,200 | MUST |
| 4 | Grounded context and reply | 28,800 | 3 | 50% | 6 | 7,200 | MUST |
| 5 | Autonomous replies (bad idea) | 36,000 | 2 | 50% | 5 | 7,200 | WON'T |
| 6 | Overview refinements | 36,000 | 0.5 | 50% | 2 | 4,500 | SHOULD |
| 7 | Advanced urgency handling | 7,200 | 2 | 50% | 2 | 3,600 | SHOULD for demo |
| 8 | Ledger writes (bad idea) | 7,200 | 2 | 50% | 4 | 1,800 | WON'T |

Tied ranks do not imply a value difference. A forbidden feature is not made acceptable by its score. Qualification/assignment and grounded context/drafting test economic value and remain MUST despite lower confidence. Minimal decision workspace and measurement are needed to test this value and cannot be cut.

## MoSCoW

**MUST (4):** qualification/assignment; grounded context/reply; human decision/history; evaluation/observability.

**SHOULD:** UX/Overview refinements, advanced urgency, multi-agent, detailed version comparison. **COULD:** richer tone suggestion and cadence control from the front end. Unknown sentiment never blocks routing.

**WON'T in v1, dated 3 November:** autonomous send; refund/ledger write/unfreeze; automatic multi-intent split; merchant voice/chat; regulatory advice/decision; external API receiving real Keelpay data.

Minimal Overview, real injection, FIFO, and visible wait are demo delivery requirements, not extra product brief MUSTs. Production urgency requirements still need definition even if advanced demo controls are SHOULD.

## Model choice by task

Routing Node and logs are deterministic; Lookup Node supplies facts; Retrieval Node supplies sources; Qualifier Model and Drafter Model handle language tasks only. Compare the fine-tuned Qualifier Model with rules/classical ML and prompting. Prompt the Drafter Model with context; fine-tuning it is outside this project. A reply is useful only with the right case and relevant evidence.

## Two decisions to defend

**Flip assumption:** the flow must save enough active time net of triage/review/rework to beat non-AI integration under stated economic assumptions while preserving QA; this threshold is not model accuracy.

**Hard cut:** autonomous sending might save review time but removes human control over wrong-payment errors; it remains excluded despite potential RICE reach.
