# RFC-001: Primary Database for Lumen Pay Ledger

- **Status:** Accepted (2026-03-12)
- **Author:** Maya Chen (Staff Engineer, Payments)
- **Reviewers:** Raj Patel (CTO), Sofia Alvarez (SRE Lead), Tom Becker (Backend)
- **Visibility:** Engineering (all)
- **Related:** GitHub PR #42 "Migrate ledger to Postgres", GitHub issue #31 "Mongo write conflicts under load", Slack thread #eng-decisions 2026-03-05

## Context

The ledger service stores every payment event. In Q1 2026 we saw duplicate-write
conflicts in MongoDB during peak load (issue #31), and finance asked for strict
transactional guarantees for reconciliation.

## Options

1. **Keep MongoDB.** No migration cost. Multi-document transactions exist but
   performed poorly in our load test (p99 1.8s at 2k writes/s).
2. **PostgreSQL 16.** Strong ACID guarantees, mature tooling, team familiarity.
   p99 120ms at 2k writes/s in the same test.
3. **CockroachDB.** Good horizontal scaling, but operational cost and licensing
   were unclear. Rejected for now.

## Decision

Adopt **PostgreSQL 16** (managed, Multi-AZ) as the primary ledger store.
Maya Chen owns the migration. Target cutover: 2026-05-15.

## Consequences

- Migration work tracked in PR #42 and issue #44 "Dual-write phase".
- MongoDB stays read-only until 2026-07-01, then is decommissioned.
- Sofia Alvarez owns backup and failover runbooks for Postgres.
- Revisit sharding if sustained writes exceed 8k/s (see decision log D-007).
