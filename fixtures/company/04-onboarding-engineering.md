# Engineering Onboarding Guide

- **Visibility:** Engineering (all), including interns and new hires

## Week 1

1. Get access: GitHub org `lumenpay`, Slack (#eng, #eng-decisions, #oncall-help), Notion Engineering space.
2. Clone `lumenpay/ledger` and `lumenpay/payments-api`; run `make dev` (needs Docker, Python 3.12).
3. Read RFC-001 (why Postgres) and RFC-002 (why SQS) before touching `ledger/`.
4. Pair with your onboarding buddy for your first PR. Small docs fixes are fine.

## Who to ask

| Topic | Person |
|-------|--------|
| Ledger and database | Maya Chen |
| Webhooks and queues | Tom Becker |
| Infrastructure, deploys, on-call | Sofia Alvarez |
| Architecture questions | Raj Patel (CTO) |

## Rules to know

- Two reviewers are required for any change under `ledger/` (decision D-009).
- Feature flags are mandatory for user-facing changes (D-004).
- No deploys on the last 2 days of the month (D-015).
- Interns do not get production database access. Use the staging replica.

## On-call

On-call rotation starts after your third month. Runbooks live in the Notion
"Runbooks" page. Page Sofia Alvarez for infrastructure incidents.
