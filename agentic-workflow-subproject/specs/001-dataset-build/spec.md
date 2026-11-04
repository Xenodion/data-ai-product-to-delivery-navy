# Feature Specification: Synthetic ticket dataset build

**Created**: 2026-10-31 | **Status**: Draft, decisions of the 2026-10-31 brainstorm (validated at each gate)

**Input**: build a labelled synthetic dataset of Keelpay merchant tickets (FR/EN) to fine-tune a small LLM with LoRA, to score it, and to score the baselines (rules, classical ML, prompted model).

## Decisions (invariants)

- **Contract**: `src/dataset_build/schema.py` (`TicketLabel`) and `docs/label_definitions.md`. Seven string fields; `UNDEFINED`/`OTHER` uppercase sentinels; `""` = absent, only on `transaction_id`, `amount`, `currency`.
- **Labels come from the scenario card, not from an LLM**: a seeded sampler draws a card, tables derive the label, the LLM only writes the ticket. Rejected: one LLM writing and labelling (label noise).
- **LoRA SFT only.** No reward model, no RL. Confidence and the deterministic-vs-ML methodology are a separate parked sub-project; the dataset metadata is its base.
- **Only Chinese-family models** (Vincent's rule: American models are too expensive for a fictional course project). Roles and models (OpenRouter ids of 2026-10-31, to confirm at gate 1):

  | Role | Model | $/M in / out |
  |---|---|---|
  | Writer, train and val | `deepseek/deepseek-v4.1-flash` | 0.045 / 0.50 |
  | Writer, tests (another family) | `xiaomi/mimo-v2.6-flash` (GLM-5.3 refuses to disable reasoning) | 0.14 / 0.28 |
  | Blind voter A | `qwen/qwen3.7-flash` | 0.03 / 0.13 |
  | Blind voter B | `inclusionai/ling-3.1-flash` (MiniMax and StepFun refuse to disable reasoning) | 0.075 / 0.225 |
  | Judge (disagreements only) | `moonshotai/kimi-k2.6` | 0.65 / 3.41 |
- **Urgency rule**: a real problem for the merchant is at least `medium`, `low` is for informational requests (the first canary showed voters and judge reading `low` on problems as `medium`). **Labels are LLM-validated, not human-validated** (disclosed limitation); Vincent reads the 30 seeds and 30 rows at gate 2.
- **Scoring table written and frozen before any result.** No hardcoded business parameters: weights, sizes, seeds in TOML.
- Synthetic data only: no real ticket leaves Keelpay's cloud.

## Sizes

Pool 9,000 cards (natural distribution, free). `train` 2,000; `val` 300 (same distribution; hyperparameters and early stopping); `test_natural` 500 (aggregate scores and cost per ticket; +-2.6 points on the whole set, about 59 urgent dispute/compliance tickets for +-7.7 points on the headline subset); `test_traps` at least 20 cards per trap type (about 390; diagnosis only, large failures visible). All splits disjoint, split on cards before any text is written. Target X per split, **X minus 10 % accepted**.

## Scenario cards

- **Label-determining variables**: intent, sub_intent (incl. the reason behind a sentinel: two equal requests with their two intents, too vague, truncated, unintelligible; OTHER kinds), urgency and sentiment with an imposed textual cue, transaction_id / amount / currency cases.
- **Style variables (metadata only)**: language, channel, length, persona, sector, noise, subject line.
- **23 traps**, each with its implied label (ID variants, lookalikes, malformed and double references, amount formats, lone `$`, missing currency, thank-you hiding a problem, furious but not urgent, polite but urgent, prompt injection, other language). Constraints keep implausible combinations out (no reference on an OTHER intent, none on empty kinds).
- Weights live in `config/cards.toml`; the train trap rate is about 35-40 %.

## Writing and checking the tickets

Chain per ticket: **deterministic checks** (schema, grounding of reference and amount, no ID-shaped string where the label is empty) -> **two blind voters** read the ticket without its label, their answer is compared to the card label field by field (free) -> **judge only when a voter disagrees**. A ticket the checks or the judge find non-conforming is **discarded, never retried**: a non-conforming ticket mostly means an incoherent combination of parameters, which fails again. It is replaced by a reserve card (same trap type for `test_traps`).

| Set | Deterministic | Voter A | Voter B | Judge |
|---|---|---|---|---|
| `test_natural`, `test_traps` | 100 % | 100 % | 100 % | on disagreement |
| `val`, `train` | 100 % | 100 % | 25 % sample (estimates the train defect rate) | on disagreement |

Every discard is logged with its reason and the card parameters. They are counted per trap type and per pair of parameters, to fix the prompt or add a constraint in the TOML, never to retry. A trap type mostly discarded is a signal (the survivors would be the easy cases).

## Incremental run and gates

One append-only JSONL log of API calls (resumable, auditable). Batches grow: 100, 250, 500, then the rest. After each batch, check before continuing:

| Stop rule (ASSUMPTION, adjust after batch 1) | Threshold |
|---|---|
| Non-conformity rate, all rows | > 30 % |
| One trap type with at least 10 attempts | > 50 % non-conforming |
| Measured cost | > 1.5 x estimate |

| Gate | Content | Passes if |
|---|---|---|
| 0 | card smoke test (done); prompt dry-run without API; validators tested on hand-made bad tickets | all green |
| 1 | 30 seed cards (stratified, not random), Vincent reads all 30 | at least 27/30 accepted without edit (0 defect in 30 bounds the defect rate under about 10 %) |
| 2 | first 100 random train cards through the full chain; Vincent reads 30: 10 flagged, 20 passed | at most 1 defect among the 20 passed; cost per row at most 1.5 x estimate |
| 3 | batches up to 500, automatic only, spot-check 10 | no trap type under 50 % pass rate; near-duplicate rate and variety of openings acceptable |
| GO | the rest | |

Validation is per **role**: the tests' writer (MiMo) gets a reduced gate 2 (60 `test_traps` cards, 15 read) and its automatic pass rate must stay within 10 points of the train writer's. Changing a model or materially changing a prompt after gate 2 repeats gate 2 for that role on 100 fresh cards. Passing rows are kept: no work is thrown away.

After generation: a similarity filter removes from train any ticket too close to a test ticket. A hand-written out-of-distribution set (about 30) is reported separately.

## Budget (assumptions to replace with measures at gate 2)

3,190 rows, 20 % margin. Measured offline: the writing prompt is about 450 input tokens (not the 3,300 first assumed); output 250 tokens and a voter prompt of about 2,300 tokens (definitions document included) are still assumptions. Writing 0.8 $, voters 1.9 $, judge on 20 % of rows 2.8 $, seeds 0.2 $: **about 5.8 $, 8.7 $ with margin; worst case about 23 $** (40 % disagreement, output x4 if reasoning is not disabled, `kimi-k3.1-pro` as judge). The OpenRouter key has a hard 10 EUR limit (Vincent, 2026-10-31): the cost stop rule must trip well before it, and a payment-required error from the API halts the run (never retried). The real variable cost of the project is the Vertex training, not the data.

## Scoring protocol (to freeze in `docs/` before results)

Table, not a single number: valid-JSON rate; exact match on `transaction_id`, `amount`, `currency`; macro-F1 on `intent` and `sub_intent`; accuracy and recall on `high` for urgency; UNDEFINED/OTHER as abstention (abstention rate, precision when answering, **confident-and-wrong rate**); desk accuracy after the decision table; expected cost per ticket from a cost matrix (urgent ticket in wrong desk > confident wrong > UNDEFINED) feeding the sizing; same table for the baselines (regex, TF-IDF + logistic regression, prompted base model) and the fine-tuned model; headline numbers from `test_natural`, slices by language, noise and trap from `test_traps`; paired bootstrap confidence intervals (same tickets for every model).

## Success criteria

- **SC-001**: same seed, same cards, byte for byte (met).
- **SC-002**: 100 % of rows pass `TicketLabel`; 0 grounding violations in the tests.
- **SC-003**: gates 1 to 3 passed before the full run; defect rate estimated on train from the voter-B sample.
- **SC-004**: every trap type has its minimum in `test_traps` (X minus 10 % tolerated for train only).
- **SC-005**: measured cost within 1.5 x the estimate.

## Out of scope / parked

Reward model and RL (DPO only if the evaluation shows a failure SFT cannot fix); confidence calibration and the deterministic-vs-ML methodology (separate sub-project); real Keelpay tickets; American models.
