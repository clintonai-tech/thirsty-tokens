# ADR-0002: Use LiteLLM Python SDK instead of the proxy

- Status: accepted

## Context
The proxy needs an always-on container and Postgres, which breaks the 50 EUR budget.

## Decision
Use the SDK inside the Lambda for token and cost accounting.

## Consequences
No virtual keys or per-user budgets. Spend cap and rate limits are implemented in DynamoDB instead.
