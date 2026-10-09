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
- **Reserve-then-settle beats check-then-add.** A conditional `ADD` on the counter is atomic, so concurrent requests cannot jointly overshoot the cap (ADR-0007). A 16-thread test against moto proves exactly cap/amount reservations succeed.
- **Edge cases show up in tests of the wrapper, not the unit.** `limit=0` let the first request through because the DynamoDB condition `attribute_not_exists(hits)` is true on a fresh item. Found by an API-level test, fixed in the repository.
- **Open the stream and read the first chunk before returning `StreamingResponse`.** Once the response starts, the status is already 200. Pre-reading means Bedrock failures (access denied, throttling) still return real 4xx/5xx; only mid-stream failures become `error` events.
- **Client IP comes from `x-amzn-request-context`** (set by Lambda Web Adapter from the function URL event), not `X-Forwarded-For`. A test proves a spoofed forwarded header gets no fresh quota. Still to confirm on the deployed URL that a client-sent `x-amzn-request-context` is overwritten by the adapter.
- **Sources for footprint are thin and disagree by up to 5x** (Epoch ~0.0006 Wh/token vs ~0.003 for Claude in arXiv 2505.09598). Coefficients are tier assumptions, documented in ADR-0008. AWS reports on-site WUE only; the off-site water factor is US-weighted.
- **One cost path.** `/chat` and `/chat/stream` both price through `estimate_cost` (models.yaml override, else `litellm.cost_per_token`), which also prices the worst case for the reservation. `completion_cost` was dropped because it needs a full response object, which a stream does not provide.
