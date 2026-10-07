# Session 3: Frontend

Read CLAUDE.md, docs/PLAN.md, docs/CONSTRAINTS.md, docs/learning-notes.md. Plan first, wait for approval. Invoke the frontend-design skill before building UI.

## Tasks
1. Scaffold Next.js (App Router, TypeScript strict) + Tailwind + shadcn/ui in frontend/. Keep it lightweight: one page, few dependencies.
2. UI: modern, clean, mobile-first, dark and light mode.
   - Prompt box with a character limit (UI-enforced), model dropdown from GET /models, submit.
   - Streaming answer display.
   - Metric cards: tokens, cost, latency, time to first token, energy, carbon, water.
   - Equivalents row with friendly wording.
   - Loading, empty, and error states. Clear messages for spend-cap and rate-limit 429s.
   - Short "how are these estimated?" link to a methodology page (stub is fine).
3. API URL via NEXT_PUBLIC env var. Update CORS in CDK to the Vercel URL. Show `cdk diff`, wait for OK.
4. Tests: a few component tests and one Playwright smoke test (optional if time is short).
5. Deploy to Vercel (root directory: frontend). Walk me through each dashboard step. I click, you guide.
6. Accessibility basics (labels, contrast, keyboard) and Lighthouse mobile check.
7. Update docs, ADR for frontend choices, learning notes.
