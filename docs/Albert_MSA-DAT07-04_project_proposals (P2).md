**ALBERT SCHOOL · MSA-DAT07-04 · M2-INTER-1 & 2**

**Mutualised project — “LLMOps & Agentic Systems”**

AI Product track — eight project proposals, and how to bring your own

**Context (fixed by the syllabus).** You are the AI product team at a B2B SaaS company building an AI-powered customer-support agent. This document gives you eight concrete starting points, each with a different vertical, a different level of autonomy and a different kind of risk. You may pick one, adapt it, or propose your own (section 3). The project is shared with MSA-DAT07-03 (Agentic Workflows): same team, same agent, two deliverables — they build and test it, you decide whether and how it should ship.

**What this course grades (50 % of the course).** Git deliverable 40 % · group oral defence 40 % · individual deliberation 10 % · peer review 10 %. The other 50 % is a 90-minute written exam without AI.

**Your deliverables (from the syllabus)**

1.  Decode the AI architecture — components, workflow patterns, trust level, tools, human-in-the-loop points.

2.  Define the expected effect on three business metrics, quantified.

3.  Design an A/B evaluation protocol with a sample-size calculation.

4.  Identify adverse effects and monitoring strategies.

5.  Write the full technical specification and the AI product brief, including a rollback plan.

# 1. The eight proposals at a glance

Each proposal states the company, the pain, the agent's job, a target trust level (L1 Assist → L5 Autonomous), a suggested primary metric, the trap specific to the case, and one thing that makes it innovative rather than “another chatbot”. Numbers are plausible orders of magnitude for a mid-size SaaS — you will re-derive them in your sizing (S2).

|  | **Vertical** | **Agent's job** | **Trust level** | **The trap** |
|----|----|----|----|----|
| **P2** | B2B payments fintech | Agent-assist copilot (drafts, never sends) | L2 | Wrong transaction match |

**Trust levels:** L1 suggests · L2 drafts, a human approves every reply · L3 acts on a scope, with sampling · L4 acts autonomously under a threshold · L5 fully autonomous.

# 2. The proposals in detail

## P2 · Agent-assist copilot for a fintech (B2B payments)

| **Company** | 800 merchant customers, 12,000 tickets / month, a high share of “where is my money” and dispute questions. |
|----|----|
| **Pain** | Agents spend 40 % of handling time reading transaction history and past tickets before replying. |
| **Agent's job** | No customer-facing autonomy. Pre-reads the account, drafts the reply with links to the transactions, flags regulatory constraints (PSD2, KYC). The human edits and sends. |
| **Trust level** | L2 throughout. |
| **Primary metric** | Average handling time per ticket at constant quality (QA score). |
| **The trap** | The copilot is only as good as the data it reads; a wrong transaction match is worse than no draft. Measuring “time saved” with a self-reported survey is not evidence. |
| **Innovative angle** | An evaluator model scores each draft for groundedness before the agent sees it; drafts under threshold are shown as “context only”, not as a reply. Your A/B compares copilot-on vs copilot-off per agent, not per ticket. |

# 3. How to choose

Run your candidate through the four agent-selection criteria:

- **High frequency —** is the workflow triggered daily or hourly? (P3 is the exception; you will need to justify it.)

- **Bounded decision space —** can you list the agent's tools and outcomes on one slide?

- **Measurable success —** can you say in one sentence whether the agent succeeded on a given ticket?

- **Recoverable failure —** if the agent is wrong, is the damage bounded and reversible? (P4 and P7 are deliberately borderline; they make good projects only if your rollback plan is serious.)

Then check the fit with the other course: the agent you decide on here is the agent your team builds in MSA-DAT07-03. Do not pick an ambition the build cannot follow.

# 4. Bring your own project

You may replace the proposals with your own idea — including one you are working on with Albert Native or elsewhere — as long as it stays within the syllabus context (B2B SaaS, customer-support agent) and passes the checklist below. Submit a half-page pitch on Git (00_pitch.md in the repository template) before Session 3 — Friday 16 October; it is validated, or sent back with changes, at the start of Session 3.

**Acceptance checklist**

1.  A named company type, a ticket volume and a support-team size — invented but plausible.

2.  A pain expressed as a cost (hours, euros, SLA penalties, churn), not as “customers are unhappy”.

3.  A do-nothing baseline: what happens if nobody builds anything.

4.  One agent job in one sentence: “When \[trigger\], the agent \[does\], producing \[outcome\].”

5.  A trust level per step of the journey, with at least one step below L4.

6.  One thing the agent must never do — this becomes your first guardrail.

7.  A reason it is a product decision and not only an engineering exercise — someone has to decide whether to ship it.

**Ideas that are usually refused:** an “AI that answers everything”, a personal assistant for the founder, a B2C consumer chatbot, or a project whose only metric is “user satisfaction”.

# 5. Repository template (mandatory structure)

Every session ends with a commit. Every member must author commits in at least four of the numbered files: the individual deliberation (10 %) asks you about a commit you signed. governance.md is updated at every session and one oral question is drawn from it. Tag the final version v1.0 before the first oral of your cohort.

| **File / folder** | **Session** | **What it contains** |
|----|----|----|
| README.md | S1 | team, chosen project, how to run the prototype |
| 01_problem_statement.md | S1 | problem statement, problem tree, press release + “would have to be true”, persona & journeys, stakeholder map |
| 02_sizing.xlsx + 02_investment_memo.md | S2 | sizing sheet (low / base / high, a source per input) and the go / no-go / conditional-go memo |
| 03_product_brief.md | S3 | one-page brief v1 → v2 (what the users changed), MoSCoW in/out of scope, AI Lean Canvas, prototype link |
| 04_architecture.md | S4 | decoded architecture: components, patterns, trust level per step, tools, HITL points, override switch |
| 05_metrics.md | S5 | evaluation stack, stop criterion, three business metrics with expected effects, metric hierarchy, segments |
| 06_ab_protocol.md | S6 | pre-registered protocol: hypothesis, unit of randomisation, MDE, sample size, duration, segments, stopping rule |
| 07_operations.md | S7 | adverse effects, monitoring layers, drift triggers, retraining, rollback plan |
| 08_launch_memo.md | S8 | the recommendation you will defend |
| governance.md | S1 → | six FAQ answers in S1, one line added per session (data, HITL, segments, owner & rollback) |
| spec.md · product_brief.md | final | full technical specification and AI product brief, with the rollback plan |
| /prototype | S4 | Streamlit or FastAPI prototype |
| /evals | S4 → | eval-set (tickets_v0 → v1), eval reports, sample-size notebook, monitoring notebook |

# 6. The final oral: pitch your project — 15 minutes (10 + 5)

An investor-style pitch in the spirit of Airbnb’s 2009 seed deck — the problem first, then the numbers. Ten beats, one slide each, each one built in a session:

1.  Problem — who suffers, and what it costs today (S1).

2.  Solution — your agent in one sentence, and its trust levels (S1, S3).

3.  Validation — what users said about your prototype (S3).

4.  Market — TAM, bottom-up sizing, net value per unit (S2).

5.  Product — a live demo, and the architecture decoded (S4).

6.  Business case — expected value vs do-nothing and the hurdle (S2).

7.  Alternatives — could the company buy a vendor product? another project? (S2).

8.  Proof — three business metrics, the A/B protocol and its sample size (S5, S6).

9.  Risks — adverse effects, monitoring, the rollback criterion (S7).

10. The ask — go / no-go / conditional go, the launch plan, who did what (S8).

It is not a technical demo: the five deliverables live in your repository, and the pitch is where you defend them. The Q&A targets what is not on the slides: the assumption behind your deflection rate, why this unit of randomisation, what happens on day one if the model provider changes the model version.
