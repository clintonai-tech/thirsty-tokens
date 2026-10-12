# ADR-0009: Frontend stack and streaming client

- Status: accepted
- Date: 2026-10-12

## Context
Session 3 needs a public, mobile-first UI that streams answers from `POST /chat/stream` and shows cost, speed and footprint. It deploys on Vercel and talks to the Lambda function URL directly from the browser.

## Decision
- **Next.js App Router + Tailwind v4 + shadcn/ui** (only Button and Textarea). One page, a methodology stub, few dependencies. The model picker is a native `<select>`: best mobile and screen-reader behaviour for five options, and no extra Radix/Base UI dependency.
- **`fetch` + `ReadableStream` with a small SSE parser** (`lib/sse.ts`), not `EventSource`, because the endpoint is POST. The parser is pure and unit-tested, including events split across chunks.
- **Browser calls the Lambda directly** (no Next.js proxy). `NEXT_PUBLIC_API_URL` is baked in at build time. This keeps streaming simple and adds no server on Vercel; the cost is that CORS must list the Vercel origin (the `PRODUCTION_ORIGIN` constant in `infra/bin/app.ts`; `-c corsOrigin=` overrides it). CORS is not a security control here; the spend cap and per-IP limit are.
- **Errors are mapped by the client** to fixed messages (`lib/api.ts`). 429 uses the server's `reason` (`spend_cap` or `rate_limit`) to pick the wording; server text is never shown raw.
- **Max prompt length (2000) is a constant** mirroring the server default. The server re-checks it, so drift only costs a 422.
- **Design:** water-level glass as the single memorable element, flat ruled metric list instead of a card grid, Bricolage Grotesque + Hanken Grotesk, light and dark via a `.dark` class (saved choice, else system).

## Consequences
- If `TT_MAX_INPUT_CHARS` changes, the UI constant must change too (or `/models` could expose it later).
- Preview deployments on Vercel get a different origin and will fail CORS until added; only the production URL is allowed by choice.
- The first request after idle can take 20s+ (cold start, see learning notes); the loading state says so.
