# Claims Register

| Claim | Type | Source | Scope / limitation | Status |
|---|---|---|---|---|
| About 2,500 merchants and 36,000 monthly tickets | Fictional scenario input | Root README and assignment proposal P2 adaptation | Starting scenario, not observed company data | Current |
| 15% reading/assignment, 45% lookup/drafting, 40% other active time | Fictional scenario input | Root README | Scenario slices; do not turn into measured minutes without the 10-minute assumption | Current |
| One in seven tickets initially misassigned | Fictional scenario input | Root README / sizing | 14.286%; about 5,143/month at 36,000 tickets | Current |
| 10 min/ticket, 46 agents, 130 productive hours/month | Assumption | Sizing Inputs | Capacity illustration, not team headcount evidence | Unvalidated |
| Dataset has 1,922 train, 293 validation, 610 natural test, 380 trap test | Measured artifact count | Nested dataset files and audit reproduction | Accepted synthetic records; quarantines excluded | Reproduced |
| D-q4 has 4/610 silent errors and 1/167 urgent wrong desk | Historical model/scorer measurement | LLMOps predictions and `audit/reproduce.cjs` | Component scorer only; not full Routing Node or post-review harm | Reproduced |
| D-q4 is better than the prompted alternative | Unsupported claim | No prompted comparator result found | Must not be stated as a result | Not established |
| Full-flow demo will use Cloud Run, static hosting, CPU Qualifier Model, external synthetic-only Drafter Model, and Langfuse | Target / oral user-confirmed scope | Conversation decisions, `spec.md`, `04_architecture.md` | Hosting/runtime and successful deployment still to verify | Planned |
| External Drafter Model/Langfuse receive only non-critical synthetic demo data | Confirmed demo boundary | User decision and governance | Does not alter fictional production boundary | Agreed design constraint |
| Every reply receives human review; no autonomous send or ledger write | Product decision | Root `spec.md`, governance, user confirmation | Demo send is simulated; no real financial operation | Agreed target |
| Unknown intent requires Human Qualification; missing payment blocks payment claims only; unknown sentiment does not block routing | Product decision | Root `spec.md`, workflow | Implement in Routing Node; model schema unchanged | Agreed target |
| Oldest-first wait-ordered queue and clickable Overview nodes | Demo requirement | User confirmation and workflow | MUST; queue state must come from backend | Agreed target |
| Advanced urgent queue and multi-agent behavior | Prioritization | User discussion / product appendix | SHOULD for demo; not a production risk approval | Scoped |
| 20 S3 cases are gold evaluation data | Unsupported claim | `evals/eval_set_v0.csv` | Authored synthetic cases, source fixtures absent, no independent oracle review | Not established |
| User interviews/usability results are measured | Unsupported claim | No actual notes supplied during this audit | Design feedback may guide scope; actual observations/timings remain unmeasured | Not established |
| Base scenario net value €194,298; expected value €214,308 | Workbook calculation based on assumptions | Root `02_sizing.xlsx`; verified export | Assumption-based output, not a forecast | Reconciled to memo |
| Active-time threshold to beat base next-best is 13.32% | Workbook sensitivity based on assumptions | Root `02_sizing.xlsx`; verified export | Changes with adoption/cost/error assumptions; not universal threshold | Reconciled to memo |
| Product saves approximately 20.262% active time | Model assumption | Workbook Flow base assumptions | No full-flow task measurement exists | Unvalidated |
