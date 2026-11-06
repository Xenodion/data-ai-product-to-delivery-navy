# Flow v2: node table (working document, v1)

Status: target architecture validated on 6 November 2026; working document, not a course deliverable, not implemented. Diagram: [flow_v2.svg](flow_v2.svg). This table carries the project status. Build order: [task list](../../../specs/013-flow-v2/tasks.md).

This replaces two rules of the 3 November workflow: "the Drafter attempts every ticket" and "every reply passes through the Validator". The root `spec.md`, `governance.md` and `docs/design/copilot-workflow.md` still describe the old rules.

## 1. Agreed rules

- **Workflow, not agent.** The path is drawn in advance. Each desk is a fixed branch: same code path, with its own prompt, tools and policy. No model chooses a tool.
- **Atomic nodes.** One LLM call is one node. Each deterministic step is one node.
- **No evidence, no factual claim.** Node 8 decides between a factual reply, a clarification and no draft.
- **Shared revision budget.** Policy blocks and Judge revisions use one counter, 2 at most, in config. Stop earlier if the same objection returns.
- **Optional Judge.** It sends recommendations back and never approves. Compare 0, 1 and 2 revisions on the frozen evaluation set, then keep it only for a clear gain in sendable drafts against latency and cost.
- **Last gate for every author.** Node 14 runs the same policy code as node 10 on the final text, whether written by a model or a person.
- **Human control.** A person can take a ticket back at any time.
- **Turns.** A merchant reply keeps the same `ticket_id` and raises `turn` by 1. Later turns keep the desk, unless a person changes it, and node 5 loads the earlier turns. Above a configured limit, the ticket goes to the Re-router.
- **Spam has no module.** `docs/label_definitions.md` puts spam and thank-you notes in `OTHER`, which goes to the Re-router, where a person closes it. On val, 19 of 20 `OTHER` tickets stayed `OTHER`; one went to `technical_api`. Real unsolicited spam is barely present in the corpus, so add cases to the evaluation set.

## 2. Ticket envelope

| Field | Required | Note |
|---|---|---|
| `ticket_id` | yes | Same value for every turn of a conversation |
| `turn` | yes | 1, 2, n, one per merchant message. `ticket_id` and `turn` together are the idempotency key. Intake refuses a turn that is not the next one |
| `merchant_id` | yes | Scopes every lookup. Never read from the text or a model. Kept instead of `customer_id` to match the current contract |
| `created_at` | yes | Total age starts here |
| `channel` | yes | The dataset has `formal_email`, `short_email`, `forwarded_thread`, `chat_message` |
| `body` | yes | Untrusted merchant text |
| `subject` | no | Rebuilt into the Qualifier input format: `Subject: ...`, blank line, body |
| `language` | no | Reply language hint; otherwise read from the text |
| `attachments` | no | Metadata only in V1 |

## 3. Exits for unclear tickets

| Case | Destination | LLM calls after detection |
|---|---|---|
| Invalid JSON or missing required field | Error queue, ticket kept | 0 |
| Qualifier down, invalid output, `UNDEFINED`, `OTHER` | Re-router | 0 |
| Human-only list | Human-only queue. **In the architecture, not built in V1** | 0 |
| Evidence gate returns `no_draft` | Validator, with the context, no draft | 0 |
| Spam or thank-you | `OTHER`, then closed by a person, logged | 0 |

Re-router and Validator actions:

1. **Correct and enrich, then re-enter at node 5.** Typed fields only: desk, sub-intent, transaction id, amount, note, each marked `source=human`. Node 3 does not check them and the Qualifier does not rerun. Lookup stays scoped to the merchant. One re-entry at most, shared with the existing rule: a second correction means the person finishes.
2. **Write the reply and send.** The text goes through node 14. This skips the Validator step, so the direct-send rate is tracked.
3. **Close without reply.** Logged with a reason.

Node 14 on human text: a hard block on another merchant's identifiers; other findings can be overridden with a logged reason. The check that each figure is in the evidence applies only to model drafts.

## 4. Nodes: behaviour

Level: L1 suggests, L2 drafts and a person approves every reply, L3 acts on a scope with sampling, L4 acts alone under a threshold, L5 fully autonomous (course project document). Levels are proposals. "Now" compares with `flow/` today.

| # | Node | Type | Pattern | Level | Now | Input | Output | On failure |
|---|---|---|---|---|---|---|---|---|
| 1 | Intake | Rule | Validation | L4 | Partial | JSON envelope | Validated ticket | Error queue |
| 2 | Qualifier | Local LLM, D-q4 | Fine-tuned extraction | L3 | Exists | Subject and body | 7 fields | Re-router, reason code |
| 3 | Field check | Rule | Chaining gate | L4 | To build | Text, 7 fields | Each reference `verified` or `unverified` | Mark `unverified`, route anyway |
| 4 | Routing | Rule | Routing | L3 | Partial | Fields, turn | Desk or triage, priority, reasons; later turns keep the desk | Re-router |
| 5 | Context plan | Rule | Routing table | L4 | To build | Desk, sub-intent, verified references, earlier turns | Tools to call, or none | Empty plan, node 8 decides |
| 6 | Ledger lookup | Tool, SQL | Augmented LLM | L4 | To build | Merchant, transaction id | Record, `missing`, `ambiguous` or `unavailable` | `unavailable` |
| 7 | Knowledge search | Tool, retrieval | Augmented LLM | L2 | To build | Query, desk | Passages with sources, including compliance rules | `unavailable` |
| 8 | Evidence gate | Rule | Chaining gate | L4 | To build | Plan, tool results | `factual`, `clarification` or `no_draft` | `no_draft` |
| 9 | Desk Drafter | LLM | Routing, chaining | L2 | Partial | Ticket, desk prompt, evidence, mode | Draft with citations | Validator, no draft |
| 10 | Policy check | Rule | Chaining gate | L4 | To build | Draft, evidence | Pass, or block with reason | Treated as blocked |
| 11 | Judge (optional) | LLM, other model | Evaluator-optimizer | L3 | To build | Ticket, evidence, draft | Closed rubric, recommendations | Skip; flag "not judged" |
| 12 | Redraft | LLM, stronger model | Evaluator-optimizer, cascade | L2 | To build | Previous draft, reasons, same evidence | New draft version | Keep last draft, objections shown |
| R | Re-router | Person | Checkpoint | Human | Backend only | Ticket, reasons | Correction, direct reply or closure | Stays in queue |
| 13 | Validator | Person | Approval checkpoint | Human | Backend only | Draft, evidence, objections | Approve, edit, send back, write | Stays in queue |
| 14 | Final compliance gate | Rule | Last gate | L4 | To build | Final text, author, merchant | Pass, override, hard block | Treated as blocked |
| 15 | Send | Rule, person trigger | Action | Human trigger | To build | Approved text | Simulated send, once | Retry, never duplicate |
| 16 | Audit log | Rule | Trace | L4 | Partial | All nodes | Versions, actors, reasons | Raise an alert; do not lose the ticket |

Blocked after the budget: the draft is shown with its reason and cannot be approved; the person writes the reply. LLM calls per ticket: 2 with the Judge off, 3 in the nominal case, 7 in the worst case (Qualifier, Drafter, 3 Judge, 2 Redraft), 1 of them local.

## 5. Nodes: metrics and guardrails

No threshold is set yet. Thresholds are chosen on validation data, never while reading the frozen evaluation set. "Measured" holds what we have today; everything else is unmeasured.

| # | Metric | Counter-metric | Guardrail | Measured |
|---|---|---|---|---|
| 1 | Tickets lost: 0; rejected share | Valid tickets refused | Idempotent `ticket_id`; visible error queue | No |
| 2 | Desk accuracy; urgent in a wrong desk | Needless triage; gap by language | Schema validation; extracts only, cannot act | `test_natural` (610): 97.5 %, 1 of 167, 2.0 per 100. Hand-written set: no report |
| 3 | Wrong references caught | False alarms on valid formats such as `TX 385 830` or `2k` | Never blocks routing; no lookup on an `unverified` id | No |
| 4 | Re-router correction rate | Share sent to triage | Pure versioned function; urgency is shown and never changes the path | No |
| 5 | Needed sources planned | Tool calls per ticket | Closed table; no model input | No |
| 6 | Exact, missing and ambiguous cases correct | Records missed although present | Read-only; merchant from the envelope; timeout; cross-merchant results: 0 | No |
| 7 | Retrieval hit rate | Stale passages; passage volume in the prompt | Approved versioned sources; desk filter; score floor | No |
| 8 | `factual` decisions that truly had enough evidence | Share of `clarification` and `no_draft` | Rule only; no factual mode without evidence | No |
| 9 | Drafts sendable as is | Unsupported claims per draft; latency; cost | Citations required; ticket treated as untrusted; no tools or actions | One run: 9.6 s, about $0.00001, with `[Your Name]` left and unwarranted promises |
| 10 | Seeded violations caught | Good drafts blocked | Price, refund promise, legal advice, figures outside evidence; blocked drafts cannot be approved | No |
| 11 | Sendable gain per revision | Good drafts rejected; added latency and cost; agreement with human graders | Closed rubric; a different model; on/off flag; never approves | No |
| 12 | Revised drafts that become sendable | Regressions; cost per ticket | Shared budget; same evidence; same objection stops; node 10 reruns | No |
| R | Correction time | Direct-send rate; repeat corrections | One re-entry; typed enrichment; total age kept | No |
| 13 | Review time; drafts approved unchanged | Seeded errors caught by reviewers | Explicit action; stale or empty drafts cannot be sent; "no warning" is not approval | No |
| 14 | Real issues stopped on final text | Override rate; false blocks | Runs for every author; hard block on other merchants' identifiers; overrides logged | No |
| 15 | Duplicate sends: 0 | Delay after approval | Simulated only; idempotent; no ledger write | No |
| 16 | Tickets with a complete history | Personal data in logs | Versions stored; no secrets; retention set by purpose | No |

## 6. Tool tiers

| Tier | Nodes 6 and 7 | Effect |
|---|---|---|
| 1. POC | Stubs return `unavailable`, shown in every diagram | Node 8 returns `clarification`; no factual reply |
| 2. Demo | Mini synthetic ledger, knowledge base and compliance rules in the project | Factual replies with citations |
| 3. Bonus | Tools deployed with the rest, only if everything else is deployed | Same contracts |

Contracts stay the same across tiers. At tier 2 the ledger must include the transactions of both demo and evaluation tickets, otherwise node 8 fails across the evaluation.

## 7. Override switch

One action, one owner: Head of Support triggers, NAVY executes, Compliance joins sensitive incidents. Levels: Judge off; drafting off (context and human writing stay); copilot off (manual queue). Test it before any demo.

## 8. Model rung per node

Course ladder, one rung per part: nodes 1, 3, 4, 5, 8, 10, 14, 15 and 16 are rung 1 (rules); node 2 is rung 4 (custom fine-tuned model); nodes 9, 11 and 12 are rung 3 (pretrained model). B2 (rung 2) reached 33.9 silent errors per 100 against 0.7 for D-q4 on `test_natural`. The one-line reason why the rung below fails is still to write for nodes 9, 11 and 12.

## 9. Gap decisions

Validated with the target architecture, sized for a course project.

| Gap | Decision | Where |
|---|---|---|
| Merchant replies | `turn` field, same `ticket_id` | Nodes 1, 4 and 5 |
| Stale evidence | The Validator sees the date of each fact; no automatic recheck | Node 13 |
| Prompt injection | No extra node; ticket stays untrusted and traps go in the evaluation set | Evaluation |
| Urgent ticket waiting | No node; an alert on queue age | Flow-level monitoring |
| Semantic cache | Not in the target; #21 and #16 settle whether the course requires it | Issues |
| Two agents on one ticket | Out of scope for one presenter; node 15 prevents a double send | None |
| Data location | Target models run in Keelpay's cloud; the external API is a demo exception | Architecture |

## 10. Open points

- Human-only list for the architecture: legal threat, complaint, `account_hold`, regulatory deadline.
- Models for nodes 11 and 12, and the mix of ledger, knowledge base and rules per desk.
- Rubric of the Judge and rules of node 8 per desk and sub-intent.
- Turn limit before the Re-router.
- Whole-flow, financial and course-level metrics: next layer, including turns per ticket as the counter-metric to closure speed.
