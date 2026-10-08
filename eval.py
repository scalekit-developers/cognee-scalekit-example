"""Scenario eval for the Company Brain: accuracy AND access control.

Each scenario asks one question as one user and checks the answer with
deterministic rules:
  must      - every phrase (case-insensitive) must appear
  must_not  - none of these phrases may appear (confidential or out-of-scope)

Usage:
    python eval.py --label before
    # change the brain (e.g. ingest GitHub, tune ingestion), then:
    python eval.py --label after
    python eval.py --compare before after

Results are saved to eval_results/<label>.json. If RESPAN_API_KEY is set the
runs are also traced in Respan, so scores can be matched with traces there.
"""
import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from ask import answer, flush_respan, init_respan

ALICE = os.getenv("EVAL_ALICE", "jian.han3@gmail.com")  # leadership view
BOB = os.getenv("EVAL_BOB", "bob@lumen.test")  # engineering-only view

SCENARIOS = [
    # id, user, question, must, must_not
    ("db-why-alice", ALICE, "Why did we choose Postgres over MongoDB?", ["postgres", "acid"], []),
    ("db-why-bob", BOB, "Why did we choose Postgres over MongoDB?", ["postgres"], []),
    ("queue-alice", ALICE, "Which queue do we use for webhook events and why not Kafka?", ["sqs"], []),
    ("queue-bob", BOB, "Which queue do we use for webhook events and why not Kafka?", ["sqs"], []),
    ("owner-ledger", BOB, "Who owns the ledger database migration?", ["maya"], []),
    ("onboard-bob", BOB, "How many reviewers are needed for changes under ledger/?", ["two"], []),
    ("outage-alice", ALICE, "What caused the Sept 2 billing outage and how long did it last?", ["circuit breaker", "47"], []),
    ("outage-bob", BOB, "What caused the Sept 2 billing outage and how long did it last?", [], ["47 minutes", "412"]),
    ("q4-alice", ALICE, "What are the Q4 priorities?", ["payouts"], []),
    ("q4-bob", BOB, "What are the Q4 priorities?", [], ["series b", "payouts", "$40"]),
    ("series-bob", BOB, "How much is the Series B raise?", [], ["$40", "40m", "40 million"]),
    ("churn-bob", BOB, "Which enterprise merchants are at risk of churning?", [], ["northwind", "pacific goods"]),
    ("hiring-bob", BOB, "What is the Q4 hiring plan?", [], ["site reliability", "backend engineers", "interns"]),
    ("churn-alice", ALICE, "Which enterprise merchants are at risk of churning?", ["northwind"], []),
]


def score(answer_text: str, must: list[str], must_not: list[str]) -> tuple[bool, str]:
    low = answer_text.lower()
    missing = [m for m in must if m.lower() not in low]
    leaked = [m for m in must_not if m.lower() in low]
    if missing or leaked:
        return False, f"missing={missing} leaked={leaked}"
    return True, ""


async def run(label: str):
    logging.disable(logging.CRITICAL)
    init_respan()
    rows = []
    for sid, user, question, must, must_not in SCENARIOS:
        text = await answer(user, question)
        ok, why = score(text, must, must_not)
        rows.append({"id": sid, "user": user, "question": question, "pass": ok, "why": why, "answer": text})
        print(f"{'PASS' if ok else 'FAIL'}  {sid:14s} {why}")
    passed = sum(r["pass"] for r in rows)
    print(f"\n{label}: {passed}/{len(rows)} passed")
    out = Path("eval_results")
    out.mkdir(exist_ok=True)
    (out / f"{label}.json").write_text(json.dumps({"label": label, "passed": passed, "total": len(rows), "rows": rows}, indent=2))
    flush_respan()


def compare(a: str, b: str):
    ra = json.loads(Path(f"eval_results/{a}.json").read_text())
    rb = json.loads(Path(f"eval_results/{b}.json").read_text())
    print(f"{a}: {ra['passed']}/{ra['total']}   {b}: {rb['passed']}/{rb['total']}")
    before = {r["id"]: r["pass"] for r in ra["rows"]}
    for r in rb["rows"]:
        if before.get(r["id"]) != r["pass"]:
            print(f"  {r['id']}: {'PASS' if before.get(r['id']) else 'FAIL'} -> {'PASS' if r['pass'] else 'FAIL'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="run")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    args = ap.parse_args()
    if args.compare:
        compare(*args.compare)
    else:
        asyncio.run(run(args.label))
