# ADR-0007: Spend cap by reserve-then-settle

- Status: accepted
- Date: 2026-10-09

## Context
The public endpoint must stay inside the credit. The daily cap lives in a DynamoDB counter. A "read the counter, call the model, add the cost" flow lets concurrent requests all pass the check before any of them pays, so the cap can be overshot. Actual cost is only known after the call, and a streamed answer can be cut off midway.

## Decision
Reserve, then settle:
1. Before the call, one conditional `UpdateItem` adds the **worst-case cost** (input tokens bounded by prompt UTF-8 bytes, plus the 500-token output maximum) to today's counter, only if `spent + worst <= cap`. If the condition fails, the request gets a friendly 429 and the model is never called.
2. After the call, a second atomic add applies `actual - reserved` (negative values refund).
3. Failed calls refund fully. A stream that dies after producing output keeps the reservation, because usage is unknown and the safe side is the cap.

Money is stored as integer micro-USD. Counters are keyed by UTC day with a TTL.

Alternative considered: check first, then add the actual cost after. It is simpler and needs one fewer write, but it races under concurrency.

## Consequences
- The cap cannot be exceeded by concurrent requests; at most one request's worst case (a fraction of a cent for these models) sits unsettled.
- Near the cap, a request may be refused although its actual cost would have fit, since the reservation is pessimistic. That is acceptable at a $2 cap.
- Two DynamoDB writes per request, both on-demand and negligible in cost.
- If settling fails, the reservation stays: the error is on the safe side.
