# NAVY Qualifier: data science and LLMOps masterclass

This is the working handbook for experiments, model comparison, diagnostics, tracking, and model lifecycle in the Qualifier project. It complements the fixed historical model-metric definitions in [`scoring_protocol.md`](scoring_protocol.md), the Router-specific decision tree and derived metrics in [`error-consequences.md`](../../specs/004-routing-node/error-consequences.md), and the recovered execution checklist in [`llmops_recovery_tasks.md`](llmops_recovery_tasks.md).

## 1. The question the model answers

The model converts a support ticket into seven structured string fields. A deterministic product rule then uses some of those fields to route the ticket. This is a **structured extraction plus decision-support problem**, not ordinary single-label classification and not an autonomous agent.

The evaluation must answer three different questions:

1. **Did the model understand the ticket?** Field-level extraction and classification quality.
2. **Would the product take the right action?** Routing, human review, urgency, and reference correctness.
3. **Is the candidate worth operating?** Latency, memory, availability, and cost, with measured values separated from scenario assumptions.

No single accuracy score answers all three. A prediction can be mostly correct while sending an urgent case to the wrong desk; a perfectly safe abstention can have zero silent errors but poor automation. Report the quality and the trade-off together.

## 2. The right error matrix for this use case

The usual binary TP/TN/FP/FN table is useful only after defining the event. It is not a complete description of a seven-field JSON output. Use a small family of complementary matrices and report raw counts as well as normalized rates.

### A. Routing action matrix (primary operational matrix)

Rows are the **true destination** derived by the documented routing policy; columns are the model output's **predicted action**:

| True \\ Predicted | Payments | Disputes | Technical | Compliance | Human review |
|---|---:|---:|---:|---:|---:|
| Payments | correct route | wrong desk | wrong desk | wrong desk | safe abstention |
| Disputes | wrong desk | correct route | wrong desk | wrong desk | safe abstention |
| Technical | wrong desk | wrong desk | correct route | wrong desk | safe abstention |
| Compliance | wrong desk | wrong desk | wrong desk | correct route | safe abstention |
| Human review | false automation | false automation | false automation | false automation | correct review |

Keep invalid JSON, `OTHER`, and relevant `UNDEFINED` outcomes visible as **reasons for human review** in a companion table; do not silently merge them into one failure class. Produce this matrix once for all tickets and again for the high-urgency cohort. The latter exposes the costly urgent misroutes directly. Add row totals and show both counts and row percentages. Empty rows mean the split has no examples for that true desk and should be marked N/A.

### B. Field confusion matrices

- `intent`, `sub_intent`, `urgency`, and `sentiment`: multiclass confusion matrices, with explicit `OTHER`, `UNDEFINED`, and `INVALID_OUTPUT` categories where they can occur. Show counts; optionally show row-normalized recall in a second panel.
- Urgency: additionally show a binary `high` versus `not_high` matrix. Here **FN means a truly high-urgency ticket predicted not-high**, and **FP means a non-high ticket escalated to high**. These have different operational costs, so report both.
- `transaction_id`, `amount`, and `currency`: exact-match correct/incorrect counts and error buckets (missed value, invented value, wrong value, wrong normalization). A huge literal-value confusion matrix is usually unreadable and low value.
- Whole JSON: exact-record accuracy may be shown as a strict diagnostic, but it should not replace field and routing metrics.

For a binary one-versus-rest view, define the positive class explicitly. Example: for “urgent ticket sent to the correct desk,” TP is a high-urgency ticket routed to its correct desk, FN is a high-urgency ticket not routed correctly, FP is a non-high ticket routed into that defined urgent-correct class (usually not a useful standalone product metric), and TN is the remainder. Because that FP definition is awkward, prefer the high-urgency routing matrix plus `urgent_wrong_desk_rate` and `recall_high_urgency`.

### C. Project headline measures

Keep the frozen contract in [`scoring_protocol.md`](scoring_protocol.md): silent errors per 100 tickets; urgent tickets in a wrong desk (denominator: high-priority tickets); error severity points; desk accuracy; auto-routed rate; needless human review; JSON contract validity; exact reference fields; urgency recall; macro F1 for intent and sub-intent.

The severity score is a transparent **relative point assumption**, not euros. Report its definition and a sensitivity view, especially the urgent-double-weight metric already in the scorer. Do not invent an expected-loss euro figure unless the probability and impact inputs have evidence and uncertainty ranges.

## 3. Metric selection: useful, misleading, and forbidden shortcuts

| Metric/view | Why it helps here | What it can hide |
|---|---|---|
| Silent-error rate | Captures a wrong definite answer that could pass unnoticed | Does not distinguish an urgent wrong desk from a minor extraction error |
| Urgent wrong-desk rate + count | Directly exposes the critical routing failure | Small urgent denominator makes one ticket move the rate substantially |
| Error severity and per-ticket distribution | Makes asymmetric error cost explicit | Weights are assumptions; a mean can hide a bad tail |
| Auto-routed / needless-triage | Shows coverage and safe abstention trade-off | High coverage is not quality by itself |
| Desk accuracy and field exact match | Simple diagnostic decomposition | Averages can conceal rare-class failure and do not measure product action alone |
| Macro F1 | Gives rare taxonomy classes a voice | Can obscure calibration, routing consequence, and class support |
| Per-class precision/recall/support | Finds class-specific failure modes | Needs counts and consistent class handling, especially for absent labels |
| Latency p50/p95, peak RAM, throughput | Supports serving decisions | Must name hardware, batch/concurrency, warm/cold state, and measurement boundary |
| Cost per 1,000 and monthly scenario | Makes operating trade-offs reviewable | Label measured billing separately from calculated scenarios |

Do not use accuracy alone, aggregate F1 alone, ROUGE/BLEU for this extraction task, ROC-AUC without calibrated scores, or a single severity point as the selection rule. This model emits hard structured outputs and currently has no confidence score; do not present calibration or selective-prediction claims without new score-producing behavior and a separate evaluation.

## 4. Comparison protocol and uncertainty

1. Freeze dataset revisions, schema, scorer, prompt, and decision policy before candidate evaluation. Record SHA-256 and row count for each split.
2. Use training data for fitting. Select hyperparameters and operating choices on validation only.
3. Compare models on the exact same ticket rows and order. For paired candidates, bootstrap the **per-ticket difference** with a fixed seed; do not compare independent confidence intervals as if they were a paired test.
4. Show 95% intervals, denominators, and event counts. For urgent-error rates, report `wrong / high-urgency total`; for small trap families, show counts and label them diagnostic instead of implying stable estimates.
5. Make one final test read after selection. Test-set findings are reporting, not another tuning loop. If a genuinely new system (such as B3) has a valid historical test export, run a predeclared one-time score against the frozen test split and keep an audit trail. Never tune on the resulting errors.
6. Record the selection rule and decision before seeing a new candidate's results. Preserve rejected candidates and reasons instead of deleting or renaming runs.

When bootstrapping, resample tickets as the sampling unit and preserve all fields for each ticket together. Do not bootstrap individual JSON fields independently; that breaks the correlation between extraction errors and routing actions.

## 5. Charts that explain decisions

Every chart needs a question, population/split, denominator, units, and a visual direction for better. Use a consistent system color map, fixed metric definitions, and labeled counts. Avoid 3D charts, radar plots, dual axes, unlabeled percentages, and truncating bars without a visible axis break.

Recommended dashboard set:

1. **Quality versus operating cost/latency:** scatter plot, lower-left preferred; encode estimated versus measured values with different marker styles or a clear note. Do not hide candidates that lack a cost estimate.
2. **Silent errors and urgent misroutes:** two aligned dot/bar panels; label urgent denominator and raw wrong/total count.
3. **Routing action matrix:** count heatmap and row-normalized heatmap, same class order, with zero-support rows marked.
4. **Field diagnostics:** one confusion matrix per field or compact small multiples, with class supports; never force long transaction IDs into a heatmap.
5. **Error profile:** per-ticket severity distribution and Pareto-style error buckets, plus trap-family counts. Keep small trap families visibly small.
6. **Training history:** train and validation loss by optimizer step, with evaluation points, selected checkpoint, and best validation step annotated. Loss explains optimization; it is not the model-selection score.
7. **Latency distribution:** p50/p95 and sample size by named machine and run, not a single unlabeled average.

SVG/PNG charts belong under MLflow run artifacts and should be regenerable from metrics or the immutable prediction artifact plus the matching label split. Chart titles and captions should carry split name and dataset revision when multiple revisions may exist.

## 6. Reproducible model card and tagging contract

Use structured fields with stable keys. Put values in the place that fits their behavior:

| Store | Put here | Examples |
|---|---|---|
| MLflow params | Immutable inputs that define a run | base model/revision, LoRA rank/alpha/dropout, learning rate, epochs, seed, precision, max sequence length, prompt hash, schema version, quantization, pipeline template digest |
| MLflow tags | Search facets and lifecycle/provenance state | `system_id`, `model_family`, `stage`, `split`, `dataset_revision`, `scorer_version`, `tracking_origin`, `git_commit`, `git_dirty`, `vertex_job_resource`, `vertex_region`, `parent_run_id`, `selection_status`, `cost_evidence` |
| MLflow metrics | Numeric comparisons with canonical units | rates as proportions (0–1), severity in points/ticket, latency seconds/ticket, measured cost or estimate in EUR, train/eval loss by step |
| MLflow artifacts | Larger or structured evidence | sanitized predictions, loss JSON, loss plot, confusion matrices, error analysis, model card, environment lock, evaluation report, manifest, checksum receipt |
| KFP / Vertex ML Metadata | Pipeline execution, task inputs/outputs, lineage | pipeline resource, task/component, parameter/artifact lineage, model and dataset artifact references, execution metrics |
| Vertex Model Registry | Deployable model/version identity and lightweight searchable labels | model URI/resource, immutable version, alias snapshot, `system_id`, `source_mlflow_run_id`, `artifact_sha256`, `schema_version`, validation state |

Tags and labels are not the artifact store. Store a URI and SHA-256 in the registry, not a second copy of long reports. Use an MLflow **model version** as the experiment/run lineage and rich artifact location; use the Vertex model version as the deployment identity. The crosswalk must include both immutable resource/version IDs and the source MLflow run ID. Treat mutable aliases such as `champion` as snapshots: log which immutable version the alias pointed to at the time of a decision.

Suggested canonical tag vocabulary:

```text
project=navy-qualifier
task=structured_ticket_extraction
system_id=B3|D|D-q8|D-q4|...
model_family=qwen2.5
model_base_id=Qwen/Qwen2.5-3B-Instruct
model_revision=<immutable commit or unknown>
prompt_sha256=<digest>
schema_version=<version>
dataset_revision=<sha256 manifest>
scorer_version=<commit or digest>
tracking_origin=vertex|historical_import|local
pipeline_job_resource=<full Vertex resource or unknown>
training_run_id=<MLflow run ID or unknown>
selection_status=reference|candidate|champion|rejected
evidence_status=measured|estimated|unknown
```

Use `unknown` explicitly. Never infer a model revision, code commit, training parameter, or cloud job link from a filename. Keep secrets, credentials, raw customer text, and reference labels out of tags and ordinary prediction artifacts. The current project uses synthetic examples; the same data-minimization rules still make experiment artifacts safer and portable.

## 7. What MLflow, Kubeflow/Vertex, and the registry each own

- **Kubeflow Pipelines (KFP) / Vertex Pipelines:** reproducible steps and their execution inputs/outputs. The pipeline component should declare model, dataset, metrics, and report artifacts instead of relying on hidden local files.
- **Vertex ML Metadata:** cloud-side lineage of pipeline executions, datasets, models, and derived outputs.
- **MLflow Tracking:** comparable experiment runs, canonical metrics, tags/parameters, evaluation artifacts, and readable experiment history.
- **Vertex Model Registry:** the immutable version selected for Vertex deployment, with small labels and links back to the MLflow run and artifact digest.
- **Repository:** source code, metric protocol, pipeline definitions, lockfiles, model-card template, and small synthetic fixtures. Large model weights and sensitive/ephemeral artifacts stay in configured artifact stores.

Use one stable crosswalk rather than pretending these systems are automatically the same registry. A local MLflow server is suitable for this course-scale project; before team-wide service, decide a shared database backend, artifact storage, authentication, backup, retention, and access controls. The current local SQLite store is not a team system of record.

## 8. Can we enrich the existing models without training again?

**Yes, for metadata and for metrics reproducible from retained artifacts.** Adding tags, notes, model-card files, registry labels, lineage links, charts, and an evaluation of already-saved predictions does not change weights and does not require training. Rebuilding a chart from a saved loss history also does not require training.

| Desired addition | Retraining needed? | Evidence needed |
|---|---:|---|
| Model tags, model card, version crosswalk | No | Known facts; mark unavailable facts `unknown` |
| Logged final metrics from existing reports/predictions | No | Prediction export, exact frozen split, scorer/protocol version |
| Field/routing confusion matrices from old predictions | No | Same prediction export and matching labels |
| Loss curve artifact from `log_history.json` | No | Existing history JSON |
| Loss values as MLflow step metrics | No | Existing history JSON with step/value records; import as a separate historical tracking event if original run cannot be safely amended |
| Vertex job/task lineage | No | Existing resource URI or a verifiable local export manifest |
| Training config, exact package versions, commit, machine utilization | No, but possibly unavailable | Original Vertex task metadata, logs, lockfile/image digest; otherwise `unknown` |
| New model predictions on a split | No training, but inference/evaluation required | Weights or old outputs, budget/permission, frozen split and protocol |
| A test comparison for B3 | No training | B3 test predictions plus verifiable split and job provenance; one-time scoring after the comparison plan is frozen |
| New checkpoints/weights or changed model quality | Yes | New training run and new immutable model version |

Our current files already include D's training `log_history.json`, a B3 validation export, and several models' prediction exports. MLflow import code already attaches the loss JSON to the D validation run, but stepwise loss metrics and a curated loss chart still need to be added. Historical provenance must be explicit: a reconstructed MLflow record is a **historical import**, not an original live-tracked run.

## 9. Implementation order for this repository

1. Freeze this metric/tagging contract and version it alongside the scorer.
2. Add a model-card JSON/YAML template and a manifest validator; validate required fields and allow `unknown` for unrecoverable history.
3. Extend evaluation artifacts with routing matrices, per-field confusion summaries, urgency counts, bootstrap intervals, and error buckets. Keep output privacy-filtered and dataset-bound.
4. Add a historical loss-history importer that records stepwise `train_loss` / `eval_loss` plus the original JSON and a deterministic chart, with a distinct idempotency key and provenance.
5. Synchronize existing Vertex run manifests and link the registered Vertex version to the source MLflow run using immutable IDs and hashes.
6. Integrate logging into future KFP components: parameters and artifacts in KFP/Vertex ML Metadata; corresponding MLflow parent/child runs with the same job/task IDs. The pipeline should emit evaluation summaries and reports as declared outputs.
7. Build and visually review the MLflow-driven comparison notebook/dashboard. Refresh historical results only from the stored predictions and matching split; do not retrain for cataloguing work.
8. Only after recovery is complete, decide whether a new training run or billed inference fills a real evidence gap. Give it a new run ID, frozen protocol, budget, and teardown plan.

## References

- MLflow tracking concepts and artifacts: [MLflow Tracking](https://mlflow.org/docs/latest/tracking/)
- MLflow model versions, lineage, aliases, and tags: [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry) and [registry workflows](https://mlflow.org/docs/latest/ml/model-registry/workflow)
- Stepwise metrics, plots, and artifacts: [MLflow tracking API](https://mlflow.org/docs/latest/tracking/tracking-api) and [deep learning guide](https://mlflow.org/docs/latest/ml/getting-started/deep-learning)
- Vertex pipeline lineage: [Track pipeline artifact lineage](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/pipelines/lineage)
- Vertex model labels: [Apply model labels](https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/model-registry/model-labels)
