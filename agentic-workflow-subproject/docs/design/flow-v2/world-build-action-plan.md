# Flow v2: merchant world, action plan

**Status:** simplified 13 November 2026 after Vincent's request for a realistic, not adversarial, test set. Phases 0 and 1 are done and approved; phase 2 is built but its sampler is being replaced (section 4). It turns the [world schema and generation plan](world-schema-and-generation-plan.md) (the design, which wins in case of disagreement) into ordered work with gates.

## 0. Scope and rules

**V1:** the merchant database, its deterministic builder, history conversations, the first-contact oracle, and the read-only flow integration. **V2 (deferred):** follow-up evaluation cases, cross-ticket scenarios, showcase merchants. **Out of scope:** GCP, PostgreSQL, embeddings, the Qualifier, the Judge/Redraft loop.

Rules: work on branch `feat/world-db`; nothing merged to `main`, pushed or tagged; commits stage explicit paths, ASCII messages, no Claude trailer, only after Vincent validates; code and docs in English, typed, Pydantic, `pathlib`, logging not `print`, no wall clock or unseeded randomness in the builder, parameters in TOML; tests mirror the source layout and never touch the network or the real deck outside the audit; paid calls only in phase 6, through the existing budget client with its own cap and call log; each phase ends with a written result shown to Vincent.

## 1. Facts this plan relies on

- The deck, its columns and counts, and the measured audit results are in `data/world/reports/deck_audit.md`.
- The API accepts a later turn only after a previous run with status exactly `sent_open` (`flow/api.py`), which is why follow-up cases are deferred.
- The injector prefixes the split to `ticket_id` and dates tickets from the wall clock (`flow/inject_dataset.py`); policy validity uses `ticket.created_at` (`flow/tools.py`). Both change in phase 5.
- The flow calls OpenRouter at runtime (Drafter); the same key serves generation. 3.40 USD is already logged against an internal cap of 8 USD and a key limit of 10 EUR. The budget guard sums every `*.jsonl` of the folder it is given, so the generation call log lives alone in its folder.
- The subproject `.gitignore` now re-includes `data/world/`; the built database lives under `.local/world/` (ignored).
- About 60 files are modified or untracked on `main` (flow v2 code, front end, docs), including `flow/tools.py`, `flow/context.py`, `flow/api.py`.

## 2. Phase map

| Phase | Purpose | Paid | Touches uncommitted flow files | Gate |
|---|---|---|---|---|
| 0, 1 | Preparation, contracts, config, schema | no | no | done, approved |
| 2 | Deck audit, loader, simple sampler | no | no | G2 |
| 3 | Merchants, attribution, dates | no | no | G3 |
| 4 | Ledger, refunds, disputes, payouts | no | no | G4 |
| 5 | Policies, oracle, validate, build: world v0; then read-only flow integration | no | yes (needs D1) | G5 |
| 6 | History conversations: pilot then full run | yes | no | G6 |
| 7 | Ingest, freeze world v1, documentation | no | docs | G7 |

Phases 2 to 4 and the build part of 5 only create new files. The flow integration in phase 5 modifies files that are currently uncommitted, so it starts only after Vincent has committed or secured that work (D1). Generation comes after the integration so that a schema or query change cannot invalidate paid text.

## 3. Decisions

| ID | Decision | Default |
|---|---|---|
| D1 | Who secures the uncommitted flow v2 work, needed before the flow integration | Vincent commits it in coherent chunks on its own branch |
| D2 | Sizes | about 60 merchants; 200 current / 300 history / 100 dev |
| D3 | Window and dates | 1 Jan to 10 Nov 2026, reference date 12 Nov 2026; history up to 21 days before the end; `current` and `dev` in the last 10 days; a `current` or `dev` ticket may not cite a complete date older than 120 days before the end |
| D4 | Volume tiers | terciles of each merchant's largest annotated amount in EUR (placeholder exchange constants in config), over merchants that have an amount; the others draw from configured weights |
| D5 | Policies | the existing `knowledge.json` documents |
| D6 | History threads | 0, 1 or 2 follow-up exchanges (55, 30, 15 %), 75 % closed and 25 % awaiting the merchant; triage tickets get one short reply |
| D7 | Where artifacts live | config, manifest, oracle and accepted-thread log under `data/world/` (tracked); database under `.local/world/` |
| D8 | Generation budget | own cap of 1.5 USD (pilot 0.3) and own call log; Vincent checks the key balance first |

## 4. Phase 2: deck audit, loader, simple sampler

Kept and already tested: `deck.py` (typed loader, refuses quarantine files, strict categories), `text_signals.py` (reference and date extraction), `audit.py` and its report, `provenance.py` (input hashes), `config.py`, `errors.py`, `rng.py`, the schema and models.

Changed:

1. `sampling.py` is a seeded random draw (done): `current` from `test_natural`, `dev` from `val`, `history` from `train` and `val` minus `dev`. Exclusions apply to the candidates before the draw: tickets dated after the reference date leave every role; `current` and `dev` candidates citing a complete date older than `max_cited_age_days` before the window end leave those two roles. The floors, two-pass selection, anomaly categories, shortfall and coverage tables and the continuation flag are gone.
2. `config.py` and `world.toml` (done): tiers, sampling floors, drop-rate threshold and regeneration count removed; added `[dates]` (`history_gap_days`, `open_days`, `max_cited_age_days`), `[merchants]` (tier weights without amount), `[ledger]` (`amount_mismatch_pct`, `duplicate_gap_minutes`); exchange weights now cover 0 to 2; budget cap 1.5 USD and pilot cap 0.3 USD.
3. `audit.py` keeps counts, the id and amount state tables, the extractor validation, dates, the stale-date count, amount quantiles and quarantine sizes; the continuation, look-alike and joint-cell sections are removed. `text_signals.py` keeps reference and date extraction only. `flow/world/desks.py` maps Qualifier desks to stored desks, and `ticket_outcomes.desk` accepts `triage`.

Gate G2: the audit extractor recovers 100 % of annotated identifiers; `current` comes from `test_natural` only, no test ticket is `history` or `dev`, `dev` comes from `val` and is disjoint from `history`; no `current` or `dev` ticket cites a date older than the cutoff; two runs give the same content hash and the manifest records the input hashes; Vincent has read the audit sections 2 to 4 and 6.

## 5. Phase 3: merchants, attribution, dates

`merchants.py` (merchants, currencies, contacts, names, tier by tercile or by configured weights when no ticket has an amount, onboarding before the earliest cited date), `assign.py` (per-sector long-tail dealing of tickets, section 4 of the design), `timeline.py` (dates per role from `[dates]`, never before a date cited in the text). Tests: every sampled ticket is assigned once under a merchant of its sector; history is dated before the `current` window and `current` and `dev` in the last `open_days`; the text-date rule holds; contacts carry the personas and languages of their tickets; determinism. Human check: ten merchant timelines printed as a structured view (dates, desk, sub-intent, role, amount, currency; no free text). Gate G3: report and timelines accepted.

## 6. Phase 4: ledger and money objects

`ledger.py` (cited transactions with annotated amount and currency, status by sub-intent, the duplicate-charge and amount-mismatch rules, filler rows) and `money.py` (refunds, disputes, payouts by rules). Tests: every well-formed identifier of a sampled ticket exists once under the right merchant; tickets with no well-formed identifier add no row; transaction identifiers are unique; refund, dispute and payout invariants. Gate G4: Vincent reads 20 ledger rows beside their ticket annotation.

## 7. Phase 5: policies, oracle, build, flow integration

1. `policies.py` loads the `knowledge.json` documents into `policies` and `policy_sub_intents`; `oracle.py` exports the deck annotation of the 200 `current` tickets to `data/world/oracle/` (a test checks that no serving module imports it); `validate.py` holds the invariants of design section 9; `build.py` runs the stages and writes `.local/world/world.sqlite` atomically with a manifest. Gate for the first half: the full build runs on the real deck with zero violations and two runs give the same canonical hash. This is world v0, with no generated messages.
2. Flow integration, after D1, one small reported step at a time, additive and compatible (design section 11): an optional `world_database_path` in `FlowConfig`, off by default so the 129 existing flow tests stay green; a read-only world access module next to the fixture path of `flow/tools.py`; the cited-transaction lookup and the policy lookup by key behind the existing `LedgerToolResult`, `RetrievalToolResult` and `EvidenceFact` types with no new field, using the mapping of design section 11.4; the merchant profile and history served to the front end only, with `current` tickets hidden unless the final-run flag is set; Text Search removed from the evaluation cases and docs (new ADR) without changing the result contract; the injector drawing from the world's `dev` and `current` lists and sending the real `merchant_id`, the bare `card_id`, the world date and the world's ticket text; a smoke test of 20 first-contact tickets taken from `dev` (never from the locked `current` tickets), end to end, with their context payloads recorded and a test that the policy source-conflict check still fires with world facts present.

Gate G5: world v0 validated; the existing flow tests still pass unchanged; the Qualifier input of every world ticket equals the deck text after line-ending normalisation (test), and Vincent has checked which line ending the Qualifier was trained on (design section 11.1); the 20 smoke cases run with bounded, merchant-scoped contexts that contain no other evaluation ticket; Vincent reads the contexts of five of them.

## 8. Phase 6: history conversations

`flow/world/threads/` with a prompt file, a renderer reusing the OpenRouter client and budget guard of `ml/qualifier/src/dataset_build/openrouter.py` through its own run config (cap of D8, call log alone in `data/world/runs/calls/`), simple automatic checks, and an append-only accepted-thread log. The model returns messages 2 to n and code inserts turn 1. The checks accept identifiers, amounts and dates found in the fact sheet, in the opening message or in the plan, and require that an awaiting thread ends with a question or request and a closed thread without. Stub dry run first with zero spend. Pilot of 20 threads (about 0.1 USD): Vincent reads all of them against a short checklist (professional agent, merchant keeps the opening mood, facts match, language and channel match, ending as planned) and the real cost per thread replaces the estimate. At most three prompt revisions. Then the full run over the roughly 300 `history` tickets in batches, with a backup copy of the call log and the thread log after each batch, stops on repeated API errors or on the cap, and a human read of about 20 threads. Gate G6: pilot approved, full run complete, spend under the cap, logs backed up.

## 9. Phase 7: ingest, freeze, documentation

Ingest the accepted threads, run `validate` again (including thread endings, timestamps and turn 1 equal to the deck text), build world v1, write the manifest with the log hash, freeze the oracle. Nothing is tagged or pushed. Documentation: the downstream list of design section 11. Gate G7: two rebuilds from the same log give the same canonical hash; Vincent signs off.

## 10. Budget

Pilot about 0.1 USD, full run of about 300 threads at most a few tenths of a dollar at the prices of `run.toml`, under a cap of 1.5 USD. These are estimates from model prices and about 2,500 input and 500 output tokens per thread; the pilot replaces them with measured values. The key is shared with the flow runtime.

## 11. Risks

| Risk | Mitigation |
|---|---|
| Follow-up cases cannot run from world data | deferred to V2 with the direction recorded |
| A model makes threads unrealistic (agent too eager, merchant too soft) | prompt rules, checks, pilot read by Vincent, three revisions at most |
| Two deck tickets of one merchant contradict each other in prose | ten timelines reviewed per version |
| Spend exceeds the key balance or the cap | own cap and call log, balance check, pilot first |
| The accepted-thread log is lost | append-only, backed up after every batch, hash in manifest |
| Labels or oracle leak into the served database or prompts | stored only in manifest and oracle; import test; prompts receive only the opening text, desk, sub-intent and fact sheet |
| Nondeterminism | per-stage SHA-256 streams, sorted iteration, explicit `ORDER BY`, UTC, canonical dump hash |
| The world breaks something already built or validated (Qualifier input, locked test splits, contracts, Drafter prompt, existing tests) | compatibility rules of design section 11; byte-for-byte test on the Qualifier input; `current` replayed only in a declared final run; no change to the contracts or the production prompts; existing tests run at every gate |
| Work on `flow/` collides with the uncommitted WIP | phases 2 to 4 and the build add new files only; integration waits for D1; explicit path staging |

## 12. Definition of done for V1

World v1 built from a frozen log; manifest and oracle committed; validation reports zero violations; two rebuilds identical; the 20-ticket smoke test passed; the pilot and full-run reports written; spend within the cap; every `current` ticket open and waiting for the agent; V2 items written down with their prerequisites.

## 11. Status (2026-11-14)

Phases 0 to 6 are built. Full history run: 300 threads (251 written by the model, 49 fallback), 0.1037 USD over 423 calls, under the 1.5 USD cap. World v1 builds with `python -m flow.world.build --threads data/world/threads/accepted.jsonl`: 600 tickets, 1,238 messages, 217 outcomes, zero violations, content hash `71ed1c65...062e`, identical on two builds; the manifest records the SHA-256 of the thread log (`threads_log_sha256`). Remaining for G7: Vincent reads about 20 threads and the fallback ones, then signs off. Nothing is committed, tagged or pushed.
