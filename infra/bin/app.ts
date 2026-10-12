#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { ThirstyTokensStack } from '../lib/app-stack';

const app = new cdk.App();

// Org SCP only allows eu-north-1, so the region is pinned rather than read from the CLI profile.
const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-north-1' };

// Origins allowed to call the function URL: the production frontend, plus localhost for
// development. `-c corsOrigin=https://...` replaces the production origin (e.g. a custom domain).
const PRODUCTION_ORIGIN = 'https://thirsty-tokens-frontend.vercel.app';
const corsOrigin =
  (app.node.tryGetContext('corsOrigin') as string | undefined) ?? PRODUCTION_ORIGIN;
if (!/^https:\/\/[^/\s]+$/.test(corsOrigin)) {
  throw new Error(
    `corsOrigin must be an https origin without a path or trailing slash, got: ${corsOrigin}`,
  );
}
const corsOrigins = ['http://localhost:3000', corsOrigin];

new ThirstyTokensStack(app, 'ThirstyTokensStack', { env, corsOrigins });
