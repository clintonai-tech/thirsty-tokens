# Session 1: Foundations

Read CLAUDE.md, docs/PLAN.md, docs/CONSTRAINTS.md. Show a short plan and wait for approval. Work in small conventional commits.

## Preconditions (confirm, do not assume)
Docker is running, `AWS_PROFILE=thirsty`, Node 24, `uname -m`. If the machine is not arm64, tell me before building images.

## Tasks
0. Repo housekeeping: update stack mentions to CDK TypeScript and region eu-north-1 in README and .env.example. Remove `infra` from ruff `src` in pyproject.toml. Add ADRs: 0003 region eu-north-1 (SCP), 0004 CDK TypeScript, 0005 container-image Lambda, 0006 LiteLLM cost fallback pricing table (if needed).
1. Backend (backend/src/thirsty_tokens):
   - config (pydantic-settings): region, max output tokens (500, not client-controllable), max input chars.
   - model registry from backend/models.yaml (id, display name, provider, tier, litellm model string, optional pricing).
   - FastAPI: GET /health, GET /models, POST /chat (non-streaming). /chat validates the model, calls LiteLLM with aws_region_name=eu-north-1, returns text, input/output tokens, cost, latency ms.
   - First check whether LiteLLM returns cost for the EU profile IDs. If not, implement the pricing-table fallback as a pure function.
2. Tests: pytest with LiteLLM mocked. Cover registry, validation, token and cost mapping, max-token enforcement. ruff, format, mypy pass.
3. Infra: remove infra/.gitkeep, then `cdk init app --language typescript` in infra/. Strict tsconfig, ESLint, Prettier, Jest with CDK assertions. Env pinned to CDK_DEFAULT_ACCOUNT and eu-north-1.
   - DynamoDB on-demand, pk/sk, TTL attribute, removal policy DESTROY.
   - Lambda DockerImageFunction, arm64, Lambda Web Adapter, response streaming enabled for later, function URL with placeholder CORS, 512MB, 30s, 14-day log retention.
   - Least-privilege IAM: Bedrock invoke scoped to the 5 profiles and the foundation models they route to, plus the one table. Explain the scoping in a comment.
   - Backend Dockerfile (uv, slim).
   - `cdk synth` and `npm test` pass. Show `cdk diff` and wait for my OK before `cdk deploy`.
4. CI/CD:
   - Extend CI with a Node 24 job: npm ci, lint, test, cdk synth.
   - Separate small CDK stack for GitHub OIDC provider and deploy role (trust: this repo, main branch). I deploy it manually once.
   - Deploy workflow (main + manual) using OIDC. If the SCP blocks IAM OIDC, stop and report. Never use access keys.
5. Verify: call /health and /chat on the deployed URL for two models and show output. Check Cost Explorer note: tell me how to confirm credits apply.
6. Update README (layout, local run, deploy), docs/PLAN.md status, docs/learning-notes.md.

## Out of scope
Footprint and equivalents, spend cap, rate limiting, frontend, Langfuse, benchmark.
