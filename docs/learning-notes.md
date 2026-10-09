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
