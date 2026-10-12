#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { ThirstyTokensStack } from '../lib/app-stack';

const app = new cdk.App();

// Org SCP only allows eu-north-1, so the region is pinned rather than read from the CLI profile.
const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-north-1' };

// The production frontend origin, passed as `-c corsOrigin=https://<project>.vercel.app`.
// localhost stays allowed for local development.
const corsOrigin = app.node.tryGetContext('corsOrigin') as string | undefined;
if (corsOrigin !== undefined && !/^https:\/\/[^/\s]+$/.test(corsOrigin)) {
  throw new Error(
    `corsOrigin must be an https origin without a path or trailing slash, got: ${corsOrigin}`,
  );
}
const corsOrigins = ['http://localhost:3000', ...(corsOrigin ? [corsOrigin] : [])];

new ThirstyTokensStack(app, 'ThirstyTokensStack', { env, corsOrigins });
