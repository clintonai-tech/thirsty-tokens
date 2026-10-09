# thirsty-tokens

Compare LLMs on cost, speed, energy, carbon, and water. Built on AWS Bedrock (eu-north-1), LiteLLM, and FastAPI.

> Status: in development

## What it does
- Send a prompt to a Bedrock model and see tokens, cost, latency, and estimated energy, carbon, and water use
- Compare two models side by side
- Relatable equivalents (phone charges, Google searches, kettle seconds, sips of water), computed deterministically
- Quality vs cost vs footprint chart from an offline benchmark

## Architecture
_Diagram coming in Session 5._

| Layer | Tech |
|---|---|
| Frontend | Next.js, Tailwind, shadcn/ui (Vercel) |
| Backend | FastAPI + LiteLLM SDK on AWS Lambda |
| LLM | AWS Bedrock |
| Storage | DynamoDB (spend cap, rate limits) |
| IaC | AWS CDK (TypeScript) |
| CI/CD | GitHub Actions (checks only); manual `cdk deploy` |
| Observability | Langfuse |

## Repo layout
```
backend/   FastAPI app, model registry (models.yaml), Dockerfile, tests
infra/     AWS CDK (TypeScript) app stack
frontend/  Next.js app
docs/adr/  Architecture decision records
scripts/   Offline benchmark and utilities
```

## Getting started
```bash
uv sync                # install backend deps
uv run pytest          # run tests (LiteLLM is mocked)
uv run ruff check .    # lint
uv run mypy            # type check
PYTHONPATH=backend/src AWS_PROFILE=thirsty uv run uvicorn thirsty_tokens.app:app --reload  # run locally (real Bedrock calls cost money)
```

## Deploy
Region is eu-north-1 only. Deploys are manual (see [ADR-0006](docs/adr/0006-manual-deploys-no-oidc.md)):
```bash
cd infra && npm ci
export AWS_PROFILE=thirsty
npx cdk diff ThirstyTokensStack     # review the changes first
npx cdk deploy ThirstyTokensStack   # needs Docker running; prints FunctionUrl
```
Infra checks: `cd infra && npm ci && npm run lint && npm test && npx cdk synth`.

## Methodology
Energy, carbon, and water figures are estimates based on per-tier coefficients. Sources and assumptions will live in `docs/methodology.md`.

## License
MIT
