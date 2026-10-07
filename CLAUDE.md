# CLAUDE.md

Project: thirsty-tokens. Compare LLMs on cost, speed, energy, carbon, water.

## Stack
Python 3.13 (uv), FastAPI, LiteLLM SDK (not proxy), AWS Bedrock (eu-central-1), DynamoDB, AWS CDK (Python), AWS Lambda, Next.js + Tailwind + shadcn/ui on Vercel, Langfuse, GitHub Actions.

## Rules
- Typed Python everywhere; ruff for lint and format; pytest for tests.
- Calculations (cost, energy, carbon, water, equivalents) are pure functions with unit tests. No LLMs in calculations.
- All coefficients live in one config file with a source comment per value.
- Max output tokens is hardcoded in the backend on every request.
- Daily spend cap and per-IP rate limit tracked in DynamoDB.
- No secrets in code. Use SSM Parameter Store. Provide `.env.example` only.
- Conventional commits. Small PRs. Record decisions as ADRs in `docs/adr/`.
- Keep answers and docs concise.

## Commands
- `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- `cd infra && cdk synth`

## Budget
Hard cap of 50 EUR total. Prefer cheap models. Never add always-on resources (NAT gateways, containers, RDS).
