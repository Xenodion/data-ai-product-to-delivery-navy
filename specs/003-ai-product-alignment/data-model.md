# Documentary Traceability Model

This model organizes document registers; it does not introduce an application database.

| Entity | Required fields | Rules |
|---|---|---|
| Decision | ID, topic, origin, status, scope, affected deliverables | Status confirmed/proposed/open; scope benchmark/demo/production; never fabricate team ratification |
| Claim | content, type, source, population or assumptions, date/version | Type fictional input/assumption/measurement/target/not implemented; measurement requires inspectable evidence |
| Requirement | ID, source instruction, deliverable, criterion, status, next action | Status met/partial/todo/justified N/A; protocol does not satisfy actual observation |
| Evidence | artifact, method, actual author or declared role, population, date, limitations | Human quote requires actually collected notes; synthetic does not mean human-annotated |
| Deliverable | path, purpose, version, sources, status | Course deliverable is not replaced by a build spec; history is labelled |

Relationships: a decision can affect several deliverables; a requirement links to at least one deliverable or open action; a measured claim links to evidence; evidence supports claims only within its population/method limits.

Status transition: an assumption becomes a measurement only after observation and evidence are added. A document correction closes a consistency gap, not automatically a validation requirement.
