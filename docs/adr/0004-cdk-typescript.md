# ADR-0004: Write infrastructure in AWS CDK TypeScript

- Status: accepted
- Date: 2026-10-08

## Context
The initial scaffold assumed CDK in Python. CDK is TypeScript-first: construct libraries, docs and examples target it, and the CDK CLI is a Node tool already needed for `cdk synth`.

## Decision
Use CDK in TypeScript (strict) under `infra/`, with ESLint, Prettier and Jest.

## Consequences
The repo has two toolchains (uv for the backend, npm for infra), and CI needs a Node 24 job. Infra code gets first-class types and the most complete documentation.
