# Postmortem PM-2026-09: Billing Outage on 2026-09-02

- **Visibility:** Engineering leads only (Raj Patel, Maya Chen, Sofia Alvarez)
- **Severity:** SEV-1, 47 minutes of failed card payments
- **Related:** GitHub issue #77, PR #81 "Circuit breaker for card client", Slack #eng-leads 2026-09-02

## Summary

On 2026-09-02 at 14:10 UTC the upstream card network began timing out. The
payments service retried without limits, exhausted its connection pool, and
failed all card payments for 47 minutes. About 3,100 payments failed; the
estimated revenue delayed was $412,000 (all later recovered via retries).

## Root cause

No circuit breaker or timeout cap on the card-network client. Retries
amplified the outage.

## Timeline (UTC)

- 14:10 Card network latency rises. First alert at 14:14.
- 14:21 Sofia Alvarez declares SEV-1.
- 14:40 Maya Chen disables retries via feature flag.
- 14:57 Service recovers.

## Action items

1. Add a circuit breaker around the card-network client (owner: Sofia Alvarez, PR #81). Logged as decision D-014.
2. Cap retries at 3 with jittered backoff (owner: Tom Becker).
3. Add a connection-pool saturation alert (owner: Sofia Alvarez).
4. Customer communication: handled by Support Lead Priya Nair; credits issued to 12 enterprise merchants.

## Notes

Two enterprise merchants threatened to churn. Account details are in the
leadership-only revenue review (see Notion "Leadership").
