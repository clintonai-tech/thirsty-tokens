# ADR-0006: Manual deploys; no GitHub OIDC

- Status: accepted
- Date: 2026-10-09

## Context
The plan was a GitHub OIDC provider and deploy role so Actions could run `cdk deploy`. Creating the provider failed with an explicit deny from the org SCP (`iam:CreateOpenIDConnectProvider`). Access keys in GitHub are not acceptable. The owner also prefers to review `cdk diff` before every deploy.

## Decision
Remove the OIDC stack and the deploy workflow. CI runs checks only (backend lint, types, tests; infra lint, tests, synth). The owner deploys manually with `cdk diff` followed by `cdk deploy`.

## Consequences
No push-to-deploy, but every change is reviewed by a human before it reaches AWS. Revisit if the SCP is relaxed.
