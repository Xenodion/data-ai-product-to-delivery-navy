# Flow v2: merchant world, schema and generation plan

**Status:** design proposal, simplified 13 November 2026. The goal is a realistic test world, not an adversarial one: the flow should meet merchants, histories and tickets the way a real support desk would, without traps built for it. Nothing here is implemented beyond the phase 1 schema and the phase 2 audit tooling. It refines the tier-2 data parts of the [synthetic context and end-to-end evaluation plan](synthetic-context-and-e2e-evaluation-plan.md) and replaces `build_synthetic_ledger.py`.

## 1. Purpose and decisions

The flow needs merchants with a profile, transactions, payouts, past tickets with conversations, and the company policies, so that drafts are grounded in the merchant's situation and the front end can show credible ticket histories.

1. **The world is the centre, tickets are one table.** Every ticket belongs to a merchant.
2. **Realistic, not adversarial.** The sample follows the natural distribution of the deck. No quota, floor or oversampling of rare cases, no decoy rows, no planted contradictions.
3. **Never edit a deck ticket.** Deck tickets are frozen and their annotation is tied to their exact text.
4. **Only a sample of the deck enters the database.** `current` tickets come from `test_natural` only (the natural distribution; `test_traps` is an adversarial split and stays out), `history` from `train` and `val`, `dev` from `val`.
5. **Conversations are generated for `history` tickets only.** Every `current` and `dev` ticket is the unchanged deck ticket, open and waiting for the agent. The `dev` tickets (from `val`) are the day-to-day demo and development queue and are never empty; the `current` tickets (from `test_natural`) are the locked final evaluation set (section 11). Follow-up evaluation cases are deferred (section 7).
6. **Context is loaded by predefined queries**, not by a planner model and not by semantic retrieval, behind the existing result types and with today's flow semantics (section 11): the cited transaction and the policies reach the Drafter; the merchant profile, recent transactions, payouts and ticket history are shown in the front end. This supersedes the Text Search tool of ADR 0001.
7. **Everything is built by a seeded, deterministic script.** LLMs only write the wording of history conversations. Code defines every fact, amount, date and status.

## 2. What the deck provides (audit, 13 November 2026)

3,205 tickets: train 1,922, val 293, test_natural 610, test_traps 380. Seven sectors, languages fr 53 % and en 45 % with a few es, de, it. `sector` describes the merchant; `language` and `persona` describe the ticket and its author. 1,100 distinct annotated transaction identifiers, none repeated. About two thirds of the tickets carry no identifier, amount or currency. Annotated amounts are heavy-tailed (median about 1,150 EUR, p90 about 57,000 to 126,000 EUR by sector). The full counts are in `data/world/reports/deck_audit.md`. Quarantine files are never opened.

## 3. Sample and roles

| Role | Source | Size | Purpose |
|---|---|---|---|
| `current` | `test_natural`, random | 200 | locked final evaluation set, replayed only in a declared final run; deck text only |
| `history` | `train` and `val`, random | 300 | past tickets shown to the flow and the front end, with conversations |
| `dev` | `val`, random | 100 | day-to-day demo queue, smoke tests and development replays; deck text only |

The draw is a seeded random sample, the same for any run with the same inputs. Exclusions are applied to the candidates before the draw, never after, so the draw is unbiased and never loops. A ticket whose text cites a date later than the reference date is excluded from every role (the audit finds none). A `current` or `dev` candidate that cites a complete date more than `max_cited_age_days` (120) before the window end is excluded from those two roles, because a ticket opened in the last days of the window about an event of February 2025 would look stale: 54 of 610 `test_natural` tickets and 16 of 293 `val` tickets. They stay available as history. Exclusions are listed with their reason in the manifest. `current` and `dev` tickets are `open_awaiting_agent`; `history` tickets are mostly `closed`, with a share `open_awaiting_merchant`. Rules:

- A test ticket is only ever `current`. It is never shown as history.
- History queries return only tickets with `role = 'history'` and `opened_at < as_of`, and only messages with `sent_at < as_of`, where `as_of` is the world date of the ticket being processed. The query layer enforces this, not the prompt. No generated message of a history thread is dated after the start of the `current` window.
- The evaluation oracle (the deck annotation of the 200 `current` tickets) is a separate file the serving code never imports.

## 4. Merchants and attribution

About 60 merchants. Each has a sector, a country, a settlement currency, a plan with fees, a KYC status, a risk level, an onboarding date, a volume tier and one contact per persona and language found among its tickets. Names come from a seeded word list.

Attribution is simple:

1. Group the sampled tickets by sector. Each sector gets a number of merchants proportional to its tickets.
2. Draw a long-tailed ticket count per merchant (Pareto weights, shape in `world.toml`; each merchant first receives one ticket) (many with a few tickets, a few with many) and deal the tickets of the sector to its merchants at random.
3. The settlement currency is the most frequent currency among the merchant's tickets, otherwise EUR; a merchant may hold several currencies. The volume tier is the tercile of the merchant's largest annotated amount converted to EUR, computed over the merchants that have an amount, so a merchant never looks smaller than its own tickets. Only about a third of the tickets carry an amount, so many small merchants have none: they draw their tier from configured weights with their own seeded stream. The onboarding date is before the earliest complete date cited by any of the merchant's tickets.
4. Dates: `history` tickets run from the start of the simulated window to `history_gap_days` (21) before its end. `current` and `dev` tickets fall in the last `open_days` (10) before the end, so the queue holds tickets opened a few days ago, not weeks ago; `dev` needs no window of its own because history queries return history rows only. A ticket is never dated before the latest date cited in its text.

Merchants with no history are expected: they test the new-customer path. Coherence between tickets of one merchant is guaranteed on structured fields only; two tickets may still tell incompatible stories in prose, which a human review of about ten merchant timelines checks at each version.

## 5. Schema

The phase 1 schema (`flow/world/schema.sql`) stands, with one change: `ticket_outcomes.desk` also accepts `triage`, because tickets whose intent is OTHER or UNDEFINED (spam, thanks only, off topic, too vague; about a fifth of the history sample) have no desk. A single mapping function (`flow/world/desks.py`) turns the Qualifier desk names into the stored ones (`technical` becomes `technical_api`). Triage tickets close with the resolution `closed_no_action`, zero follow-up exchanges and one short agent reply. SQLite, read-only for the flow, amounts in minor units, plain portable SQL: `merchants`, `merchant_currencies`, `contacts`, `transactions`, `refunds`, `disputes`, `payouts`, `tickets` (with `role` and `thread_state`), `ticket_outcomes`, `messages` (turn 1 is the unchanged deck text), `policies`, `policy_sub_intents`. Not stored in the served database: the deck split, labels, trap and case columns, and the distinction between rows anchored by a ticket and filler rows. These live in the generator manifest and the oracle file.

## 6. Transactions, payouts and the ledger

- **Cited transactions.** For each sampled ticket, every well-formed `TX-dddddd` found in its text or annotation gets one row under its merchant, with the annotated amount and currency (the merchant's settlement currency and an amount in its usual range when the ticket gives none). The status follows the ticket's sub-intent (for example a delayed credit is `processing`, a refund status is `refunded`). Tickets with no well-formed identifier add nothing: a malformed or foreign reference simply finds no row, as it would in real life.
- **Two small rules for realism.** A `duplicate_charge` ticket gets a second identical transaction a few minutes later. An `amount_mismatch` ticket gets a ledger amount that differs from the stated one by a plausible small amount, a configured percentage.
- **Filler.** About 60 transactions per merchant from its tier (status mix, refund and dispute rates in configuration), enough for "recent transactions" and weekly payouts. Refunds, disputes and payouts are derived from transactions by rules.

## 7. History conversations

Each `history` ticket is the opening message of its thread; the rest is written by a model, one call per thread.

- **Plan by code.** The outcome (`closed` 75 %, `open_awaiting_merchant` 25 %), the number of follow-up exchanges (0, 1 or 2 with weights 55, 30 and 15 %; most threads are the ticket and one agent reply), the timing between messages (hours for a reply, days for a chase, with the last message dated before the start of the `current` window) and the fact sheet (the merchant's rows relevant to the ticket) are decided by code. A closed thread's outcome is also written to `ticket_outcomes` before any text exists.
- **One call per thread.** The prompt gives the opening text, the desk and sub-intent, the fact sheet, the outcome, the number of messages and the timing, and asks for messages 2 to n as JSON. Code inserts turn 1, so the deck text can never be rewritten. Rules in the prompt: the agent is professional and does not promise more than a support agent can; the merchant keeps the mood of the opening; no identifier, amount or absolute date outside the allowed set; the thread ends on an agent message.
- **Checks.** Automatic: message count and order, language, and no identifier, amount or date outside the allowed set, which is the fact sheet, the tokens of the opening message (openings, especially forwarded ones, contain numbers and dates an agent may legitimately echo) and the dates of the plan. An `open_awaiting_merchant` thread ends with a question or a request, a closed thread without one. A thread that fails is retried once, then replaced by a minimal one (the ticket and one agent reply built from the policy text). A human reads about 20 threads. No model judge.
- **Not generated in V1.** Follow-up evaluation cases, cross-ticket scenarios and showcase merchants. Executing a follow-up needs a previous run with status exactly `sent_open` in the API store, persisted extracted fields and a rule for consecutive merchant messages; the chosen direction for V2 is to run earlier turns headlessly and store them as `sent_open` with the world's agent reply as the human-authored text.
- **Reproducibility.** Accepted threads are appended to a log (model, prompt hash, cost). The database build ingests the log, so rebuilding from the same log, configuration and seed gives identical content.

## 8. Policies

The 22 documents of `flow/fixtures/knowledge.json` (21 approved, 1 draft) are all in English; they are loaded into `policies` and `policy_sub_intents` as `en`, and the Drafter replies in the language of the ticket. Selection is by key: desk, sub-intent and the world date. The Drafter receives only approved, valid documents and cites their `source_id` and version.

## 9. Generation script

`python -m flow.world.build`, parameters in `data/world/world.toml` validated by Pydantic. No wall clock, no builtin `hash()`, one seeded stream per stage. Stages: load the deck, sample, build merchants, assign and date tickets, build transactions, derive refunds, disputes and payouts, plan history threads, load policies, export the oracle and the manifest (sample list, input hashes, row counts), validate, write the database atomically. Thread generation is a second entry point that reads the planned database and writes the accepted-thread log.

Invariants checked by `validate` and by tests: every sampled ticket belongs to one merchant of its sector; no test ticket has the role `history` or `dev`; `current` tickets come from `test_natural` only; history is dated before the `current` window, and every history message is dated before it; no ticket is dated before a date cited in its text; every cited identifier exists once under the right merchant; **merchant isolation**: every predefined query, run for every merchant, returns only that merchant's rows, and history queries never return a `current` or `dev` ticket; closed and awaiting threads end on an agent message with strictly increasing timestamps and turn 1 equals the deck text byte for byte; every closed ticket has an outcome whose desk is stored; two runs with the same inputs give the same content hash.

## 10. What the world feeds

The flow reads the database read-only through the predefined queries (each bounded, named, with source identifiers and an `as_of` argument). The injector draws from the world's `dev` and `current` lists and sends the real `merchant_id`, the bare `card_id`, the world date as `created_at`, the channel, the language and the world's ticket text. The front end shows a merchant's tickets and messages with outcomes, and hides `current` tickets unless the final-run flag is set. The 200 V1 evaluation cases are first-contact cases from `current`, scored against the deck annotation. The flow is integrated read-only on the world before any paid generation, so a schema or query change cannot invalidate paid text. The first section 3.2 and 3.3 of the context plan, which prescribe adversarial scenario constructors, are superseded by this document; the V1 oracle scores the label and route fields only.

## 11. Compatibility with what exists

The world must not change anything the team has already built or validated.

1. **The fine-tuned Qualifier is untouched.** It never receives context, history or merchant data. Its input is `Ticket.message_text`, which is the deck text itself (the deck text already carries its own `Subject:` line, so the envelope `subject` stays `None`), wrapped by the training instruction of `ml/qualifier/src/prompt.py`. The world never rewrites a ticket: turn 1 is the deck text, in one fixed line-ending form.
   - **Line endings.** The committed deck files and the log the tickets were generated into use LF (the generation log holds 5,314 texts and none contains a carriage return; the committed blob of `val.csv` has none). A Windows checkout with `core.autocrlf=true` rewrites the CSV files with CRLF (2,575 carriage returns in the working copy of `val.csv`), so the injector of today sends CRLF text on this machine and LF text on Linux or Vertex. Which form the Qualifier saw in training cannot be read from the repository: `ml/qualifier/scripts/upload_dataset.py` uploads the working-copy files to the bucket. The world therefore stores the committed form (`text_newline = "lf"` in `world.toml`) and the Phase 5 injector sends the world's text, so the Qualifier receives one fixed form on every machine. If the bucket files turn out to use CRLF, changing that one setting to `crlf` restores it; nothing else moves. Input hashes are computed on LF-normalised content so that a manifest does not depend on the checkout.
   - Checked on 13 November 2026: after normalising line endings, the text built from the world loader equals the text the injector sends, for all 3,205 deck rows (`tests/flow/world/test_world_compat.py` guards it on a micro deck with accents and both checkouts).
2. **Locked splits stay locked.** The `current` tickets come from `test_natural`. They sit in the database, because their merchants and histories must exist, but they are replayed through the flow only in a declared final run with `--allow-locked-split`, as `flow/inject_dataset.py` already enforces, and the front end hides them unless that final-run flag is set. Day-to-day work (demos, the phase 5 smoke test, prompt, policy and query iterations) uses the `dev` tickets, which come from `val`; results on `dev` are never reported. `test_natural` was already used to choose the Qualifier champion (`docs/scoring_protocol.md`), so it is fresh only for the end-to-end evaluation of the flow. The injector draws its tickets from the world's `dev` and `current` lists, not from its own random draw of the CSV files.
3. **Contracts and context semantics do not change in V1.** `Ticket`, `TicketRun`, `ContextPlan`, `EvidenceFact`, `LedgerToolResult`, `RetrievalToolResult` and `EvidenceResult` keep their fields, and so does the behaviour of the context plan (the ledger is queried only for payment and dispute sub-intents with a verified identifier), of the Evidence gate and of the Drafter modes. The world replaces only what sits behind those types: the cited-transaction lookup and the policy lookup by key. The merchant profile, recent activity and ticket history are shown in the front end and are not sent to the Drafter. Giving them to the Drafter would be an additive contract change (one optional field such as `EvidenceResult.merchant_context`, filled in every mode) together with a new Drafter prompt release, to be evaluated against the V1 baseline; it is deliberately left out of V1. The world is switched on by an optional `world_database_path` in `FlowConfig`, off by default, so the 129 existing flow tests stay green and the fixture path remains the default for them.
4. **Mapping of world rows to tool results.** For the cited transaction: `source_id` is `world:transactions:<TX>`, `source_version` is the world version string, the record date is the settlement time or, failing that, the creation time. The facts are the existing fields `transaction_status`, `record_updated_at`, `transaction_amount` and `transaction_currency`, with `amount` formatted from minor units to a two-decimal string by the single conversion function and added to `allowed_figures`, so that a Drafter quoting the ledger amount is not flagged as an unsupported figure. Only the cited transaction uses the field `transaction_status`: the policy hard block compares the distinct `transaction_status` facts, and any other fact (profile, recent transactions, history) must use another field name. A test shows that the conflict check still fires with world facts present.
5. **`ticket_id` is the bare `card_id`.** The deck's `card_id` is the same kind of string in every split (all start with `train-2026...`), so it does not reveal the split. The current injector builds `ticket_id` as the split plus the `card_id` (for example `train-train-20261031-08816`), which exposes the split in the API and the front end. Nothing in the flow, the graph, the metrics or the front end parses a ticket identifier, and `M-DEMO` appears only as data in one test.
6. **Formats.** Transaction identifiers are `TX-dddddd`; the label carries amounts as decimal strings with two decimals and the database carries integer minor units; currencies are those of the Qualifier contract; `channel` takes the four envelope values; `created_at` is timezone-aware UTC; `merchant_id` is any non-empty string.

## 12. Downstream updates

New ADR superseding ADR 0001; `node_table_v1.md`, `tools.md`, `flow_v2.svg`, the cases of the context plan, step 6 of `specs/013-flow-v2/tasks.md`; remove `build_synthetic_ledger.py` and `ledger.json`; update `README.md` and `04_architecture.md`.

## 13. Limits

The world is synthetic and realistic in distribution, not measured against real Keelpay data. It exercises merchant context, history and isolation on first-contact cases; it does not measure follow-up handling. Generated conversations imitate real support exchanges and are judged by sample review. About 120 `forwarded_thread` tickets of the `current` pool quote earlier support replies that have no matching history row; this is accepted, as a merchant may forward an exchange held on another channel.
