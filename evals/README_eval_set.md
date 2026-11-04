# Eval-set v0 — Keelpay copilot (A3-4, issue #9)

`eval_set_v0.csv`: 20 tickets, one row per case. They are the judge of the prototype in S4, the seed of the metrics in S5 and the start of the hand-written set reported apart from the synthetic tests (`finetuned_llm_classifier/docs/scoring_protocol.md`, section 5).

## Origin
- **Inputs:** drafted with an AI assistant (Claude) on 2 November 2026, from a coverage plan written to fill what the generated dataset lacks: a phone one-liner, a reply-all thread, a Belgian formal letter, an instruction hidden in a pasted log, Dutch, two currencies, a screenshot described in words. The dataset's tickets were written by other models (DeepSeek, Xiaomi MiMo), so these are out of its distribution. Fictional merchants and people; no real data.
- **Labels:** written by hand by a team member who does not tune the model, **before any run**, and never changed because of a model output.

## How to label (blind)
Do not open `finetuned_llm_classifier/data/dataset/*.csv` or any model output while labelling.

**The seven `label_*` columns** follow `finetuned_llm_classifier/docs/label_definitions.md`. In short:

| Column | Allowed values |
|---|---|
| `label_intent` | `payment_status` · `dispute` · `technical_api` · `compliance` · `OTHER` (understood, no desk fits) · `UNDEFINED` (two equal requests, too vague, unreadable) |
| `label_sub_intent` | payment_status: `delayed_credit` `missing_payment` `status_inquiry` `refund_status` · dispute: `unauthorised_fee` `chargeback` `duplicate_charge` `amount_mismatch` · technical_api: `webhook_down` `api_error` `auth_failure` `integration_question` · compliance: `kyc_update` `account_hold` `document_request` `regulatory_question` · or `OTHER` / `UNDEFINED` (repeat the intent if the intent is `OTHER` or `UNDEFINED`) |
| `label_transaction_id` | `TX-` + 6 digits, normalised · `UNDEFINED` (present but malformed or ambiguous) · empty (absent) |
| `label_amount` | `12500.00` (dot, two decimals, no separator) · `UNDEFINED` · empty |
| `label_currency` | ISO code (`EUR`, `GBP`, `CHF`…) · `UNDEFINED` · empty |
| `label_urgency` | `high` (deadline within 48 h, activity blocked, funds or account frozen, regulatory deadline) · `medium` (real problem, not blocking) · `low` (informational) · `UNDEFINED` |
| `label_sentiment` | `negative` · `neutral` · `positive` · `UNDEFINED` |

**The three copilot columns** (the course template). In v0 they are **derived from the hand labels by fixed rules**, not labelled a second time: desk from `label_intent` (`OTHER` / `UNDEFINED` → human triage); hand-over `yes — triage` for `OTHER` / `UNDEFINED`, `yes — confirm the desk` for a dispute or compliance ticket with `high` urgency (the brief's criticality rule), otherwise `no — L2 draft`; evidence = the reference, amount and currency labelled, plus the ledger record to look up. What each column means:
- `expected_output_or_action`: the desk, then what a good draft must and must not do, in one line, specific enough for two graders to say yes or no. Example: *"Payments desk; the draft names the payment and its status, asks for nothing already given, promises no date not backed by the ledger."* For a ticket that goes to a person, write what the person must see.
- `evidence_or_source`: what the answer rests on — the reference, amount or deadline in the message, the ledger record to look up, or the policy.
- `hand_over_to_a_person`: `yes — triage` for `UNDEFINED` / `OTHER`; `yes — confirm the desk` for a critical ticket (dispute or compliance with a deadline or high urgency, per the brief); otherwise `no — L2 draft`.

Write in `notes` anything you hesitated on: it is where disagreements are explained later.

## After labelling
Run the copilot or the router on the 20 rows, then two people grade the outputs independently. Results and the origin of the set go in `evals/report_v0.md` and `04_architecture.md` §7.
