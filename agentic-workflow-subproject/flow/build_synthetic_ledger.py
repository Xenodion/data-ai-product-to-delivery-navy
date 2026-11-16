"""Build a versioned demo ledger from references in authored synthetic tickets.

The builder reads only ticket text from frozen synthetic splits. It does not read
the target/label columns. The resulting ledger is an independent simulator
fixture, not an observed Keelpay dataset or a quality label for the Qualifier.
"""

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path(__file__).parent / "fixtures" / "ledger.json"
DEFAULT_INPUTS = (
    ROOT / "data" / "dataset" / "val.csv",
    ROOT / "data" / "dataset" / "test_natural.csv",
    ROOT / "data" / "dataset" / "test_traps.csv",
)
REFERENCE = re.compile(r"\bTX[\s-]?(?:\d[\s-]?){6}\b", re.IGNORECASE)
STATUS_VALUES = ("settled", "processing", "under_review")


def build_records(paths: tuple[Path, ...]) -> list[dict[str, str]]:
    ids: set[str] = set()
    for path in paths:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                # Intentionally ignore `target` and every annotation column.
                for match in REFERENCE.finditer(row["ticket"]):
                    digits = re.sub(r"\D", "", match.group()).upper()
                    if len(digits) == 8 and digits.startswith("TX"):
                        digits = digits[2:]
                    if len(digits) == 6:
                        ids.add(f"TX-{digits}")

    records = []
    for transaction_id in sorted(ids):
        suffix = int(transaction_id[-2:])
        day = suffix % 6 + 1
        records.append(
            {
                "merchant_id": "M-DEMO",
                "transaction_id": transaction_id,
                "status": STATUS_VALUES[sum(map(int, transaction_id[-6:])) % len(STATUS_VALUES)],
                "updated_at": f"2026-11-{day:02d}",
                "source_id": f"ledger_{transaction_id.lower().replace('-', '_')}",
                "source_version": "ledger-v1",
            }
        )

    # Fixed adversarial fixtures exercise merchant isolation and ambiguous data.
    records.extend(
        [
            {
                "merchant_id": "M-OTHER",
                "transaction_id": "TX-900002",
                "status": "settled",
                "updated_at": "2026-11-06",
                "source_id": "ledger_foreign_tx_900002",
                "source_version": "ledger-v1",
            },
            {
                "merchant_id": "M-DEMO",
                "transaction_id": "TX-900001",
                "status": "processing",
                "updated_at": "2026-11-05",
                "source_id": "ledger_ambiguous_a_tx_900001",
                "source_version": "ledger-v1",
            },
            {
                "merchant_id": "M-DEMO",
                "transaction_id": "TX-900001",
                "status": "under_review",
                "updated_at": "2026-11-06",
                "source_id": "ledger_ambiguous_b_tx_900001",
                "source_version": "ledger-v1",
            },
        ]
    )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--inputs", type=Path, nargs="+", default=DEFAULT_INPUTS)
    args = parser.parse_args()
    payload = {"version": "synthetic-ledger-v1", "records": build_records(tuple(args.inputs))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['records'])} synthetic ledger rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
