"""Create demo issues in YOUR OWN test repo (as the authorizing user, via Scalekit).

Usage:
    .venv/bin/python seed_github.py --user jian.han3@gmail.com --repo <owner>/lumen-pay-demo

Only run this against a throwaway demo repo you own. It creates ~8 issues.
Issue numbers will start from the repo's next free number, so they will not
match the "#42" style references in the Notion docs; the titles do match.
"""
import argparse
import os

try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from dotenv import load_dotenv
from scalekit import ScalekitClient

load_dotenv()

ISSUES = [
    ("Mongo write conflicts under load",
     "Duplicate-write conflicts in the MongoDB ledger during peak load. Finance needs strict transactional "
     "guarantees for reconciliation. Leads to RFC-001 (see Notion: 01-rfc-001-database-choice)."),
    ("Migrate ledger to Postgres (PR)",
     "Implements RFC-001: PostgreSQL 16 replaces MongoDB as the ledger store. Owner: Maya Chen. "
     "Cutover target 2026-05-15. Two reviewers required under ledger/ (decision D-009)."),
    ("Dual-write phase for ledger migration",
     "Write to both MongoDB and Postgres until cutover. Mongo goes read-only on 2026-07-01. Owner: Maya Chen."),
    ("Webhook retries flood merchants",
     "Synchronous webhook retries pile up when a merchant endpoint is slow and delay other payments. "
     "Leads to RFC-002 (SQS FIFO). Owner: Tom Becker."),
    ("Add SQS publisher for payment webhooks (PR)",
     "Implements RFC-002: SQS FIFO with one message group per merchant plus a DLQ. Owner: Tom Becker. "
     "Merchants must dedupe by event_id (at-least-once delivery)."),
    ("Billing outage 2026-09-02: card-network timeouts",
     "Card network timeouts exhausted the connection pool because retries were uncapped. "
     "Postmortem PM-2026-09 (engineering leads only). Owner: Sofia Alvarez."),
    ("Circuit breaker for card-network client (PR)",
     "Adds a circuit breaker and caps retries at 3 with jittered backoff. Decision D-014. Owner: Sofia Alvarez."),
    ("Require two reviewers for ledger/ changes",
     "Branch protection: two approvals for any change under ledger/. Decision D-009. Owner: Sofia Alvarez."),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--repo", required=True, help="owner/name of YOUR demo repo")
    args = ap.parse_args()

    actions = ScalekitClient(
        env_url=os.environ["SCALEKIT_ENVIRONMENT_URL"],
        client_id=os.environ["SCALEKIT_CLIENT_ID"],
        client_secret=os.environ["SCALEKIT_CLIENT_SECRET"],
    ).actions
    conn = os.environ.get("GITHUB_CONNECTION_NAME", "github-connect")

    account = actions.get_or_create_connected_account(
        connection_name=conn, identifier=args.user
    ).connected_account
    if account.status != "ACTIVE":
        link = actions.get_authorization_link(connection_name=conn, identifier=args.user).link
        print(f"Authorize GitHub first, then re-run:\n{link}")
        return

    for title, body in ISSUES:
        r = actions.request(
            connection_name=conn,
            identifier=args.user,
            method="POST",
            path=f"/repos/{args.repo}/issues",
            body={"title": title, "body": body},
        )
        print(r.status_code, title)
        if r.status_code >= 300:
            print(r.text[:300])
            break


if __name__ == "__main__":
    main()
