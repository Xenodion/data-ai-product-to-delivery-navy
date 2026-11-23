# Production-readiness checklist — Keelpay copilot

Issue #22, requirement of the shared LLMOps project brief. Checked on 23 November 2026 against `main` and the open pull requests named in the rows. Each item points to a file or a result in the repository; nothing here is a claim without one.

**Status:** **Ready** = built and evidenced in the repo · **Partial** = built but not measured, or measured but not built in · **Missing** = neither. Paths are relative to `agentic-workflow-subproject/` unless they start with `../` (repository root).

## Verdict

| Scope | Ready? |
|---|---|
| Synthetic course demo, run locally | **Yes**, with the demo limits of the last section |
| Keelpay pilot on real tickets | **No.** 6 blocking items, listed at the end (⛔ in the tables) |
| Production rollout | **No.** Decided by the pilot A/B only (`../06_ab_protocol.md` §7) |

## 1 · Evaluation

| Item | Status | Evidence |
|---|---|---|
| Frozen dataset with disjoint splits, read once for the tests | Ready | `data/dataset/` (train 1,922, val 293, test_natural 610, test_traps 380); `docs/scoring_protocol.md` §8 |
| Metrics that put the costly error first (silent errors, urgent in a wrong desk) | Ready | `ml/qualifier/src/scoring.py`; `docs/scoring_protocol.md` |
| Baselines and the champion compared on every split | Ready | B0–B3, D, D-q8, D-q4 in `docs/scoring_protocol.md` §8; D-q4: 0.7 silent errors per 100 against 33.9 for B2 |
| Hand-written eval-set, labelled before any run, with a grading guideline | Ready | `../evals/eval_set_v1.csv` (100 cases), `../evals/README.md` |
| Two human graders and an LLM judge, agreement measured | Ready | 80 % human–human, 95.8 % human–judge (`../05_metrics.md` §5, `../evals/grading/`) |
| Full flow measured end to end | Partial | last run 13 November, before the guardrails (`../evals/report_v0.md`); the runtime Qualifier now uses constrained decoding, not what the D-q4 benchmark measured (`../spec.md` §3 v3) |
| ⛔ Eval-set replay of the current flow before the pilot | Missing | condition 1 of `../08_launch_memo.md` §3 (PR #88) |
| Automated evaluation in CI on every prompt, handler or pipeline change, failing under a threshold | Missing | no CI workflow in the repository (`.github/` absent); issue #19 |
| Unit tests of the flow and the scorer | Partial | 306 tests in `tests/` (239 flow, 61 qualifier, 4 confidence) and `tests/test_layout.py`; not run automatically (no CI) and not re-run for this checklist |

## 2 · Monitoring

| Item | Status | Evidence |
|---|---|---|
| Per-node latency, outcomes and Drafter cost recorded | Ready | `flow/metrics_store.py` (SQLite events and aggregates); measures in `docs/design/flow-v2/measures-and-gates.md` |
| Traces with prompt name, label and version | Partial | `@observe` spans in `flow/pipeline.py`, `flow/drafter.py`, `flow/human_actions.py`; prompt versions in `docs/design/flow-v2/prompt-management.md`; one trace per ticket from a deployed run not captured yet (#41) |
| Thresholds for latency, drift and quality, with a reader and an action | Ready (on paper) | four layers in `../07_operations.md` §2, computed in `../evals/07_monitoring.ipynb` (PR #86): PSI bands, invalid ≤ 3.4 %, audit alarm ≥ 13 of 800, p95 ≤ 18 s |
| Alerts that fire on those thresholds | Missing | no scheduler or alerting; #20, #41 |
| ⛔ Weekly labelled audit sample running | Missing | process defined in `../07_operations.md` §2, not staffed |

## 3 · Rollback

| Item | Status | Evidence |
|---|---|---|
| Prompt rollback | Ready | move the Langfuse `production` label to the previous immutable version (`docs/design/flow-v2/prompt-management.md`) |
| Model rollback | Partial | previous version by `qualifier_model_uri`, `qualifier_model_version` and MD5 in `flow/config.toml`, or the Registry alias (`docs/scoring_protocol.md` §8); manual, not rehearsed |
| ⛔ One switch for the copilot level (Judge off, drafting off, routing off, copilot off) | Missing | `copilot_mode` specified in `../governance.md` Session 4 and `../07_operations.md` §4; not built (#60); only `ledger_enabled` and `knowledge_enabled` exist in `flow/config.toml` |
| Rollback criteria with owners | Ready | `../07_operations.md` §4, `../spec.md` §11 (PR #90) |
| ⛔ Rollback tested before a demo or release | Missing | test defined (eval-set at L1 produces no draft, manual queue at L3), never run (#60) |
| Model unavailable does not lose the ticket | Ready | timeout 120 s then Re-router with status `unavailable` (`flow/config.toml`, README "Run the ticket flow locally") |

## 4 · Cost caps

| Item | Status | Evidence |
|---|---|---|
| Cost per ticket known | Ready | Qualifier €0.59 per 1,000 tickets on CPU (`../02_investment_memo.md`, efficiency front, PR #87); Drafter cost per call recorded (`flow/metrics_store.py`) |
| Bounded tokens and calls per ticket | Ready | `drafter_max_tokens = 700`, `qualifier_max_tokens = 160`, `transient_retries = 3`, `max_automated_turns = 3`, `max_reroutes = 2` (`flow/config.toml`); at most 7 model calls per ticket in the target (`../04_architecture.md`) |
| Billed cloud resources torn down after use | Ready (procedure) | "Cost and teardown" in `README.md`: undeploy then delete every endpoint, never over a night; pipeline jobs checked after each run |
| Spending cap that stops calls when a budget is reached | Missing | no budget check in `flow/`; the provider key's own limit, if any, is set outside the repository |
| Endpoint idle cost | Partial | a Vertex endpoint has no scale to zero (`README.md`); demo-only deployment rule (#73) |

## 5 · Data handling and security

| Item | Status | Evidence |
|---|---|---|
| No real customer data anywhere | Ready | synthetic corpus and world only (`../governance.md` Session 3); external Drafter and Langfuse allowed for synthetic data only (`../spec.md` §7) |
| Ticket and draft text kept out of traces and metrics | Ready | `@observe(capture_input=False, capture_output=False)` in `flow/`; allowlisted metric labels (`docs/design/flow-v2/measures-and-gates.md`) |
| Secrets out of Git and out of images | Ready | `.env` ignored (`.gitignore`), `.env.example` holds placeholders; `OPENROUTER_API_KEY` read at run time, never copied into an image (README "Container demo") |
| Personal data in team exports kept out of Git | Ready | `audit_logs*.csv` ignored (PR #89) |
| Merchant isolation | Partial | tools scoped to the envelope's `merchant_id` (`flow/tools.py`, `tests/flow/test_tool_barrier.py`); foreign merchant IDs hard-blocked at the final gate (`flow/policy.py`); no cross-merchant test on a multi-tenant store (#31) |
| Prompt injection from the ticket | Partial | ticket wrapped in delimiters it cannot close (`flow/drafter.py`); no tool can send, write or refund (`../04_architecture.md` §1); injection cases in the eval-set, not re-measured |
| Authentication on the API | Missing | local single-user demo, not exposed on the network (README "Local API and frontend") |
| ⛔ Legal basis, retention, provider terms for real tickets | Missing | 90-day retention is a proposal; DPO decision open (`../governance.md` Session 3, open settings) |

## 6 · Reliability

| Item | Status | Evidence |
|---|---|---|
| Idempotent intake and send; no duplicate send | Ready | idempotency keys in `flow/api.py` and `flow/api_store.py`; send rules in `docs/design/flow-v2/policy-check.md` |
| State survives a restart | Ready (local) | SQLite state and LangGraph checkpoints on a named volume (`flow/config.toml` `[api]`, `flow/deploy/compose.demo.yml`) |
| Shared store for several replicas | Missing | SQLite is the local adapter; PostgreSQL planned (`docs/design/flow-v2/measures-and-gates.md`) |
| Human on every send, gates before it | Ready | Policy check (node 10) and Final compliance gate (node 14) before every simulated send (`flow/human_actions.py`) |

## 7 · Known limits

- **Synthetic scores are optimistic.** The tickets are cleaner than real mail; comparisons between systems are the finding, not the absolute rates (`docs/scoring_protocol.md` §7).
- **The urgent guardrail fails on the model alone.** One urgent ticket of 167 lands in a wrong desk on test_natural; the Re-router and the weekly sample must catch it (`docs/scoring_protocol.md` §8).
- **Rare serious errors cannot be certified** at these sample sizes (`../governance.md` Session 2); they are handled by stopping and rollback rules.
- **Value is sized, not measured.** Time saved is an assumption until the A/B (`../02_investment_memo.md`, `../06_ab_protocol.md`).
- **The Policy check is lexical.** It can miss paraphrases and flag benign text (`docs/design/flow-v2/policy-check.md`).
- **Token probabilities do not flag wrong answers.** AUC about 0.6 on intent, sub-intent and urgency (issue #45, `ml/confidence/`).

## ⛔ Blocking before a pilot

1. Eval-set replay of the current flow (§1).
2. Weekly labelled audit staffed (§2).
3. `copilot_mode` built (#60) and 4. rollback tested at L1 and L3 (§3).
5. Legal basis and retention for real tickets (§5).
6. Real tickets, models and traces inside Keelpay's cloud, not the demo's external services (`../spec.md` §7).

Non-blocking but expected before a rollout: CI evaluation (#19), alerting (#20, #41), a spending cap, API authentication, a shared database.
