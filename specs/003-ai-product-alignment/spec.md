# Feature Specification: AI Product Alignment
**Feature**: 003-ai-product-alignment<br>
**Created**: 2026-11-03<br>
**Status**: In progress; see tasks and validation for accurate completion state<br>
**Input**: Audit the merged course project, settle product choices/governance, then organize future work with Spec Kit before building the live demo.

## User scenarios and testing

### User Story 1 — Defend one recommendation (P1)
As a NAVY team member, I can explain the problem, product, alternatives, and pilot decision without contradictions between deliverables.

**Why P1:** all further work depends on shared scope and assumptions.<br>
**Independent test:** compare pitch, README, brief, canvas, and memo against the decision matrix.

Acceptance scenarios:
1. Given confirmed choices, when a reader compares deliverables, then the Qualifier Model qualifies, deterministic rules assign, a Support Agent approves every send, and ambiguity blocks only dependent steps.
2. Given the demo scope, when the three spaces and priorities are described, then FIFO and wait are MUST, advanced urgency is SHOULD, and no production guarantee is implied.
3. Given the recommendation, when read, then demo GO, conditional pilot, and production expansion are distinct.

### User Story 2 — Separate evidence, assumptions, and targets (P1)
As an evaluator, I can trace each claim to its source and scope.

**Why P1:** fabricated evidence or mixed metrics undermine a product recommendation even if model work is technically sound.<br>
**Independent test:** check research, data provenance, metrics, and cited sensitivities.

Acceptance scenarios:
1. Given provisional user-research material, when research/brief are aligned, then no invented quote or timing is presented as evidence, and actual user validation remains an open activity.
2. Given historical model results, when summarized, then they remain intact and are not presented as full-product validation.
3. Given revised sizing, when memo and workbook are compared, then figures reconcile, scenarios are feasible, and amortized value is distinguished from cash.

### User Story 3 — Prepare future deliverables and build (P2)
As a team, I know which deliverables need work, which observations to collect, and which feature to prepare next.

**Why P2:** converting decisions into verifiable work prevents version drift.<br>
**Independent test:** trace one course requirement to its deliverable, source, status, and task.

Acceptance scenarios:
1. Given supplied assignments, when the matrix is reviewed, then each requirement is satisfied or explicitly open with a next action.
2. Given the future portfolio, when a developer reads it, then dependencies/entry criteria are explicit and an unplanned feature does not look implementation-ready.

## Edge cases

- A demo limit must not be described as a production risk reduction.
- A correctly copied figure may still depend on an unvalidated assumption.
- LLMOps requirements confirmed verbally by Vincent are distinguished from written instructor requirements.
- Historical mock-up features may retain old rules and must be labelled historical.
- Actual user research cannot be replaced by generated reports.
- Future sessions without supplied briefs remain planned without invented requirements.

## Requirements

### Functional requirements

- **FR-001**: Current deliverables MUST use Keelpay and canonical terminology: Qualifier Model, Routing Node, desk, Human Qualification, Human Review, Support Agent.
- **FR-002**: Deliverables MUST distinguish benchmark, synthetic demo, and fictional production.
- **FR-003**: Governance MUST assign rules/quality to Support, business exposure to Compliance, and implementation/measurement to NAVY, with manual recovery and separate disablement.
- **FR-004**: Research deliverables MUST not present unsupported user findings as evidence and MUST describe a protocol for three conversations and two declared real/role-play participants.
- **FR-005**: Historical results MUST remain preserved and the missing prompted-model comparison MUST be stated.
- **FR-006**: Memo/workbook MUST share a base and feasible sensitivities; demo/production costs and cash/amortization MUST be distinguished.
- **FR-007**: Brief MUST have at most four MUSTs and at least five WON'Ts; RICE/process MUST align to those capabilities.
- **FR-008**: The twenty S3 cases MUST respect taxonomy and clearly state oracle/provenance/required context.
- **FR-009**: Success criteria MUST separate business value, quality, safety, UX, and component measures; a small set cannot certify rare risk.
- **FR-010**: Each available course requirement MUST point to a deliverable, source, and observable status.
- **FR-011**: Unimplemented capabilities and proposed decisions MUST remain explicitly identified.
- **FR-012**: Corrections MUST preserve original assignment instructions, existing worktree changes, and mock-up history.
- **FR-013**: Future plans MUST follow AI Product trade-offs and specify verifiable outcomes/dependencies.

### Key entities

- Product decision: origin, status, demo/production scope, affected deliverables.
- Claim: content, source, fictional input/assumption/measurement/target status.
- Course requirement: source document, known deadline, deliverable, criterion, status.
- Evidence: artifact, population, method, date, limitations.
- Deliverable: role, version, sources, and required corrections.

## Success criteria

- **SC-001**: Eight structural decisions (model role, rules, ambiguity, human control, urgency, FIFO, external services, evidence) have no unreported conflict across current deliverables.
- **SC-002**: No unsupported interview, user result, or deployment is used as real evidence.
- **SC-003**: Decision figures in the memo reconcile with the revised workbook within stated rounding.
- **SC-004**: Each S3 case has a verifiable expectation, provenance, and required context available.
- **SC-005**: Every requirement in supplied Assignments 1–3 has a status and response/action link.
- **SC-006**: A reader can identify current recommendation, pilot conditions, and missing evidence.

## Assumptions

- Vincent's confirmed product scope governs this authorized work; it is not retrospective instructor/team ratification.
- Original Assignments 1–3 remain pedagogical references; future sessions are covered when their briefs are available.
- This feature corrects deliverables; it does not deploy a product or perform human testing on participants' behalf.
- Open implementation/business parameters remain explicit until assigned and validated.
