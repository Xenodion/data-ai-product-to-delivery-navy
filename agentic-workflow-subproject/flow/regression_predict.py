"""Run the runtime Qualifier on the 100 eval-set cases and store its answers for the regression gate.

    docker compose -f flow/docker-compose.yml up -d   # local CPU Qualifier, about 40 s to load
    uv run python -m flow.regression_predict
    uv run python ml/qualifier/scripts/regression_check.py

It calls the same code as the demo (`flow/qualifier.py`: production prompt, structured output), one
ticket at a time, and writes the predictions and a manifest of what produced them. Local and free;
it reads the hand-labelled eval-set only. Commit both files: CI replays them (issue #19).
"""

import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from flow.contracts import Ticket, load_config
from flow.qualifier import build_qualifier_model, load_qualifier_prompt, qualify
from ml.qualifier.src.regression_eval import (
    TICKET_PLACEHOLDER,
    expected_fingerprint,
    load_thresholds,
    load_triples,
    prompt_template_sha,
    resolve,
)


def main() -> int:
    load_dotenv(Path(__file__).parent.parent / ".env")
    config = load_config()
    source = load_thresholds()["source"]
    eval_set = resolve(source["eval_set"])
    triples = load_triples(eval_set)
    prompt = load_qualifier_prompt(config)
    model = build_qualifier_model(config)

    rows, statuses = [], Counter()
    for i, triple in enumerate(triples, 1):
        ticket = Ticket(ticket_id=triple.case_id, merchant_id=config.merchant_id,
                        body=triple.ticket, created_at=datetime.now(UTC))
        result = qualify(ticket, model=model, config=config, prompt=prompt)
        statuses[result.status] += 1
        rows.append({"id": triple.case_id, "status": result.status, "raw_output": result.raw or ""})
        print(f"{i:>3}/{len(triples)} {triple.case_id} {result.status}", flush=True)

    predictions = resolve(source["predictions"])
    predictions.parent.mkdir(parents=True, exist_ok=True)
    with predictions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "status", "raw_output"])
        writer.writeheader()
        writer.writerows(rows)

    fingerprint = expected_fingerprint(eval_set, resolve(source["flow_config"]))
    # The prompt actually used, which may come from Langfuse: the gate compares it with the repository.
    fingerprint["prompt_sha256"] = prompt_template_sha(str(prompt.compile(ticket=TICKET_PLACEHOLDER)))
    manifest = {
        **fingerprint,
        "prompt_name": prompt.name,
        "prompt_label": prompt.label,
        "prompt_version": prompt.version,
        "decoding": "structured output, JSON schema, strict (flow/qualifier.py)",
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "cases": len(rows),
        "statuses": dict(statuses),
    }
    resolve(source["manifest"]).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {predictions.name}: {dict(statuses)}")
    return 0 if statuses.get("unavailable", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
