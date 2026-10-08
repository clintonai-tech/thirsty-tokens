#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { ThirstyTokensStack } from '../lib/app-stack';

const app = new cdk.App();

// Org SCP only allows eu-north-1, so the region is pinned rather than read from the CLI profile.
const env = { account: process.env.CDK_DEFAULT_ACCOUNT, region: 'eu-north-1' };

new ThirstyTokensStack(app, 'ThirstyTokensStack', { env });
