# 04 Architecture: Keelpay Support Copilot, decoded

Session 4. Target architecture validated on 6 November 2026. Working detail, with the measures of every node, is in [the node table](agentic-workflow-subproject/docs/design/flow-v2/node_table_v1.md); the build order is in [the task list](agentic-workflow-subproject/specs/013-flow-v2/tasks.md).

## 1. Workflow or agent, and why

**A workflow, not an agent.** The path is drawn in advance and each desk is a fixed branch with its own prompt, tools and rules. No model chooses a tool or a next step. The task decomposes into fixed sub-tasks (read, route, gather facts, draft, check, approve), and the product is judged by a person who must be able to explain and switch off every step. An agent that picks its own tools would be harder to test, to explain and to stop, which is why we keep the fixed path.

## 2. Diagram

![Keelpay Support Copilot flow v2](agentic-workflow-subproject/docs/design/flow-v2/flow_v2.svg)

A merchant ticket comes in as a typed envelope (`ticket_id`, `turn`, `merchant_id`, `created_at`, `channel`, `body`). A merchant reply keeps the `ticket_id` and raises `turn` by 1; later turns keep the desk and load the earlier turns. The two language models are node 2 (the Qualifier, local) and node 9 (the Drafter); nodes 11 and 12 are optional and kept only if measured.

## 3. Components, in order

Trust levels: L1 suggests, L2 drafts and a person approves every reply, L3 acts on a defined scope with sampling, L4 acts alone under a threshold. "Today" compares with the code in `agentic-workflow-subproject/flow/`.

| # | Component | Pattern | Level | Tool or model | Today | Main metric | Main risk |
|---|---|---|---|---|---|---|---|
| 1 | Intake | Validation | L4 | Rule | Partial | Tickets lost: 0 | A valid ticket refused |
| 2 | Qualifier | Fine-tuned extraction | L3 | Local LLM, D-q4 | Exists | Urgent tickets in a wrong desk: 0.6 % (1 of 167) | An urgent ticket sent to the wrong desk |
| 3 | Field check | Chaining gate | L4 | Rule | To build | Wrong references caught | A valid format flagged as wrong |
| 4 | Routing | Routing | L3 | Rule | Partial | Re-router correction rate | The desk kept wrongly on later turns |
| 5 | Context plan | Routing table | L4 | Rule | To build | Needed sources planned | A needed source not planned |
| 6 | Ledger lookup | Augmented LLM | L4 | Read-only SQL tool | To build | Exact, missing and ambiguous cases correct | Another merchant's record returned |
| 7 | Knowledge search | Augmented LLM | L2 | Retrieval tool | To build | Retrieval hit rate | A stale passage used |
| 8 | Evidence gate | Chaining gate | L4 | Rule | To build | `factual` decisions that had enough evidence | A factual reply without enough evidence |
| 9 | Desk Drafter | Routing, chaining | L2 | LLM | Partial | Drafts sendable as is | An unsupported claim or promise |
| 10 | Policy check | Chaining gate | L4 | Rule | To build | Seeded violations caught | A violation missed |
| 11 | Judge (optional) | Evaluator-optimizer | L3 | Other LLM | To build | Sendable gain per revision | Good drafts rejected, extra cost |
| 12 | Redraft | Evaluator-optimizer | L2 | Stronger LLM | To build | Revised drafts that become sendable | A revision worse than the draft |
| R | Re-router | Checkpoint | Human | Person | Backend only | Correction time | Repeated corrections |
| 13 | Validator | Approval checkpoint | Human | Person | Backend only | Review time | Approval without reading |
| 14 | Final compliance gate | Last gate | L4 | Rule | To build | Real issues stopped on the final text | A violation in a human text missed |
| 15 | Send | Action | Human trigger | Rule | To build | Duplicate sends: 0 | A reply sent twice |
| 16 | Audit log | Trace | L4 | Rule | Partial | Tickets with a complete history | Personal data in logs |

Rules (nodes 1, 3, 4, 5, 8, 10, 14, 15, 16) are the lowest rung of the course ladder. The Qualifier is a custom fine-tuned model: on `test_natural`, the rung below (B2) made 33.9 silent errors per 100 tickets against 0.7 for D-q4. Nodes 9, 11 and 12 use a pretrained model; the reason the rung below fails is still to write. Thresholds are set on validation data, never on the frozen evaluation set.

## 4. Tools

| Tier | Nodes 6 and 7 | Effect |
|---|---|---|
| 1 | Stubs returning `unavailable` | The flow runs end to end; the Evidence gate returns `clarification`, no factual reply |
| 2 | Mini synthetic ledger, knowledge base and compliance rules | Factual replies with citations (the demo) |
| 3 | Same tools deployed (bonus) | Same contracts |

All tools are read-only and scoped to the `merchant_id` of the envelope, never read from the text. No tool sends, writes or refunds. In the target, the models run in Keelpay's cloud; the external API used for the demo sees synthetic data only.

## 5. Human checkpoints

| Checkpoint | Kind | Owner | Service level (assumption) | Actions |
|---|---|---|---|---|
| Re-router (R) | Exception handling | Support Agent | Urgent tickets within 1 hour, others within 1 working day | Correct and enrich once, write and send, or close with a reason |
| Validator (13) | Approval of every model draft | Support Agent | Same as above | Approve, edit, send back for one redraft, or write |
| Send (15) | Human trigger | Support Agent | At approval | Simulated send, once |

**Human-only list (proposal):** a legal threat, a complaint, an `account_hold`, a regulatory deadline. These tickets are not drafted. In the target they go to a Human-only queue; this queue is in the architecture and is not built in the first version.

A person can take any ticket back at any time. The service levels are assumptions to confirm with the Head of Support. Nothing is sent without a person, and every text, written by a model or a person, passes the final compliance gate. A person who writes directly skips the Validator step; that direct-send rate is tracked.

## 6. Override switch

One action, three levels, tested before any demo or launch:

1. **Judge off:** the optional revision loop stops.
2. **Drafting off:** context and human writing stay; no model draft is prepared.
3. **Copilot off:** every ticket goes to a manual queue that works without the copilot.

**Owner:** the Head of Support triggers it, the NAVY team executes it, and Compliance joins for sensitive incidents. A switch is a feature flag with an owner; "unplug the bot" is not a switch.

## 7. Limits that bound the system

- **Shared revision budget:** policy blocks and Judge recommendations use one counter, 2 at most; the loop stops earlier if the same objection returns. A draft still blocked after the budget cannot be approved, and the person writes.
- **Turn limit:** above 3 turns on one ticket (proposal), the ticket goes to the Re-router.
- **No evidence, no factual claim:** the Evidence gate chooses between a factual reply, a clarification and no draft.
- **Unclear tickets:** invalid input goes to an error queue; Qualifier failure, `OTHER` or `UNDEFINED` go to the Re-router; spam and thank-you notes are closed there by a person.
- **Cost per ticket:** 2 language-model calls with the Judge off, 3 in the nominal case, 7 in the worst case; one of them is local.

## 8. Built today and target

Built: the Qualifier (D-q4, measured), the routing rule, a first Drafter and part of the audit log. To build, in order: measures, the ticket envelope and turns, context plan and Evidence gate with stubs, policy check and final gate, the per-desk Drafter, the tier-2 tools, human actions and Send, the API and screens, then the optional Judge and the switch. The other items are not built. No endpoint is deployed.
