# 02 — Investment memo (one page)

**Recommendation:** **CONDITIONAL GO, in two stages.** Ship now the rules-only ticket-to-transaction attach with routing on structured fields (stage 1). Build the fine-tuned router and the drafter (stage 2) only if the S4 gold-set experiment clears three bars: the fine-tuned router beats the prompted model, total time saved reaches about 13 % of handling time, and incremental serious errors stay at or below 0.1 % of tickets.

> Line one is the decision. Everything below is evidence for that line. Same base case as `02_sizing.xlsx`; the company, scale and constraint come from the frozen brief in the README.

| €/year, year 1 | Pessimistic | Base | Optimistic | Expected value |
|---|---|---|---|---|
| Net annual value | −86,106 | +91,992 | +379,588 | **+96,082** |
| Probability | 0.30 | 0.50 | 0.20 | — |
| Do-nothing (value of the current process improving on its own) | 43,200 | 77,490 | 151,200 | 77,490 (the sheet compares with Base) |
| Next-best project: rules-only attach and structured routing, no AI (the hurdle) | 3,880 | 78,486 | 192,728 | 78,486 |

Steady state (Q4 adoption held for a full year, base): **+186,787 a year**. Year 1 carries the ramp-up.

## 1. How much?
**Bottom-up, base case, year 1.**
- **Volume and time saved:** 30,750 tickets a month on average over the year. The copilot saves 14.5 % of handling time at full adoption: 5.4 % from routing (15 % of time × 55 % of tickets routed automatically × 65 % cut) and 9.1 % from drafting (45 % of time × 22 % cut × 92 % of tickets correctly routed). Adoption averages 44 % over the year (15 % in Q1 to 70 % in Q4).
- **Value:** that is 23,361 ticket-equivalents at €7 of agent-time each, **€163.5k gross**. Hand-overs avoided add **€30.4k** (misrouted tickets fall from 1 in 7 to 8 % on handled tickets, at €3 of queue delay each).
- **Costs:** wrong replies **−€34.5k** (incremental, priced against today's human error rate), tokens and retries −€1.5k, fixed costs **−€66k** (integration €20k amortised, evaluation €10k, quality owner €18k, monitoring €12k, re-evaluation €6k). Net **+€92k**.

**Where the numbers come from.**
- **Given by the scenario** (treated as the company's logs, as the course template says): 1,500 merchants, ~30,000 tickets, the 15 % and 45 % time slices, 1 ticket in 7 misrouted, the data constraint.
- **Analogies:**
  - €5–15 per human ticket and €0.02–0.20 per AI conversation (S2 slides).
  - About −13 % time per issue (Brynjolfsson, Li & Raymond, QJE 2025).
  - $128 per chargeback (Mastercard 2025).
  - A scale-to-zero cloud service at near-zero cost (our Museum Guide demo on Cloud Run).
- **Guesses to test:** everything else, each with its test in the sizing. The one that matters: **total time saved**, tested in S4 and measured in the S6 A/B.

## 2. How sure?
**Scenarios.** Weighted 30 / 50 / 20, the expected value is **+€96k**. The pessimistic case is a slow rollout with higher error rates and loses **€86k**; the optimistic case gains **€380k**.

**Flip points (base case, varying total time saved).**

| Total time saved | 10 % | 15 % | 20 % | 25 % | 30 % |
|---|---|---|---|---|---|
| Net value, year 1 | +€41k | +€98k | +€154k | +€211k | +€267k |

- The base case breaks even at about **6 % time saved** (hand reading of the table).
- It beats the next-best project and do-nothing from about **13 %**. The base case is 14.5 %, so the margin over the hurdle is thin, and S4 and S6 are what decide.
- The decision does not depend on the cost of the model: hosting two models in our own cloud with scale-to-zero costs a few thousand euros a year.

**What the S4 prototype tests.**
- **Hypothesis 1 (router):** the fine-tuned model beats rules and classical ML, and beats the prompted model by a margin fixed before the run.
- **Hypotheses 2 and 4:** urgent tickets stay out of the wrong desk; seeded wrong readings are caught by the support agent.
- **Time saved:** measured on a sample, then in the S6 A/B.

## 3. What if we're wrong?
**Cost lines that dominate.** Not the model. Integration (€20k a year, amortised), the quality owner (€18k) and monitoring (€12k) dominate; hosting and tokens are under €5k a year.

**Cost of error, priced as a tail.**
- **Basis:** a wrong reading that a support agent does not catch costs about €150 on a payment question, €400 on a dispute and €300 on a technical or compliance question (guesses).
- **At the rates assumed:** 0.05–0.12 % of tickets with an uncaught serious error, incremental to today, costs **€34.5k in year 1**, or **€45k** in the pessimistic case.
- **Safety nets:** `UNDEFINED` goes to a human; critical tickets (amount, urgency, dispute or compliance, deadline) need a human to confirm the desk before any draft; a misrouted ticket is rerouted and redrafted once, then goes to triage.

**Governance line.** A wrong status, amount or deadline told to a merchant on a dispute or compliance question, and an urgent ticket left in the wrong desk, are **legal and reputational** risks: the merchant acts on it and can complain to the regulator. Owner: **Head of Compliance**. The Head of Support owns the routing rules, the thresholds and the switch back to "reading only" (`governance.md`, Session 2).

## 4. Compared to what?
**Do-nothing is not zero.** Agents get about 3 % faster a year, worth **€77k** at today's volume and cost. Volume also grows with the merchant base, so the cost of reading, routing, looking up and writing grows with it (problem statement, §7).

**Next-best project.** The same engineers can ship the rules-only attach: each ticket gets the merchant's recent transactions, open disputes and last tickets by merchant ID, date and amount, and structured fields route the easy tickets.
- **Value:** about **€78k net a year** in the base case (6 % of handling time saved, 70 % adoption, €30k a year to run). To test it, observe 20 tickets.
- **Nothing is lost:** it is also the copilot's lookup layer, so stage 2 starts from it. The copilot is an increment on top of stage 1, which is why we recommend both in sequence rather than one against the other.

**Does the pessimistic case clear the hurdle?** No: −€86k against €78k. That is why the decision is conditional.

## 5. Build, buy or orchestrate?
**We orchestrate**, because the edge is our ledger, dispute history and desk rules, and tickets must stay in our cloud (the data constraint): managed components in our own cloud (model hosting, retrieval) around our routing table and review screen. Weighted scores from the `Build or buy` tab: **Build 3.54 · Buy 3.00 · Orchestrate 3.66**. Build and Orchestrate are within the template's 0.3 margin, so the data constraint and the run burden decide.

**What would change our mind:** a vendor copilot that reads our ledger, runs inside our cloud tenancy and does not train on our data. We would buy it: about €21k a year for 38 seats at ~€45 a month, roughly €17k a year less than our build-specific costs.

*Sources:*
- `01_problem_statement.md` and `02_sizing.xlsx` (Inputs, Flow and Read options tabs).
- S2 slides: cost per human ticket, cost per AI conversation, do-nothing.
- Brynjolfsson, Li & Raymond, "Generative AI at Work", *QJE* 140(2), 2025.
- Mastercard, "What's the true cost of a chargeback in 2025?".
- Cloud Run per-second pricing and our Museum Guide deployment notes (`deploy/README.md`, free tier).
- Job postings for customer advisers in France (France Travail, Michael Page, 2026) — to re-source on the day.
