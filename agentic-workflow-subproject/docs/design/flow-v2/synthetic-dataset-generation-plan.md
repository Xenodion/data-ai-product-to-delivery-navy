# Flow v2: synthetic dataset generation plan

**Status:** plan accepted for implementation; 10 November 2026. The bounded HTTP replay client is implemented in `flow/inject_dataset.py`; no OpenRouter generation or locked test replay is implied by the client.

Companion plan: [synthetic context and end-to-end evaluation](synthetic-context-and-e2e-evaluation-plan.md). Existing pipeline: `ml/qualifier/src/dataset_build/`; flow fixtures: `flow/fixtures/`.

## 1. Purpose and boundaries

Build a reproducible, versioned set of synthetic support conversations and matching synthetic source data for full-flow evaluation. The model-written ticket is a surface rendering of a predefined scenario. It must not define the scenario's ground truth. The scenario card and evidence manifest define facts; an LLM may express them in natural language, but may not invent them.

The generated set serves the flow demo and regression gate. It does not replace or relabel the existing Qualifier train/validation/test sets, and its results must not be reported as a new Qualifier benchmark. All provider calls use synthetic content only. No real merchant or customer data may be sent to OpenRouter.

## 2. Reuse the proven parts of the current generator

The current pipeline already provides useful controls: scenario cards with a closed label schema; separate prompt rendering; a JSON-only OpenRouter client; per-role model configuration; a hard spending budget reconstructed from append-only logs; transient-only retries; prompt hashes; deterministic card IDs; ticket checks; blind independent voters; a judge for disagreements; split-specific writers; accepted/rejected records and provenance. Extend those controls rather than create a second ungoverned generation script.

Current configured ticket-writing roles include `deepseek/deepseek-v4.1-flash` for train/validation and `xiaomi/mimo-v2.6-flash` for natural/trap tests; other configured roles include Moonshot/Kimi, Qwen and Ling. Provider/model availability and prices are volatile, so treat these as the current project configuration, not permanent recommendations. Select models through `run.toml`, pin the exact returned model ID/version in each record, and check actual usage cost from the response.

## 3. Data objects and generation order

### 3.1 Scenario card

Extend or wrap the existing `Card` into a versioned `FlowScenario`. Preserve the seven-field `TicketLabel` target and its current taxonomy. Add explicit scenario variables required to define the synthetic world: stable `case_id`, merchant scope, canonical transaction reference, true ledger amount/currency and status, optional deliberate user-vs-ledger mismatch, relevant business state (refund/dispute/webhook/KYC as appropriate), eligible KB document IDs/versions, source validity dates, evidence outcome, and expected human/gate path.

Use enumerated scenario constructors and validators, not free-form model-created database rows. A card that represents an absent, malformed, ambiguous, foreign-merchant or unsupported fact must say so explicitly. Store the expected label and evaluation oracle in a separate evaluator-only artifact. Runtime prompts and tool adapters receive neither the oracle nor card target fields.

### 3.2 Build artifacts in causal order

1. Freeze taxonomy, scenario schema, scenario quotas, split assignment and seed. Allocate cases across all four desks and supported sub-intents, languages/channels, field-presence patterns, evidence outcomes, gate outcomes, and human paths. Record target counts and minimum slice denominators before generating text. Do not claim reliable per-cell rates for sparse combinations.
2. Create and validate the scenario card and its expected label with deterministic code.
3. From the same card, build synthetic ledger rows and document eligibility metadata. Facts, source IDs, versions and dates are deterministic and versioned. This step happens before ticket prose is written.
4. Render only the merchant-facing scenario into the writer prompt. Exclude target labels, expected routes, source IDs, database status, test rubric, oracle, and hidden trap tags. Include only the user-visible amount/reference/situation that the card intentionally exposes.
5. Write the ticket through the configured OpenRouter role. Require the existing JSON object contract (`subject`, `body`); persist model ID, prompt hash, parameters, returned usage/cost, seed, card hash and timestamp. Append results; never silently overwrite a prior response.
6. Run deterministic checks: output shape, non-empty and bounded text, language/channel constraints, exact visible reference/amount where required, forbidden leakage of label/source/oracle terms, unsupported new identifiers/numbers, and applicable trap invariants. Reject and retain the reason when any check fails; do not repair rejected test records by hand without a new version.
7. Review text using the existing blind voter/judge procedure. Voters and judge see only the written ticket and label definitions, not the card target. Compare their structured labels to the hidden card target in evaluator code; invoke the judge only for disagreements, as the current pipeline does. Record each vote, disagreement, judge version and verdict. Human adjudication is required for uncertain/high-risk cases and a stratified sample of accepted cases.
8. Independently validate the context bundle against the scenario card: ledger rows match the intended true facts; mismatch and absent cases remain intentional; KB sources are approved for the correct desk/sub-intent/language/date; IDs and versions are unique/stable; no foreign merchant fact leaks. A model vote cannot approve source truth.
9. Run SQL, Text Search, and full-flow assertions, then freeze the ticket, context and oracle artifacts together with hashes and a manifest. This accepted bundle is immutable. A change creates a new dataset/fixture version and reruns the gates.

## 4. OpenRouter roles and safe use

Use OpenRouter for ticket wording and, optionally, linguistic variants of approved KB prose. Follow the existing role separation: writer role by split, independent voter roles, and a judge only for disagreement. A writer, voter and judge never see the expected card label; evaluator code compares their output with that label after the call. Log every vote and judge verdict; none of them can create or alter SQL facts.

For KB variants, the prompt receives an approved canonical fact sheet and policy text with explicit allowed claims. The model may change wording, not add facts, obligations, amounts, status, dates, sources, promises, or rules. Compare the output claim-by-claim to the approved source, run policy checks, and require a named human reviewer before `status=approved`. Keep a deterministic canonical document if review is unavailable. Never use the LLM to author ledger metrics, balances, transaction states, source IDs, event counts, pass/fail or evaluation oracles.

Reuse budget estimation, hard stop, usage-based accounting, API-key isolation, bounded transient retries and append-only logs from `openrouter.py`. Persist configuration and actual returned model/version, parameters, prompt hash, input-card hash, output hash, usage, cost, retry/error history and reviewer. Never log API keys. A nonconforming model answer is a rejected record, not a silent retry with changed prompts.

## 5. Split and leakage policy

Maintain separate splits and purposes:

| Split | Generation/review use | Flow use |
|---|---|---|
| Scenario development | Iterate on cards, schemas and fixture builders; all changes versioned | Unit/integration and local demos |
| `flow_e2e_staging` (planned 200 cases, coordinated with #62) | Freeze after balanced card/text/context/oracle review | Release regression on every relevant model, prompt, SQL, Text Search or KB change |
| Qualifier `train` / `val` | Preserve existing writer/review and model-training roles | `val` may diagnose flow behavior while building fixtures; do not train the Qualifier on flow oracle output |
| Qualifier `test_natural` | Preserve as the headline model-only test; do not tune fixture or model choices against results | Use only for a declared final replay, with context/oracle version disclosed; never silently promote it into development data |
| Qualifier `test_traps` | Preserve for per-trap diagnosis only, not an overall headline | Same one-way final replay rule; report per-trap denominators and no tuning |

Do not create an apparent independent test by deriving truth rows from test labels and then presenting their matching rate as independent retrieval generalization. For integrated synthetic replay, context should be generated from the source scenario before the ticket and label are exposed to evaluation. If the original scenario cards for an existing frozen ticket are unavailable, any offline reconstruction is explicitly marked `reconstructed`, reviewed, and excluded from claims that require an independent source-ground-truth test.

## 6. Quality gates for generated data

### Card and source integrity

- Every case validates against the frozen seven-field taxonomy and exactly one named scenario constructor.
- Every factual draft claim expected by the oracle has an eligible source ID/version; every source can be traced to a scenario and fixture version.
- Exact, missing, ambiguous, wrong-merchant, mismatch, stale, unapproved and unavailable conditions are represented deliberately and separately.
- Amount/currency matching distinguishes user-reported values from ledger truth; precision and normalization rules are explicit.
- No expected label, trap label, oracle, hidden source or API secret appears in writer input or runtime prompts.

### Text acceptance and reviewer checks

- Preserve writer output, checks and votes as append-only artifacts. Report attempted, accepted and rejected counts, rejection reasons, vote agreement, judge rate, human adjudication rate and cost per accepted case.
- Check per language, channel, desk/sub-intent and trap family; do not rely on one aggregate acceptance rate. Require enough attempts per planned slice before interpreting its failure rate.
- Inspect the accepted sample for unsupported additions, wrong amounts/references, missing requested information, prompt injection, unsafe promises, language drift and source/oracle leakage.
- Freeze accepted data and hashes before any end-to-end score. A changed writer model, prompt, card distribution, source builder or KB creates a new version and requires re-review.

### Text Search and complete-flow checks

- SQL: exact match returns the expected merchant-scoped source/version and facts; missing, ambiguous and foreign cases return the right non-disclosing outcome; amount/currency conflicts are surfaced as designed.
- KB: measure recall/precision at the configured top-k, no-hit accuracy, wrong-desk search, stale/unapproved exclusion, source-version correctness and prompt-injection exclusion. Token overlap is the deterministic baseline; embeddings are a separate #43 experiment, not a default.
- Full flow: compare the observed path, tool calls, evidence, citations, gate results, human action availability, terminal state and send/idempotency invariants to the evaluator-only oracle.
- Hard failures include a false approved source, cross-merchant disclosure, oracle leakage, a blocked final send, an unsourced factual claim, or a duplicate send. A judge score never overrides these deterministic invariants.

## 7. Cost and reproducibility controls

Before generation, produce a dry-run estimate from planned card counts, role/model prices, prompt sizes and maximum output tokens. Set a user-approved run budget and per-role ceilings; abort before the next call if either ceiling would be crossed. Reconcile the estimate to the API-reported usage/cost after each batch. Preserve partial append-only logs so an interrupted run resumes without duplicate calls. Fix and record random seeds for card allocation and reviewer sampling; LLM prose is not assumed deterministic, so accepted outputs are frozen rather than regenerated from the same seed.

Each release bundle contains: schema version, card-generation config and hash, prompt hashes, split counts, model IDs and decoding parameters, cost report, writer/reviewer logs, human adjudication, synthetic SQL/KB fixture hash, oracle hash, Text Search report, full-flow report and known limitations. No build is called complete until the bundle can be traced from a case back to its scenario and sources.

## 8. Execution sequence

1. Freeze the `FlowScenario`, evidence-manifest and oracle schemas with the companion plan.
2. Audit which original `Card` metadata and validated ticket-to-card links are still available. Do not reconstruct missing scenario truth from model predictions.
3. Select and stratify a new development batch; estimate OpenRouter cost and set the hard ceiling before calls.
4. Generate context deterministically from cards; generate ticket wording with existing OpenRouter writer/voter/judge code; review context sources separately.
5. Build the planned `flow_e2e_staging` 200-case set (#62), with a balanced coverage matrix and locked split manifests.
6. Run mocked CI, SQL/Text Search checks and full-flow scoring. Review failures and revise only development data/configuration.
7. Freeze a new version and run one declared staging evaluation; preserve results and do not tune on the locked staging cases.

### 8.1 Local API replay of accepted tickets

`python -m flow.inject_dataset --limit N` previews a reproducible sample from `val.csv` and makes no HTTP calls. Add `--submit` to send it to the local API. The default split is `val`; `test_natural` and `test_traps` require `--allow-locked-split` and should be used only for a declared final replay. `train` is never an injector option.

The client derives stable ticket IDs, request timestamps, idempotency keys, selection order and request hashes from the split, seed and session ID. A session manifest and append-only JSONL result log are stored under `.local/`; replaying the same session reuses its request identity. The HTTP envelope contains only user-visible ticket fields, never `target`, trap tags, evaluator metadata or source/oracle data. Set `--session-id` to intentionally separate a later replay. The bounded `--limit` is required.

Optional next-turn replies come from a separate JSON file keyed by the original `card_id`, for example `{"val-20261110-001": ["Here is the additional information you requested."]}`. The injector waits for each prior turn's terminal state and posts the next reply only after `sent_open`; `sent_closed` and `closed_manual` cause remaining follow-ups to be logged as skipped, never reopened implicitly. No follow-up text is fabricated from the hidden target. API/model availability and human action are prerequisites; this replay is not a billable model-free CI harness.

Ingress smoke, 10 November 2026: `val-seed-1-n-1` submitted one `val` ticket (`val-train-20261031-05197`). Replaying the same command returned the same `flow_id`, confirming one persisted ingress for this session; the API snapshot reached `awaiting_reroute` on desk `triage`. The run record shows the configured local Qualifier (`d-q4`) unavailable with a connection error, no qualifier label, no context plan, no evidence decision and zero drafts. Therefore this was not a successful inference or end-to-end acceptance; SQL, Text Search and the Drafter were not called. The request log is local under `.local/runs/dataset-injector.jsonl`. API restart recovery and human-gated workflow paths also remain unverified.

Before using locked splits, freeze the session ID, split, seed, selected case manifest, flow/model/prompt versions, context fixture version and evaluation purpose. Do not tune on locked-split outcomes.

## 9. Limitations

Chinese-provider LLMs can produce fluent but factually inconsistent prose. Blind relabeling alone does not validate SQL truth or KB authority. Scenario/source integrity and human source approval are separate gates. A successful synthetic end-to-end test validates implementation behavior against the simulator; it does not establish real-world database coverage, production quality or causal business impact.
