# NAVY — Keelpay Support Copilot

**Data & AI Product: From Diagnosis to Delivery — MSA-DAT07-04** · Albert School · M2-INTER-2. Shared project with Agentic Workflows & LLMOps. Working reference: 3 November 2026.

| Team member | Git handle |
|---|---|
| Alexandre Waerniers | Xenodion |
| Vincent Lamy | Vincent-20-100 |
| Nahel Bachiri | nahelbachiri-oss |
| Yoni Mahieddine | InoyDev |

## Product and decision

When a merchant ticket arrives, the copilot qualifies it, assigns known requests through deterministic rules, retrieves authorized context, and prepares a sourced reply or clarification. A Support Agent resolves only necessary ambiguities, reviews every reply, and explicitly triggers each send. No autonomous send, refund, account unfreeze, or ledger write.

**GO to build and evaluate the demo; CONDITIONAL GO for a Keelpay pilot.** Expansion depends on end-to-end evidence at constant quality. Deterministic context attachment without AI is an alternative to test, not a delivered project.

## Shared scenario

Keelpay is a fictional B2B fintech with about 2,500 merchants in France and Belgium, 36,000 monthly tickets, mostly in French and English. Scenario inputs: reading/assignment uses 15% of active handling time; lookup/context/drafting 45%; other actions/review/send 40%. One in seven tickets first reaches the wrong desk, equal to 14.286% or about 5,143 tickets at this volume. These are fictional starting data, not observations by our team.

Ten minutes per ticket, 46 agents, costs, growth, adoption, and savings are assumptions in [the sizing workbook](02_sizing.xlsx). Active handling time excludes queue wait, which is measured separately.

The canonical names are **Qualifier Model** (seven-field extractor), **Routing Node** (deterministic Python decision), **Lookup Node**, **Retrieval Node**, **Drafter Model**, **Support Agent** (human), **Demo Injector** (Python script), and **Langfuse** (observability). See [the terminology reference](docs/design/terminology.md).

## Reference flow

Demo Injector → Qualifier Model → Routing Node → Lookup Node / Retrieval Node → Drafter Model → Support Agent review → simulated send. Human Qualification is required only when a dependent decision cannot be made. An unidentified payment may require selection or clarification; unknown sentiment does not block routing. Priority alone does not block draft preparation.

Bounded L3 assignment, assisted lookup/context, L2 reply, human send. The first desk correction triggers one re-preparation; a second reroute requires manual triage. Do not automatically split multi-intent tickets.

Three target tabs: **Overview**, **Qualification & Routing**, and **Replies to Review**. Clicking a human node opens an eligible task. Waiting time and oldest-first are MUST for the demo; advanced urgency and multi-agent are SHOULD. Overview reflects backend events; Langfuse observes processing but does not store operational queues.

## Demo and fictional production are separate

| Environment | Boundary and evidence |
|---|---|
| Benchmark | Synthetic tickets, contract, and historical Qualifier Model results; component evidence only |
| Course demo | Static front end, Cloud Run CPU backend, synthetic ledger/KB, external Drafter Model and Langfuse permitted only on non-critical synthetic data; simulated sends |
| Fictional production | Real tickets, models, and traces remain in Keelpay cloud under the scenario's internal policy; architecture, compliance, and value require validation before any pilot |

The Qualifier Model schema is [schema.py](finetuned_llm_classifier/src/dataset_build/schema.py), with semantics in [label_definitions.md](finetuned_llm_classifier/docs/label_definitions.md). All seven values are strings; an absent reference/amount/currency is empty string, ambiguity is `UNDEFINED`, and out-of-taxonomy intent/sub-intent is `OTHER`. The contract has no confidence score or `critical` urgency. `UNDEFINED` blocks only decisions that depend on that field.

## Current state and evidence

The [LLMOps sub-project](finetuned_llm_classifier/README.md) has 3,205 accepted tickets (1,922 train, 293 validation, 610 natural test, 380 traps). D-q4 has four silent errors on 610 and one wrong-desk case among 167 urgent tickets in the historical scorer. That scorer derives desk from intent; it does not yet measure the full product policy. Prompted-model comparison remains outstanding. Vertex registration is reported in the logs; no current cloud state is certified here.

The [single V0 baseline](prototype/copilot_panel/v2.html) opens without setup and simulates four cases. The earlier sketch is retained for provenance, not as a competing design. V0 is not the real-time front end; the single English-language V1 successor, Routing Node, integrated backend, three-tab experience, and demo deployment remain to be built. Ticket messages stay in their authored languages.

## Current documents

- [Pitch](00_pitch.md), [problem statement](01_problem_statement.md), [investment memo](02_investment_memo.md), [product brief](03_product_brief.md), [lean canvas](03_ai_lean_canvas.md).
- [Design feedback and agent journey](03_user_research.md), [prototypes](03_prototype_link.md), [governance](governance.md).
- [Product specification](spec.md), [architecture](04_architecture.md), [workflow and detailed UX](docs/design/copilot-workflow.md), [terminology](docs/design/terminology.md), [synthetic evaluation cases](evals/README_eval_set.md).
- [Spec Kit roadmap](specs/roadmap.md), [AI Product alignment specification](specs/003-ai-product-alignment/spec.md), [implementation tasks](specs/003-ai-product-alignment/tasks.md), [validation record](specs/003-ai-product-alignment/validation.md), and the future [Routing Node contract/cases](specs/004-routing-node/spec.md).
- [Audit](audit/2026-11-03-audit-coherence.md): dated diagnostic, distinct from the corrected current state. Original course files in `docs/` are preserved; the earlier Paylio prototype spec is archived there and does not define the Keelpay scenario.

Deliverables 05 metrics, 06 A/B, 07 operations, 08 launch, and final synthesis remain to be produced from available course instructions. Each member signs their own contributions; do not attribute nonexistent commits. The course asks for at least four numbered files per member and a final v1.0 tag before the oral presentation.

The versioned Spec Kit plans in `specs/` organize implementation; `.specify/workbench/` contains ignored local generation and review artifacts. Do not copy a scenario, contract, or policy change into one document without updating its reference and affected deliverables with the reason.
