# Confidence study (issue #45)

Question: can the probability of the tokens the Qualifier (D-q4) writes be used as a confidence threshold, so that doubtful tickets go to the Re-router with a flag `UNCONFIDENT` instead of to a desk? Does it lower the silent errors, at what cost in tickets sent to a human, and does it reach zero urgent tickets in a wrong desk?

Status on 7 November 2026: **replay done for `val`, the two test sets are replayed on Vertex and not analysed yet.** Nothing here changes the flow; a threshold would need a separate decision.

## How the data is made

- `ml/qualifier/src/pipelines/confidence_signals_pipeline.py` replays a split through the same GGUF as the flow (`model-q4.gguf`, URI in `flow/config.toml`), greedy decoding, same prompt, CPU only on Vertex (8 CPU, 16 GB, about 13 s per ticket). The job stops on its own, nothing to tear down.
- Submission: `uv run python ml/qualifier/scripts/pipeline_runner.py confidence --test-file <split>.csv --gguf-uri <uri> --confirm-billable-run` (billed to the school project; `--smoke` replays 20 tickets).
- The output is one JSON line per ticket: the text, each token, its log probability and the 5 best candidates.
- `src/signals.py` reads the probability of a field value (the first token and the product of its tokens, JSON syntax ignored). `src/analysis.py` joins it to the labels and simulates a threshold. Tests: `tests/confidence/`.

## The runs (Vertex project `agentics-workflows-2`, region `europe-west2`)

| Split | Tickets | Job id (end of the job name) | State on 7 Nov |
|---|---|---|---|
| `val` | 293 | `20261107094738` | done, downloaded |
| `test_natural` | 610 | `20261107094752` | running, about 2.2 h from 09:48 |
| `test_traps` | 380 | `20261107094805` | running, about 1.4 h from 09:48 |
| `val` smoke | 20 | `20261107092704` | done (check only) |

Fetch a finished run into `.local/runs/confidence/<split>.jsonl` (ignored by Git):

```bash
uv run python -m ml.confidence.scripts.fetch_signals test_natural 20261107094752
uv run python -m ml.confidence.scripts.fetch_signals test_traps 20261107094805
```

State of a job: Vertex console, Pipelines, name `keelpay-router-confidence-signals-pipeline-<job id>`. The files stay in the bucket under `pipeline_root/158407666882/<pipeline name>-<job id>/`.

## First result, on `val` only (293 tickets)

- Too few errors to pick a threshold: 1 silent error, 0 urgent ticket in a wrong desk.
- The probability does not separate right from wrong answers on `intent` (AUC 0.60, 5 errors), `sub_intent` (0.60, 6) and `urgency` (0.64, 6): wrong answers have the same probability as right ones, about 0.999. The fine-tuned model is overconfident.
- The single silent error has probability 1.0 on `intent`: no threshold on `intent` or `urgency` catches it. A threshold high enough to reject it would send 41 % of the tickets to a human.
- `transaction_id` is the best signal: AUC 0.84, mean probability 0.885 when the id is wrong against 0.989 when it is right (5 errors, fragile).
- Reading: for the desk and the urgency, token probabilities look close to useless here. A negative result is valid and goes in the architecture document as such.

## Next steps

1. Fetch the two test runs (commands above) when the jobs have succeeded.
2. Fix the rule on `val` before opening them: which fields, which threshold. With 1 silent error the only defensible choices are a threshold on `transaction_id` and a report of the signal's AUC. Then apply the frozen rule once to `test_natural` and `test_traps`.
3. Write notebook `notebooks/01_signals_and_threshold.ipynb` on the real data: look first, interpret after (journal style of `ml/qualifier/notebooks/`).
4. Report: silent errors and urgent tickets in a wrong desk before and after, the share sent to a human, with intervals. 1 urgent case in 167 cannot prove zero: say so. Update the issue #45 and one line in `04_architecture.md` section 8.
