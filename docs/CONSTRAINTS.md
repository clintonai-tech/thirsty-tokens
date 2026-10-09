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

## Footprint methodology (Session 2, done)
- Energy (Wh) = Wh per output token by tier x (output tokens + 0.1 x input tokens). Tiers are assumptions because closed models do not publish sizes.
- Carbon (gCO2e) = kWh x 211.2 g/kWh (EU-27 average 2024, not Sweden's, since routing may cross regions).
- Water (L) = kWh x 5.29 L/kWh (on-site 0.18 + off-site 5.11).
- Values, sources and retrieval dates are in `backend/src/thirsty_tokens/footprint/coefficients.py`; rationale in ADR-0008. All outputs are labelled "estimates".

## Limits
- Max output tokens: 500 (server-side). Max input: enforced by the UI and re-checked server-side by character count.
- Daily spend cap default: $2 (`TT_DAILY_SPEND_CAP_USD`). Per-IP daily request limit default: 30 (`TT_DAILY_REQUEST_LIMIT`). Both reset at UTC midnight (ADR-0007).

## Accounts and secrets
- GitHub (clintonhy@gmail.com), AWS and Langfuse and Vercel (clintonaitech@gmail.com).
- Langfuse keys are stored by the owner. Claude must never see them. Store in SSM Parameter Store via `aws ssm put-parameter` run by the owner.
