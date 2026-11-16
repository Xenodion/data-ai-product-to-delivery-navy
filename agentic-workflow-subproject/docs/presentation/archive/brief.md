# Brief for the storyline of the final presentation

This brief is shared by every author of a storyline version. It states the constraints, not the content: each author reads the repository and decides what to show.

## The exam (as given by the team, verbatim, French)

> Les choses obligatoires sont : un LLM fine-tuné sur Kubeflow avec metrics, un endpoint déployé GCP avec registry, une interface pour utiliser le flow, un monitoring avec Langfuse.
> Les choses qui vont améliorer la note : une explication détaillée de la R&D de fine-tuning, des garde-fous qu'on a mis en place, etc.
> Le tout présenté sur des slides avec des charts et des screenshots, 15 min : ~8-10 min de présentation, 5-7 min de Q&A.

The course is "Agentic Workflows & LLMOps" (Albert School, M2). The same project is shared with the course "Data & AI Product: From Diagnosis to Delivery" (problem framing, sizing, investment memo, metrics, governance). The team has 4 members (root `README.md`).

## Constraints set by the team

**Order of the talk (fixed):**
1. Cover, then an index slide with the topics and the team names. A progress bar on every following slide shows where we are.
2. **Context**, for someone who knows absolutely nothing about the project: who asked us what, which company (fictional scenario: check the real one in the repo), which users, what the problem is.
3. **How we framed the need**: key metrics and go/no-go gates, so that we did not build a useless "buzz" product. This comes from the AI Product course work and must be condensed (1-2 slides).
4. **The complete workflow we built.**
5. **The ML work**: the fine-tuned model (its input and output formats, how we fine-tuned it: dataset, epochs, settings, process, not only scores), the models compared and the trade-off charts used to choose, the results.
6. **Guardrails** (wherever they fit best).
7. **Deployment** (the subject of the course): registry, endpoint on GCP.
8. **Monitoring** with Langfuse.
9. **Conclusion**: recap of the method, the economics of the project (what we expect it to earn), and the gates for what comes next: we stop at a deployed MVP, so the steps toward putting it into service are a plus.
10. **Demo** (video of the app) at the very end.
11. Hidden appendix slides for the Q&A.

**Style (strict):**
- Present the work plainly. No drama, no grandiloquence, no slogans, no social-media "buzz" tone. A metric choice is an important point, not the heart of the talk.
- Very little text: short, synthetic sentences that explain. No title / subtitle / sub-subtitle stacks.
- No KPI tiles, no number-dropping: a number appears only where it explains something, inside a sentence or a chart.
- Every content slide carries one very explicit chart or screenshot. If the visual needs a paragraph to be understood, it is the wrong visual.
- Short, airy divider slides introduce each section (passed in 2-3 s) instead of overloading content slides.
- About 12-14 content slides for ~9 min of talk (plus dividers, cover, index, demo).

**The work must show both hard skills and governance**, concisely, by choosing very carefully what is shown and how.

## Facts to check yourself, not to assume

- What is actually built and deployed today (code in `agentic-workflow-subproject/flow/`, `frontend/`, `flow/deploy/`; current state notes in `docs/roadmap.md`, `specs/roadmap.md`, `README.md`). Do not claim anything is deployed or built unless the repo shows it; list gaps instead.
- Every number you put on a slide must come from a file in the repo; cite the path.

## Where to look (pointers only)

- Root: `README.md`, `00_pitch.md`, `01_problem_statement.md`, `02_investment_memo.md`, `03_product_brief.md`, `03_user_research.md`, `04_architecture.md`, `05_metrics.md`, `governance.md`, `spec.md`, `evals/`, `prototype/`, `docs/project/` (course briefs, .docx).
- Sub-project `agentic-workflow-subproject/`: `README.md`, `initial_brief.md`, `docs/` (methodology, scoring protocol, baseline results, compact variants, mlops tracking, roadmap, design/flow-v2/), `docs/results/` (predictions, loss history, timings), `ml/qualifier/notebooks/` (journals 01-05), `ml/qualifier/src/` (pipelines, components), `ml/confidence/`, `flow/`, `frontend/src/`, `specs/`.
- Open GitHub issues: `gh issue list`.

## Output format

Write one Markdown file at the path you are given. English. Structure:

1. **Storyline in 5 lines**: what the audience should understand, in order.
2. **Slide by slide**, for each slide: section · purpose (what the jury must retain) · the text on the slide (the exact short sentence(s)) · the visual (exactly what it shows, and the data source path) · what the speaker says (2-4 short lines) · time · material status (exists / chart to make / screenshot to capture).
3. **What we deliberately do not show, and why** (selection matters as much as content).
4. **Appendix slides and the questions to prepare.**
5. **Gaps** between the course requirements and the current state of the repo, with what must be done before the slides.
6. **Timing table** that adds up.

Do not edit any other file. Do not run git commands that change state, and nothing that bills on a cloud.
