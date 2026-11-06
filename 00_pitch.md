# 00 — Keelpay Pitch

NAVY adapts the P2 scenario into one shared AI Product and LLMOps project. **Keelpay**, a fictional B2B fintech, serves about **2,500 merchants** and receives **36,000 monthly tickets**, in French and English. Scenario data allocate **15%** of active handling time to reading/assignment and **45%** to lookup/drafting; **one ticket in seven** is initially assigned to the wrong desk.

At **10 minutes per ticket** and **130 productive hours per agent/month** (assumptions), volume represents about **6,000 hours and 46 agents**. The two painful slices represent 3,600 hours of capacity, not realized cash savings. Calculations, costs, and alternatives are in [02_sizing.xlsx](02_sizing.xlsx).

**Today**, people read, assign, search, and reply. Experience and macros may improve the process without this project; volume may also grow. The non-AI alternative is deterministic attachment of merchant and transaction context.

**Copilot flow:** the Qualifier Model extracts seven fields; the Python Routing Node selects the desk and allowed steps; Lookup Node / Retrieval Node / Drafter Model prepare a sourced reply or clarification. The Support Agent resolves necessary ambiguities, reviews, and sends.

**Control:** bounded L3 routing, human desk correction (Re-router), L2 reply, human send. Urgency raises attention without blocking draft preparation. No autonomous sending or ledger writes. Missing information blocks only decisions that depend on it.

**Decision:** GO to build/evaluate the demo; pilot remains conditional on Support and Compliance review after active-time, constant-QA, and residual-risk measurement. The Qualifier Model benchmark does not prove this gain. The key failure is a request that appears handled but has the wrong desk, payment, or urgency response.

The demo uses only non-critical synthetic data and may call an external Drafter Model for that demo. Fictional production keeps models/data/traces in Keelpay cloud. See [README](README.md), [governance](governance.md), and [product brief](03_product_brief.md).
