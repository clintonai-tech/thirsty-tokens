# Learning notes

## Session 1: Foundations
- **LiteLLM already prices the EU inference profiles.** `litellm.cost_per_token("bedrock/eu.*")` returned values for all five (EU prices sit about 10% above US ones). So no pricing table was needed; `pricing` in `models.yaml` is only an override. Check before building a fallback.
- **EU inference profiles need two IAM resources.** Bedrock authorises the inference profile (our region and account) and the foundation model it routes to (any EU region). The foundation-model statement uses `eu-*` plus a `bedrock:InferenceProfileArn` condition, so the model can't be invoked directly.
- **Single source of truth for models.** CDK reads `backend/models.yaml` to build the IAM ARNs, so adding a model never means editing infra code by hand.
- **Lambda Web Adapter** lets the same FastAPI image run locally and on Lambda. Streaming needs both `AWS_LWA_INVOKE_MODE=response_stream` and the function URL `RESPONSE_STREAM` invoke mode.
- **The org SCP denies `iam:CreateOpenIDConnectProvider`**, so GitHub OIDC (and push-to-deploy) is not possible in this account. Deploys are manual: `cdk diff`, review, `cdk deploy` (ADR-0006). A first-time stack that fails rolls back to `ROLLBACK_COMPLETE` and must be destroyed before redeploying.
- **TypeScript 7 vs typescript-eslint.** `cdk init` generated TS 7, but typescript-eslint only supports `<6.1`, so infra is pinned to `~6.0`.
- Building the Lambda image on an arm64 Mac is native; CI uses an arm64 runner for the same reason.
