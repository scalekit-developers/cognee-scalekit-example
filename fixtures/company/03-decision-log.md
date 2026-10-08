# Lumen Pay Decision Log

- **Visibility:** Engineering (all)

| ID | Date | Decision | Owner | Why | Source |
|----|------|----------|-------|-----|--------|
| D-001 | 2026-01-14 | Use Python 3.12 + FastAPI for all new services | Raj Patel | Team skill set, async support | Slack #eng-decisions |
| D-004 | 2026-02-02 | Adopt trunk-based development with feature flags | Maya Chen | Long-lived branches caused merge pain | PR #19 |
| D-006 | 2026-03-12 | PostgreSQL 16 replaces MongoDB for the ledger | Maya Chen | Mongo write conflicts, ACID needs | RFC-001, PR #42 |
| D-007 | 2026-03-12 | Revisit sharding only if sustained writes exceed 8k/s | Maya Chen | Avoid premature complexity | RFC-001 |
| D-009 | 2026-04-08 | Require two reviewers for any change under `ledger/` | Sofia Alvarez | Money-moving code | PR #51 |
| D-011 | 2026-05-20 | SQS FIFO for webhook events; defer Kafka | Tom Becker | Team size, ops cost | RFC-002, PR #58 |
| D-014 | 2026-09-03 | Add circuit breaker around the card-network client | Sofia Alvarez | Sept 2 billing incident | Postmortem PM-2026-09 |
| D-015 | 2026-09-10 | Freeze non-critical deploys on the last 2 days of each month | Raj Patel | Month-end reconciliation risk | Slack #eng-leads |
