# Session 4: Compare mode, benchmark, chart

Read CLAUDE.md, docs/PLAN.md, docs/CONSTRAINTS.md, docs/learning-notes.md. Plan first, wait for approval.

## Tasks
1. Compare mode (2 models): backend endpoint runs both calls in parallel, with the spend cap checking the combined worst-case cost. Frontend shows two columns on desktop and stacked cards on mobile, with a delta summary (cheaper, faster, greener).
2. Offline benchmark (scripts/benchmark/), no LLM judge, no quality scoring:
   - 20 fixed prompts across categories (reasoning, summarization, coding, writing, factual), stored in a versioned file.
   - Run all 5 models with identical prompts and the server-side max output tokens. Record input/output tokens, cost, latency, time to first token, and footprint (reuse the production footprint module).
   - Print the estimated total cost before running and ask me to confirm. Target well under 1 EUR.
   - Output benchmark-results.json, committed to the repo and loaded by the frontend as a static file.
3. Chart: cost vs energy scatter (bubble size = latency, color = tier). Tooltips, mobile-friendly. Deterministic callouts for cheapest, fastest, and greenest model, computed in a pure function.
4. State the limitation in the UI and README: the chart compares cost, speed, and footprint, not answer quality.
5. Tests for the aggregation and callout logic.
6. Update docs, ADR for the benchmark design (why no judge), learning notes.
