import * as cdk from 'aws-cdk-lib/core';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { ThirstyTokensStack } from '../lib/app-stack';
import { loadBedrockModels } from '../lib/models';

const models = loadBedrockModels();
const app = new cdk.App();
const stack = new ThirstyTokensStack(app, 'TestStack', {
  env: { account: '123456789012', region: 'eu-north-1' },
});
const template = Template.fromStack(stack);

test('registry yields the five EU profiles and their foundation models', () => {
  expect(models).toHaveLength(5);
  expect(models.map((m) => m.profileId)).toContain('eu.anthropic.claude-sonnet-4-6');
  expect(models.map((m) => m.foundationModelId)).toContain('amazon.nova-pro-v1:0');
});

test('table is on-demand with pk/sk, ttl and DESTROY', () => {
  template.hasResourceProperties('AWS::DynamoDB::Table', {
    BillingMode: 'PAY_PER_REQUEST',
    KeySchema: [
      { AttributeName: 'pk', KeyType: 'HASH' },
      { AttributeName: 'sk', KeyType: 'RANGE' },
    ],
    TimeToLiveSpecification: { AttributeName: 'ttl', Enabled: true },
  });
  template.hasResource('AWS::DynamoDB::Table', { DeletionPolicy: 'Delete' });
});

test('lambda is arm64 container image, 512MB, 30s, streaming env', () => {
  template.hasResourceProperties('AWS::Lambda::Function', {
    PackageType: 'Image',
    Architectures: ['arm64'],
    MemorySize: 512,
    Timeout: 30,
    Environment: {
      Variables: Match.objectLike({ AWS_LWA_INVOKE_MODE: 'response_stream' }),
    },
  });
});

test('limits are configured via env vars pointing at the table', () => {
  template.hasResourceProperties('AWS::Lambda::Function', {
    Environment: {
      Variables: Match.objectLike({
        TT_TABLE_NAME: { Ref: Match.stringLikeRegexp('^Table') },
        TT_DAILY_SPEND_CAP_USD: '2',
        TT_DAILY_REQUEST_LIMIT: '30',
      }),
    },
  });
});

test('limit settings can be overridden through props', () => {
  const custom = new ThirstyTokensStack(new cdk.App(), 'Custom', {
    env: { account: '123456789012', region: 'eu-north-1' },
    dailySpendCapUsd: 0.5,
    dailyRequestLimit: 5,
  });
  Template.fromStack(custom).hasResourceProperties('AWS::Lambda::Function', {
    Environment: {
      Variables: Match.objectLike({
        TT_DAILY_SPEND_CAP_USD: '0.5',
        TT_DAILY_REQUEST_LIMIT: '5',
      }),
    },
  });
});

test('log retention is 14 days', () => {
  template.hasResourceProperties('AWS::Logs::LogGroup', { RetentionInDays: 14 });
});

test('function URL streams and is CORS-restricted', () => {
  template.hasResourceProperties('AWS::Lambda::Url', {
    InvokeMode: 'RESPONSE_STREAM',
    Cors: Match.objectLike({ AllowOrigins: ['http://localhost:3000'] }),
  });
});

test('bedrock access is scoped: no wildcard resources, foundation models need our profiles', () => {
  const policies = template.findResources('AWS::IAM::Policy');
  const statements = Object.values(policies).flatMap(
    (p) =>
      (p as { Properties: { PolicyDocument: { Statement: unknown[] } } }).Properties.PolicyDocument
        .Statement,
  ) as { Action: string | string[]; Resource: unknown; Condition?: unknown }[];
  const bedrock = statements.filter((s) => JSON.stringify(s.Action).includes('bedrock:'));
  expect(bedrock).toHaveLength(2);
  for (const s of bedrock) {
    expect(JSON.stringify(s.Resource)).not.toBe('"*"');
    expect(JSON.stringify(s.Action)).not.toContain('bedrock:*');
  }
  const fm = bedrock.find((s) => JSON.stringify(s.Resource).includes('foundation-model'));
  expect(JSON.stringify(fm?.Condition)).toContain('bedrock:InferenceProfileArn');
});

test('dynamodb grant is limited to the one table', () => {
  const policies = JSON.stringify(template.findResources('AWS::IAM::Policy'));
  expect(policies).toContain('dynamodb:PutItem');
  expect(policies).not.toContain('dynamodb:*');
});
