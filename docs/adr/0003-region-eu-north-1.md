# ADR-0003: Deploy everything in eu-north-1

- Status: accepted
- Date: 2026-10-08

## Context
The AWS account sits in an org with a service control policy that denies every region except eu-north-1. Bedrock EU inference profiles are available there.

## Decision
All stacks, the Lambda, DynamoDB and Bedrock calls use eu-north-1. The region is pinned in the CDK app environment and the backend config.

## Consequences
No multi-region setups. EU inference profiles may route across EU regions internally, so IAM must allow the underlying foundation-model ARNs. If an SCP denies an action we stop and report it instead of working around it.
