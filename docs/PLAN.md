# Plan

## Goal
A public portfolio app to showcase AI engineering: query an LLM on AWS Bedrock and see tokens, cost, latency, and estimated energy, carbon, and water, with relatable equivalents. Compare two models side by side. A static cost vs energy chart comes from an offline benchmark (no quality scoring).

## Scope
**In:** model picker (5 models), single and compare mode, streaming, token and cost via LiteLLM, footprint estimates (deterministic), relatable equivalents (deterministic), daily spend cap and per-IP rate limit (DynamoDB), Langfuse tracing, offline benchmark (no LLM judge), CDK TypeScript, CI/CD with OIDC, ADRs, methodology page.

**Out:** LLM-as-judge quality scoring, uncertainty ranges, tokenizer visualizer, prompt diet, what-if sliders, guessing game, community totals, share cards, evaluation in CI, public stats page, custom domain, Bedrock Guardrails, AWS Budgets (not available).

## Architecture
Browser (Vercel, Next.js) -> Lambda function URL (FastAPI + LiteLLM, container image) -> Bedrock (eu-north-1). DynamoDB holds spend cap and rate-limit counters. Langfuse receives traces. Benchmark results are a static JSON file served to the frontend.

## Sessions (5 x 2h)
| # | Focus | Status |
|---|---|---|
| 1 | Foundations: docs, repo changes, FastAPI + LiteLLM, CDK TS stack, CI checks, manual deploy | in progress (code done; deploy and verify pending) |
| 2 | Backend core: streaming, footprint, equivalents, spend cap, rate limit, tests | todo |
| 3 | Frontend: Next.js UI, streaming, metric cards, Vercel deploy | todo |
| 4 | Compare mode, offline benchmark, chart | todo |
| 5 | Langfuse, hardening, kill switch, README, methodology, diagram, ADRs | todo |

If a session overruns: push the chart (4) or Langfuse (5) later.

Known limitation (state it in the README): the app compares cost, speed, and footprint, not answer quality. The core app should be live by the end of Session 3.

## Definition of done
Live URL, public repo with architecture diagram, ADRs, passing CI, one-command deploy, methodology page.
