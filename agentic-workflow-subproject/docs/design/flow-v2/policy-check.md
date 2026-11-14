# Flow v2: shared policy check (nodes 10 and 14)

`flow/policy.py` owns one deterministic rule set. Node 10 calls `check_draft` after every model draft. `flow/human_actions.py` implements Validator review actions and calls `check_final_text` on the exact approved text immediately before simulated send, regardless of whether the author was a model or a person. A blocked result records the failed check and prevents the send transition.

## Rules

- Block explicit price/fee quotes and commitments, refund promises, and legal advice in English or French using the finite phrase patterns in the module.
- For model text, block every numeric figure not listed in the evidence result. Transaction IDs and approved source IDs are treated as identifiers, not figures. The evidence adapter must supply normalized allowed figures; tier-1 stubs supply none.
- For all authors, hard-block a foreign `M-####` merchant identifier and any exact identifier in the known foreign-identifier list. This cannot be overridden.
- For human final text, skip figure-to-evidence comparison. Other findings can pass only with a non-empty override reason, which is returned in `PolicyCheckResult` and copied into the human action record.
- A policy-check exception returns a hard block. Model drafts with a block are flagged `Draft.blocked`; `can_approve_model_draft` also requires a passing result whose SHA-256 matches the exact draft text.

`approve_reply` requires a non-empty current response and explicit actor. Model drafts must also have a passing node 10 check whose hash matches the exact draft. Edits and human-written replies invalidate prior approval. `handoff_to_rerouter` invalidates the current response and approval, and `close_manual` records a required reason without sending. `send_simulated` requires approval, a non-empty idempotency key, and a passing node 14 check; repeating the same key returns the recorded receipt and another key is rejected after a send. This state-level idempotency lasts only as long as the `TicketRun` is retained; durable uniqueness and append-only event persistence belong to API/database issue #31. The action records contain actor, timestamp, reason and a content hash rather than duplicating reply text.

This is a small deterministic guardrail, not a semantic legal or factuality verifier. It can miss paraphrases and can flag benign phrasing. Seeded violations and clean drafts must be reviewed in the evaluation set before a demo decision. Node 10 does not approve; node 14 is still required after edits and human-written text.
