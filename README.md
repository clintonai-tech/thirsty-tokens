# thirsty-tokens

Compare LLMs on cost, speed, energy, carbon, and water. Built on AWS Bedrock, LiteLLM, and FastAPI.

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
| IaC | AWS CDK (Python) |
| CI/CD | GitHub Actions (OIDC) |
| Observability | Langfuse |

## Repo layout
```
backend/   FastAPI app, footprint and cost logic, tests
infra/     AWS CDK stacks
frontend/  Next.js app
docs/adr/  Architecture decision records
scripts/   Offline benchmark and utilities
```

## Getting started
```bash
uv sync                # install backend deps
uv run pytest          # run tests
uv run ruff check .    # lint
```

## Methodology
Energy, carbon, and water figures are estimates based on per-tier coefficients. Sources and assumptions will live in `docs/methodology.md`.

## License
MIT
