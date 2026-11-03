# 03 — Keelpay Product Brief

**NAVY · 3 November 2026 · aligned after trade-offs.** Summary; see the [process, RICE, and scope appendix](docs/design/product-brief-annex.md).

**User and problem.** Support Agents handle merchant requests in French and English. Reading/assignment and lookup/drafting consume 60% of active time in the scenario. One in seven requests initially reaches the wrong desk. A dangerous failure is a reply prepared against the wrong payment or an urgent ticket that appears to be handled.

**Proposal.** The Qualifier Model extracts seven fields; the Python Routing Node selects a desk and next steps; Lookup Node / Retrieval Node / Drafter Model prepare context and a sourced reply or clarification. The Support Agent qualifies only what is necessary, then reviews and explicitly sends every reply. Bounded L3 routing; L2 reply; no autonomous send or ledger write.

**Four MUSTs.** (1) Qualify and assign, with targeted human resolution. (2) Prepare a grounded reply with merchant context, sources, and ambiguity handling. (3) Enable human decisions: qualification, final review, editing, gates, and history. (4) Evaluate and observe: reference cases, metrics, traces, and recovery. RICE/MoSCoW are in the appendix.

**Target surface.** Three tabs: Overview, Qualification & Routing, Replies to Review. Queues show wait time and oldest-first order. A click on a human node opens an eligible task; events and counts come from the backend. Minimal Overview is required for the demo; advanced urgency handling and multi-agent remain SHOULD.

**Decision rules.** Undecidable intent → qualification; unidentified payment → selection or clarification before payment-specific claims; unknown sentiment → neutral tone. Priority does not require pre-draft confirmation. A desk correction permits one new preparation; the second reroute goes to manual triage. If a draft is sent unchanged, the Support Agent confirms facts and sources; cosmetic editing is not required.

**Success to test.** Measure active time on comparable tasks, net of corrections, at constant QA, and compare with the economic hurdle in the corrected sizing. Track first-pass desk accuracy, automatic-assignment coverage, urgent detection/handling, and serious post-review errors separately. The economic threshold varies with assumptions; 90% desk accuracy and 50% automatic assignment are not substitutes. Twenty S3 cases check the contract; a roughly 200-case exercise is exploratory for rare risks.

**Decision and evidence.** GO for demo construction/evaluation; conditional Keelpay pilot. D-q4 is the measured candidate; prompted-model comparison and complete-product measurement remain. The design to evaluate separates qualification from reply review, shows payment candidates and sources, and makes waiting and live flow visible ([research plan](03_user_research.md)).

**Data and constraints.** Synthetic benchmark is separate from synthetic ledger/KB fixtures; split and provenance are documented. External Drafter Model and traces are allowed only on non-critical synthetic demo data; fictional production remains in Keelpay cloud. See [governance](governance.md).

**Still open.** Priority signals/deadlines, QA rubric, retention, rare-risk protocol, and technical choices for implementation plans. **Out of scope:** autonomous sending, financial writes, automatic intent splitting, external voice/chat, regulatory advice/decisions, and real data sent to external APIs.
