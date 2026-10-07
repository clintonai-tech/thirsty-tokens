# Session 5: Observability, hardening, launch

Read CLAUDE.md, docs/PLAN.md, docs/CONSTRAINTS.md, docs/learning-notes.md. Plan first, wait for approval.

## Tasks
1. Langfuse: I have the keys and will store them in SSM myself. Give me the exact `aws ssm put-parameter` commands (SecureString). You read them in Lambda at cold start via boto3 and cache them. Trace each request: model, tokens, cost, latency, footprint. Tracing failures must never break a request. Use the LiteLLM Langfuse callback or the SDK, explain the choice.
2. Kill switch: SSM parameter or env flag that disables /chat immediately (friendly maintenance message), plus a documented runbook in docs/RUNBOOK.md. AWS Budgets is unavailable, so this is the emergency brake.
3. Hardening: input sanitation, consistent error shapes, structured JSON logs with request IDs, a CloudWatch alarm on Lambda errors and one on Bedrock throttles (SNS email if allowed by the SCP, otherwise skip and tell me), timeouts and retries on Bedrock calls.
4. Methodology page: sources, assumptions, coefficients, limits, "estimates" disclaimer. Pull values from the same config as the code.
5. README: what it is, screenshots, live link, architecture diagram (mermaid), decisions and tradeoffs, cost notes, one-command deploy, local dev, CI badges. Add LICENSE name, repo topics, and a short "what I learned" section.
6. Final checks: credits usage, secrets scan of the repo and git history, remove dead code, make sure CI is green, tag v1.0.0.
7. Draft a LinkedIn post and a YouTube video outline from the project (docs/launch/).
