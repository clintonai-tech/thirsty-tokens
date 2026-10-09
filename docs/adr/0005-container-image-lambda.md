# ADR-0005: Run the backend as a container-image Lambda

- Status: accepted
- Date: 2026-10-08

## Context
The backend is FastAPI with LiteLLM, which is a large dependency set. We need response streaming later and no always-on resources.

## Decision
Package the backend as a container image (arm64) on Lambda with the Lambda Web Adapter, exposed through a function URL with response streaming enabled.

## Consequences
Images allow up to 10 GB, so LiteLLM fits easily, and the same app runs locally with uvicorn. Cold starts are slower than zip packages. Pay-per-request keeps idle cost at zero.
