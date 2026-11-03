# Learning notes

## Session 1: Foundations
- **LiteLLM already prices the EU inference profiles.** `litellm.cost_per_token("bedrock/eu.*")` returned values for all five (EU prices sit about 10% above US ones). So no pricing table was needed; `pricing` in `models.yaml` is only an override. Check before building a fallback.
- **EU inference profiles need two IAM resources.** Bedrock authorises the inference profile (our region and account) and the foundation model it routes to (any EU region). The foundation-model statement uses `eu-*` plus a `bedrock:InferenceProfileArn` condition, so the model can't be invoked directly.
- **Single source of truth for models.** CDK reads `backend/models.yaml` to build the IAM ARNs, so adding a model never means editing infra code by hand.
- **Lambda Web Adapter** lets the same FastAPI image run locally and on Lambda. Streaming needs both `AWS_LWA_INVOKE_MODE=response_stream` and the function URL `RESPONSE_STREAM` invoke mode.
- **The org SCP denies `iam:CreateOpenIDConnectProvider`**, so GitHub OIDC (and push-to-deploy) is not possible in this account. Deploys are manual: `cdk diff`, review, `cdk deploy` (ADR-0006). A first-time stack that fails rolls back to `ROLLBACK_COMPLETE` and must be destroyed before redeploying.
- **TypeScript 7 vs typescript-eslint.** `cdk init` generated TS 7, but typescript-eslint only supports `<6.1`, so infra is pinned to `~6.0`.
- Building the Lambda image on an arm64 Mac is native; CI uses an arm64 runner for the same reason.
- **Anthropic on Bedrock needs two one-time steps**: the account-wide use-case form, then a first invocation by a role that has `aws-marketplace:Subscribe`/`ViewSubscriptions`. Each model subscribes separately, and a failed first attempt (ours came from the least-privilege Lambda role) can leave it stuck. Activate new Claude models from the Bedrock playground as an admin before the app calls them. Amazon (Nova) models need neither.
- **Check pricing at a realistic request size.** LiteLLM's cost map has long-context tiers (`*_above_200k_tokens`); a 1M-token probe showed Sonnet 4.5 at double the real price for our small requests.
- **Cold start is dominated by `import litellm`** (about 1.5s at full CPU, loading ~1,000 modules whatever submodule you import) on a 512MB Lambda; the 10s init limit was exceeded, so Lambda retried init inside the first request (~25s). Accepted for now; options are more memory, lazy import, or direct boto3 (would need an ADR).
- **Errors from Bedrock are mapped to 4xx/5xx with safe messages** (`errors.py`); the raw error stays in CloudWatch.

## Session 2: Backend core
- **Reserve-then-settle beats check-then-add.** A conditional `ADD` on the counter is atomic, so concurrent requests cannot jointly overshoot the cap (ADR-0007). Atomicity rests on DynamoDB's conditional-write guarantee; a threaded test against moto was removed because moto is not atomic across threads (it let 11 of 10 through in CI), so it tested the fake, not our code. Sequential boundary tests cover the cap logic.
- **Edge cases show up in tests of the wrapper, not the unit.** `limit=0` let the first request through because the DynamoDB condition `attribute_not_exists(hits)` is true on a fresh item. Found by an API-level test, fixed in the repository.
- **Open the stream and read the first chunk before returning `StreamingResponse`.** Once the response starts, the status is already 200. Pre-reading means Bedrock failures (access denied, throttling) still return real 4xx/5xx; only mid-stream failures become `error` events.
- **Client IP comes from `x-amzn-request-context`** (set by Lambda Web Adapter from the function URL event), not `X-Forwarded-For`. A test proves a spoofed forwarded header gets no fresh quota. Confirmed on the deployed URL: a request sent with fake `X-Forwarded-For: 7.7.7.7` and `x-amzn-request-context` (sourceIp 9.9.9.9) was counted under the real caller's hash, and neither fake hash appears in DynamoDB.
- **Sources for footprint are thin and disagree by up to 5x** (Epoch ~0.0006 Wh/token vs ~0.003 for Claude in arXiv 2505.09598). Coefficients are tier assumptions, documented in ADR-0008. AWS reports on-site WUE only; the off-site water factor is US-weighted.
- **One cost path.** `/chat` and `/chat/stream` both price through `estimate_cost` (models.yaml override, else `litellm.cost_per_token`), which also prices the worst case for the reservation. `completion_cost` was dropped because it needs a full response object, which a stream does not provide.

## Session 3: Frontend
- **CORS is not a security control.** It only tells browsers which sites may read a response; `curl` ignores it, and the function URL is public anyway. What protects the budget is the spend cap, the per-IP limit and the server-side token cap. The origin is a constant in `infra/bin/app.ts` so a plain deploy keeps it (ADR-0009).
- **`EventSource` cannot POST**, so streaming uses `fetch` plus a reader and a small pure SSE parser, tested with events split across chunks.
- **Tests catch formatting bugs early**: a `trim` helper that stripped trailing zeros turned "150" into "15"; a unit test found it before users did.
- **Check what generators install.** `shadcn init` added a stray npm package named `cn` (the import should be `@/lib/utils`) and the whole shadcn CLI as a runtime dependency. The CLI dragged in most of the production audit findings; removing it left 0.
- **Moto is not thread-safe**, so a 16-thread test against it flaked (11 of 10 reservations) and tested the fake, not our code. Dropped; atomicity is DynamoDB's conditional-write guarantee.
- **Vercel gotchas**: production builds `main`, so the first deploy 404s until the frontend is merged; "Git information retrieval failed" was GitHub's secondary rate limit (wait, redeploy); a 404 `NOT_FOUND` on a "Ready" deployment points at framework preset or root directory.
- **Model output is untrusted.** Answers are rendered with `react-markdown`, which ignores raw HTML; a test checks a `<script>` tag does not render. Jest needs the ESM-only markdown packages transformed.
- **Dependencies age in weeks.** Next 16.4.0 gained critical advisories between sessions; `npm audit --omit=dev` is a cheap check before each session.
- **Cold start is user-visible**: after weeks idle the first call returned 502 then took 18s. The client retries once on 502/503/504. A real fix (lazy `litellm` import or more memory) is Session 5.
