# Constraints

## AWS account
- Account is in an Idea Incubator org with a service control policy (SCP). **Only eu-north-1 works.** Other regions return an explicit SCP deny.
- $100 credit, expires 2 Apr 2027. No payment method on file, so the credit is a hard cap. Self-imposed cap: 50 EUR.
- AWS Budgets is unavailable. Spend control is the in-app daily cap (DynamoDB) plus a kill switch (Session 5).
- CLI profile: `thirsty` (IAM user `thirsty-admin`). CloudShell is available in the console.
- CDK is bootstrapped in eu-north-1.

## Bedrock models (EU inference profiles, all verified working in eu-north-1)
| Tier | Profile ID |
|---|---|
| small | eu.amazon.nova-micro-v1:0 |
| small | eu.amazon.nova-lite-v1:0 |
| medium | eu.amazon.nova-2-lite-v1:0 |
| medium | eu.amazon.nova-pro-v1:0 |
| large | eu.anthropic.claude-sonnet-4-6 |

Notes:
- Claude Haiku 4.5 was dropped: its AWS Marketplace subscription failed on first use and could not be recovered (it also did not appear under Marketplace subscriptions). Replaced by Nova 2 Lite.
- Anthropic models need two one-time steps per account before the app can call them: (1) the Anthropic use-case form (account-wide), then (2) a first successful invocation by a principal that has AWS Marketplace permissions (e.g. the admin role in the Bedrock playground). Do step 2 before the Lambda role calls the model, because a failed first attempt by the Lambda role (which has no Marketplace permissions) left the subscription stuck. Each Anthropic model is activated separately.
- `eu.anthropic.claude-sonnet-5-5` is not available to this account.
- EU profiles may route across several EU regions, so IAM must allow the underlying foundation-model ARNs in those regions. The SCP only affects calls made by this account's principals, not Bedrock's internal routing, but verify.
- LiteLLM may lack pricing for EU profile IDs. If so, keep a pricing table in `models.yaml` (per-million input and output token USD) and compute cost from tokens. Add a unit test.

## Footprint methodology (Session 2)
- Energy (Wh) = tokens x per-tier coefficient (Wh/token). Tiers are assumptions because closed models do not publish sizes.
- Carbon (gCO2e) = Wh x EU average grid intensity (not Sweden's, since routing may cross regions).
- Water (L) = Wh x water usage effectiveness constant.
- Verify every constant against current published sources (AWS, Epoch AI, EcoLogits docs) and cite them in the config file. Label outputs "estimates".

## Limits
- Max output tokens: 500 (server-side). Max input: enforced by the UI and re-checked server-side by character count.
- Daily spend cap default: $2. Per-IP daily request limit default: 30.

## Accounts and secrets
- GitHub (clintonhy@gmail.com), AWS and Langfuse and Vercel (clintonaitech@gmail.com).
- Langfuse keys are stored by the owner. Claude must never see them. Store in SSM Parameter Store via `aws ssm put-parameter` run by the owner.
