# CLAUDE.md

Project: thirsty-tokens. Compare LLMs on cost, speed, energy, carbon, water.
Read `docs/PLAN.md` and `docs/CONSTRAINTS.md` at the start of every session. Session tasks live in `docs/sessions/`.

## Stack
- Backend: Python 3.13 (uv), FastAPI, LiteLLM Python SDK (not the proxy), AWS Bedrock
- Infra: AWS CDK in **TypeScript** (strict), DynamoDB, Lambda (container image, arm64, Lambda Web Adapter)
- Frontend: Next.js + Tailwind + shadcn/ui on Vercel
- Observability: Langfuse. CI/CD: GitHub Actions for checks only; deploys are manual (SCP blocks OIDC)

## Hard constraints
- Only region **eu-north-1** is allowed (org SCP). Use `AWS_PROFILE=thirsty`.
- Never read `~/.aws` or credential files. Never print, log, or commit secrets. Secrets go in SSM Parameter Store.
- No always-on resources (NAT gateways, containers, RDS). Budget is the $100 credit, self-cap 50 EUR.
- Ask before any action that costs money or creates resources outside the CDK stacks.
- If an SCP denies an action, stop and report the exact error. Never work around it.
- **Never run `cdk deploy` (or any other command that creates, changes, or destroys AWS resources).** The owner always deploys manually: Claude gives the commands (`cdk diff` first, then `cdk deploy`), the owner reviews the diff and runs them. Claude may run read-only `cdk synth`, and `cdk diff` only if the owner asks.

## Code rules
- Typed Python; ruff (lint + format), mypy strict, pytest. TypeScript strict; ESLint, Prettier, Jest.
- Calculations (cost, energy, carbon, water, equivalents) are pure functions with unit tests. No LLMs in calculations.
- All coefficients live in one config file with a source comment per value.
- Max output tokens is hardcoded server-side on every request.
- Models live in `backend/models.yaml`, never hardcoded.
- Conventional commits, small PRs, ADRs in `docs/adr/` for significant decisions.

## Working agreements
1. Start each session by reading the docs, then show a short plan and **wait for approval**.
2. Learning mode: before each major step, explain in 3-4 lines what and why. For real design choices, give two options with trade-offs and let me choose.
3. End each session by: updating `docs/PLAN.md` status, appending to `docs/learning-notes.md`, and listing done, left, and deviations.
4. Keep answers and docs concise.

## Commands
- Backend: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy`
- Infra: `cd infra && npm ci && npm test && npx cdk synth`
- Deploy (owner runs manually, in order): `cd infra && AWS_PROFILE=thirsty npx cdk diff <Stack>`, review, then `AWS_PROFILE=thirsty npx cdk deploy <Stack>`
