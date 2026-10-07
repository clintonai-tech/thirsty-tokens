# Session 2: Backend core

Read CLAUDE.md, docs/PLAN.md, docs/CONSTRAINTS.md, docs/learning-notes.md. Plan first, wait for approval.

## Tasks
1. Streaming: SSE endpoint POST /chat/stream (Lambda function URL response streaming). Final event carries usage, cost, latency, time-to-first-token, tokens/sec, footprint, equivalents. Keep /chat working.
2. Footprint module (pure functions, backend/src/thirsty_tokens/footprint/):
   - coefficients.py: per-tier Wh/token, EU average grid intensity, water usage constant, each with a source comment and retrieval date. Research current sources and cite them. Label as estimates.
   - calculate(tier, input_tokens, output_tokens) -> energy_wh, carbon_g, water_l.
   - Unit tests with fixed expected values and edge cases (zero tokens, unknown tier).
3. Equivalents module (pure, deterministic): phone charges, Google searches, kettle seconds, sips of water. One constants dict with sources. Pick the most readable unit per magnitude. Unit tests.
4. Spend cap: DynamoDB atomic daily counter in USD. Check before the call using a worst-case cost estimate (input tokens + max output), update with actual cost after. Friendly 429 when reached. Extract a small repository class so it is testable.
5. Rate limit: per-IP daily counter in DynamoDB with TTL. Read IP from the function URL request context, not from a client header. Friendly 429.
6. Tests: DynamoDB with moto or a local stub, LiteLLM mocked. All checks pass.
7. CDK: pass table name and settings via env vars. Show `cdk diff`, wait for OK, deploy, verify with curl.
8. ADRs for any real decision (e.g. cap check strategy). Update docs.
