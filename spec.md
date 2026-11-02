# spec.md — Keelpay agent-assist copilot · skeleton v0

> Session 3 skeleton, completed in Session 4. Written from `03_product_brief.md`, the frozen brief (README) and the drafter plan (`docs/plans/copilot-drafter.md`, decisions D1–D4, validated on 1 November 2026). This is what the coding agent reads: every line is a decision; `⟨TO DECIDE⟩` marks the decisions not taken yet.

## 1. Problem (one paragraph)
Keelpay's support agents (~36,000 merchant tickets a month, French and English) spend ~15 % of handling time reading a free-text ticket and routing it, and ~45 % finding the payment and writing the reply; ~1 ticket in 7 first lands in the wrong desk, and an urgent one can miss its deadline. The copilot reads each ticket into a strict JSON, routes it with fixed rules, looks up the merchant's transactions, and drafts a cited reply that the support agent approves, edits or reroutes — nothing reaches the merchant without a person.

## 2. Workflow — seven steps, in this order
1. **Read** — rung 3. A `Router` interface returns the JSON of §3. Implementations: `BaselineRouter` (TF-IDF + logistic regression, B2), `LocalGgufRouter` (fine-tuned small model, if the compact variants exist), `VertexRouter` (only if an endpoint is deployed). The fine-tuned model is used only if it passes the gate of `finetuned_llm_classifier/docs/scoring_protocol.md`; otherwise the best baseline. Trust: L1.
2. **Decide** — rung 1, `prototype/decision.py`. In this order:
   - invalid JSON, `intent` = `OTHER` or `UNDEFINED` → **triage** (no draft);
   - `intent` = `dispute` or `compliance` **and** `urgency` = `high` → **critical**: held until a person confirms the desk, then continues;
   - a policy keyword in the ticket (refund promise, fee waiver, legal) → **escalate** with the reason;
   - otherwise → **auto**: routed to the desk of the intent. Trust: L3 with a weekly sampled audit.
   - **No separate confidence threshold:** the router returns no score (seven string fields only, `label_definitions.md`). Its doubt is expressed as `UNDEFINED` / `OTHER`, which go to triage; "low confidence" in the frozen brief means exactly that. Measured on val: the router sends 16.0 % of tickets to triage against 16.7 % in the labels, all of them rightly (`03_product_brief.md`, step 1).
   - **Language rule:** a ticket in a language other than French or English → **triage**. The scenario's languages are French and English, and the training data has almost no other language (`governance.md`, Session 3).
3. **Look up** — rung 1, `prototype/ledger.csv`. By merchant and `transaction_id` only; `transaction_id` = `UNDEFINED` or `""` → no lookup, candidates by merchant and amount are shown to the agent, no draft until the agent picks one. Trust: L1, read-only, this merchant only.
4. **Retrieve** — rung 1, `prototype/retrieve.py`. Split `prototype/kb/*.md` by `## ` heading; TF-IDF cosine; top 3 chunks of the ticket's desk with a score **above 0**, i.e. sharing at least one term with the ticket. No tuned threshold: retrieval is already limited to the desk's article, and the citation and policy checks catch a weak source.
5. **Draft** — rung 3, `prototype/draft.py`, `generate_reply_draft(ticket, router_json, chunks, transaction)`. Uses only the router fields, the lookup and the retrieved chunks; cites each chunk as `[KB-xxx · Section]`; anything not in them is written `[VERIFICATION NEEDED]`. Default: a deterministic template drafter (no credentials). The real call is a hosted model API, synthetic tickets only (D1, dated exception in `governance.md`, Session 3), capped at 3 USD with a per-call cost log (D2). Trust: L2.
6. **Policy check** — rung 1, `prototype/policy.py`. Blocks a draft that promises a refund, waives a fee, states a legal commitment, or quotes an amount not in the lookup. A blocked draft is shown with its reason and cannot be approved.
7. **Review and log** — the agent approves, edits or reroutes (one click; redrafted once; a second reroute → triage). Every reading, decision, edit and reroute is logged. **No send in the prototype.** Trust: person only for sending; L4 for the log.

## 3. Contracts
- **Input:** `{id, merchant_id, text}` — `text` = `Subject: …` + blank line + body, French or English, possibly a forwarded thread.
- **Router output** (`finetuned_llm_classifier/docs/label_definitions.md`): exactly seven keys, every value a string — `intent`, `sub_intent`, `transaction_id` (`TX-######`), `amount` (`12500.00`), `currency` (ISO, closed list), `urgency`, `sentiment`; `UNDEFINED` = cannot be determined, `OTHER` = understood but no desk, `""` = absent (`transaction_id`, `amount`, `currency` only).
- **Decision:** `{route: auto | critical | triage | escalate, desk, reason}`.
- **Chunk:** `{article_id, section, text, score}`.
- **Engine output** (`prototype/copilot_engine.py`): `{desk, fields, decision, draft_text | NO_DRAFT, citations: [{article_id, section}], policy: pass | block, reason}`.

## 4. Edge cases (each one is a row of `evals/eval_set_v0.csv`)
- Two requests of equal weight (EV-14) → `UNDEFINED` → triage; no draft.
- Too short to understand (EV-18) → `UNDEFINED` → triage.
- Language outside French and English (EV-05) → triage by the language rule of step 2; results reported apart.
- An instruction hidden in the ticket (EV-04, prompt injection) → treated as text; never changes the decision, the urgency or the draft's rules.
- Malformed or lookalike reference (EV-02 invoice number, EV-07 letter O) → no lookup on it; candidates shown; no amount stated that the lookup does not confirm.
- Deadline within 48 hours on a dispute (EV-08) → critical.
- Amount in another currency or several currencies (EV-19) → the draft quotes only amounts present in the lookup.
- Thank-you or pricing question (EV-15) → `OTHER` → triage.

## 5. Fallbacks
- Router error or invalid JSON → triage, with the ticket shown as is.
- No chunk with a score above 0 → `NO_DRAFT`, decision `escalate`.
- Lookup finds nothing → `NO_DRAFT`; the agent sees "no matching transaction".
- Model or API error, or budget reached → template drafter.
- Company-wide switch → "reading only" (no draft) or off, owned by the Head of Support.

## 6. Surface
Chainlit app (`finetuned_llm_classifier/src/app/main.py`, plan D3): the agent pastes a ticket and sees the JSON, the decision and its reason, the lookup, the sources and the draft; edits are asked in the chat; no send. The static mock `prototype/copilot_panel/index.html` is the reference for what the panel shows (case card, path taken, one-click reroute). Every draft is captioned: "Trust level L2 — nothing is sent until you approve."

## 7. Evaluation (never tune while looking at it)
- **Router:** `finetuned_llm_classifier/src/scoring.py` on the sealed test sets (610 + 380) — desk accuracy, share routed automatically (1 − abstention), urgent tickets in the wrong desk, valid JSON (≥ 98.5 %, also reported at 99 %).
- **Copilot:** `evals/eval_set_v0.csv`, 20 tickets labelled by hand. Metrics to print: desk correct (vs `label_intent`), route correct (vs `hand_over_to_a_person`), **drafts on tickets that must go to a person (must be 0)**, policy blocks, policy breaches on EV-04 (must be 0).
- **Drafter** (plan, phase 3): retrieval hit@3, citation precision, "sendable as is" (cites the expected article and passes the policy), then ROUGE / BERTScore and a judge for faithfulness. Needs `expected_kb`, `expected_section` and a reference reply per row: to add when the set grows to 50 (Assignment 4).

## 8. Definition of done
- On the gold set: **≥ 90 %** of tickets to the right desk on the first pass, **≥ 50 %** routed automatically, **0** urgent ticket auto-routed to the wrong desk (`03_product_brief.md` §7).
- On `evals/eval_set_v0.csv`: **0** drafts on hand-over tickets, **0** policy breaches.
- Drafter: "sendable as is" ≥ `⟨TO DECIDE⟩` — set by the drafter plan's owner before the first drafter run (plan, phase 3); not derivable from the sizing, and the course example's figure is not reused (README rule).
Below a bar: do not fix the prompt; list the misses by cause and propose the change to this spec.

## 9. Out of scope (v0)
Sending to a merchant · autonomous replies (L4) · ledger write access (payout, refund, unfreeze) · real merchant data · a production external model API · dispute arbitration, legal or regulatory advice · voice, chat or a merchant-facing bot · splitting a ticket into several.

## 10. Files
```
finetuned_llm_classifier/          router: dataset, scoring, training (own uv project)
  docs/label_definitions.md        JSON contract
  src/scoring.py                   router metrics
  src/app/main.py                  Chainlit surface
prototype/
  copilot_panel/index.html         static mock of the panel (03_prototype_link.md)
  kb/*.md                          four articles, one per desk
  ledger.csv                       ~30 synthetic transactions
  retrieve.py citations.py draft.py policy.py decision.py copilot_engine.py
evals/eval_set_v0.csv              20 tickets labelled by hand (frozen)
```
