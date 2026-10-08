# RFC-002: Event Queue for Payment Notifications

- **Status:** Accepted (2026-05-20)
- **Author:** Tom Becker (Backend)
- **Reviewers:** Maya Chen, Sofia Alvarez, Raj Patel
- **Visibility:** Engineering (all)
- **Related:** GitHub PR #58 "Add SQS publisher", issue #52 "Webhook retries flood merchants", Slack thread #eng-decisions 2026-05-14

## Context

Merchant webhooks are sent synchronously from the payment service. When a
merchant endpoint is slow, retries pile up and delay other payments (issue #52).

## Options

1. **Amazon SQS + DLQ.** Simple, managed, cheap. No ordering across messages
   (FIFO queues give ordering per merchant at lower throughput).
2. **Kafka (MSK).** Great for replay and streaming, but heavy for a team of 9
   engineers. Estimated 0.5 FTE ongoing operations.
3. **Keep synchronous retries.** Rejected: root cause of issue #52.

## Decision

Use **SQS FIFO** with one message group per merchant, plus a dead-letter queue.
Tom Becker owns implementation (PR #58). Kafka is deferred until we need replay
or streaming analytics (decision log D-011).

## Consequences

- Webhook delivery decouples from payment latency.
- Merchants see at-least-once delivery; they must dedupe by `event_id`.
- Sofia adds DLQ alerting to the on-call runbook.
