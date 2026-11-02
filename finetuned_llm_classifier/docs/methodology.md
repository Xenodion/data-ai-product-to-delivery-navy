# Methodology: how we test, control and choose without wasting money

Short guide to the process of this sub-project and the habits that kept it cheap and honest. It is written for a student team working alone on a fine-tuning project with a limited budget. The journal of what was actually done, step by step, is in `notebooks/`; the frozen rules are in `docs/scoring_protocol.md`; the plan is in `docs/roadmap.md`.

## 1. The order of work

1. **Fix the output contract** (closed lists of values, `src/dataset_build/schema.py`). Dataset, scoring and prompt all read from it.
2. **Write the scoring protocol before any result exists**: metrics, cost matrix, the systems compared, the decision rule. Changes after seeing results are appended with a date and a reason, never silently edited.
3. **Build the dataset with gates**, then freeze it.
4. **Score cheap baselines first** (majority, rules, TF-IDF + logistic regression). They are the bar the model must clear, and the strongest one is often close to free.
5. **Measure locally before paying for a GPU**, then run a **smoke test** on the GPU, then **one full run**, then read the curve.
6. **Choose on the validation set, read the test sets once**, at the very end.
7. **Write the journal as you go**, in the order of discovery (intent, run, then reading).

## 2. Habits that protect the result

| Habit | Why | Where |
|---|---|---|
| Labels come from the scenario card; the language model only writes the text | no label noise from the generator, labels are known by construction | `src/dataset_build/cards.py` |
| Two blind voters, a stronger judge only when they disagree | cheap review, expensive model used where it matters | `review.py` |
| A ticket that fails is quarantined, never fixed, retried or reused | no hidden tuning of the data toward what passes | `data/dataset/*_quarantine.csv` |
| Tests written by another model than train and val | the model is not scored on the style of its own writer | `config/run.toml` |
| Stop rules (non-conformity, failing trap type, cost per ticket) and a hard budget | the run stops by itself and is diagnosed, instead of burning money | `production.py` |
| Same tickets for every system, paired bootstrap on the differences | a difference is believed only if its interval excludes 0 | `src/scoring.py` |
| Test sets read once; settings chosen on val only | prevents choosing the winner on the test set | `docs/roadmap.md` rules |
| Counts with their denominator below 20 tickets, no interval | small groups are shown, not over-interpreted | `docs/scoring_protocol.md` |
| Check the scorer on trivial systems (perfect, everything to a human) | a scorer bug is found before it ruins a comparison | notebook 2 |

## 3. Measure before you spend

- **Token lengths with the real tokenizer** (local, free). Our chats had a median of 495 tokens and 41 percent were over the course's 512 limit, which would have cut the JSON answer off four tickets in ten. One measurement changed a setting that no loss curve would have flagged.
- **Check what the loss learns from.** With the library collator, only the answer (about 30 to 50 tokens of 500) is in the loss. Check the decoded tokens of a few examples and that the inference prompt is exactly the beginning of the training text.
- **Compile the pipelines locally** before submitting (`kfp` compile is free and catches parameter mistakes).
- **Smoke test** (`--smoke`): 200 tickets, 40 steps, 20 predictions. It answers four questions for a fraction of a full run: does everything load, how long does a step take, does the loss go down, is the output valid JSON. The time per step gives the cost of the full run before launching it.
- **Try the cheaper compute on the smoke test first.** float16 gave the same losses at every step and ran 3.1 times faster than float32 (213 s against 654 s for 40 steps), which turned a six-hour run into about two.

## 4. Controlling the cost

- **Say what is local (free) and what is billed**, and what stops it, before every command that bills.
- **Pipeline jobs are ephemeral; an endpoint never is.** A Vertex endpoint bills per node and per hour, has no scale to zero and keeps billing while idle. No endpoint is deployed before the tests are done and one model is chosen; if a deployment is needed it is deleted the same day. After every run, check in the console that nothing stays `RUNNING` or `PENDING`.
- **Cache and skip.** An unchanged step is skipped by the pipeline (`SKIPPED` in the state); a changed parameter reruns only what depends on it.
- **Watch the run without paying for it.** The job writes its TensorBoard files to the bucket while it runs; reading them gives the live loss and the step rate, so the end time and the cost are known early.
- **Keep an internal budget below the hard limit of the key**, log the cost of every call, and compare the logs with the counter (ours differed by 0.37 USD, which is noted in the journal).
- **Smaller is cheaper to try**: a smaller model, or a merged and quantised model on CPU, is a new system to score, not a replacement of the decision rule (see `docs/roadmap.md`, G6).

## 5. Getting back to the sweet spot without recomputing

The training saves a checkpoint every 50 steps (`save_steps` equal to `eval_steps`), keeps the best two (`save_total_limit=2`), and at the end loads the one with the lowest validation loss (`load_best_model_at_end`, `metric_for_best_model="eval_loss"`). If the validation loss starts to rise, the adapter that is saved is the one at the minimum, not the one at the last epoch: overfitting costs the GPU time already spent but does not force a new run. The full loss history is also saved with the adapter (`log_history.json`) and as TensorBoard files in the bucket, so the step of the minimum is known and a next, shorter run can stop there. The validation loss is not the final judge: the scores on val decide. In our full run the lowest validation loss was at the last evaluation (step 1250 of about 1300), so the mechanism was not needed; the oscillations seen in the middle of the run were noise, which is why a trend over several evaluations, not one point, is what to read.

## 6. Choosing

- A model is kept only if it beats the best baseline on the expected cost per ticket with an interval that excludes 0, keeps valid JSON at 99 percent or more, and does not send more urgent tickets to a wrong desk. Otherwise the report says the simpler option is kept; this is a valid result.
- Diagnose by field and by trap type before changing a setting, and change settings on val only.
- Report the cost and the speed next to the quality: the interesting result is the front between them, not the best score alone.

## 7. The journal

Notebooks are written in the order of discovery, as in a time series where the result is not known before the cell is run: say what is about to be done and why, run, read the result, then decide the next step. The reading is never written before the output it comments on.
