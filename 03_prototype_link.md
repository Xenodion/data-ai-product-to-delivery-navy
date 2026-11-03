# 03 — Prototype Baseline and Demo Target

## One V0 baseline

The current local reference is the [V0 baseline](prototype/copilot_panel/v2.html). It is a clickable, in-memory interaction mock-up with synthetic payment candidates, source inspection, editing, simulated send, and undo. Its filename and historical browser report still use the earlier V2 work-item identifier; that identifier does not establish a second product version.

The earlier [prototype sketch](prototype/copilot_panel/index.html) is retained as a historical source for provenance. It is not a competing option, is not a current target, and should not be shown alongside V0 as a version choice.

The existing screenshot predates the English UI localization and is therefore not presented as a current V0 capture. Open the HTML baseline for the current interface.

The interface copy is in English; synthetic merchant messages and example replies remain in their authored language, including French. The V0 checks verify UI behavior and rendering only. They do not measure usability or product gains. V0 has no business backend, live AI, real queue, or durable state; reload resets the session. It contains a legacy pre-draft urgency gate that conflicts with current policy. Preserve it as a baseline fact; do not reuse that rule in the next build.

## One future V1

Build one successor after the complete workflow and UI/UX are reworked against [design feedback and task prompts](03_user_research.md), the [current workflow](docs/design/copilot-workflow.md), and the [product spec](spec.md). Do not make parallel successor variants. The successor becomes the single demo front end and must follow persistent backend state.

Its product flow has three distinct spaces: **Overview**, **Qualification & Routing**, and **Replies to Review**. Overview shows injected ticket events, operational counts, waiting age, priority, and ratios with periods/denominators. Clicking a human node opens the correct eligible task. The qualification space resolves only the blocking decision. The review space shows the draft, sources, history, attention items, editing, and clear send gates. New arrivals cannot replace the current task or erase edits.

The V1 front end will continue using English interface copy, while incoming synthetic merchant messages remain in their authored languages. No translated ticket fixtures are needed. Every queue/action/animation comes from backend state. The Python Demo Injector, Qualifier Model, deterministic Routing Node, Lookup Node, Retrieval Node, Drafter Model, Support Agent actions, and Langfuse are the target flow; the external Drafter Model and external traces are allowed only for non-critical synthetic demo data. Sends are simulated and human-triggered.

## Version rule

There is one reviewable baseline (V0) and one planned successor (V1). The predecessor code and earlier work-item records may remain in the repository for provenance, but must not be presented as alternate product designs. Once the new workflow is approved, update one canonical interface and its acceptance record; do not create a third parallel mock-up.
