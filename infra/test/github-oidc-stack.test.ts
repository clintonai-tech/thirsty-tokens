import * as cdk from 'aws-cdk-lib/core';
import { Match, Template } from 'aws-cdk-lib/assertions';
import { GithubOidcStack } from '../lib/github-oidc-stack';

const stack = new GithubOidcStack(new cdk.App(), 'OidcTest', {
  env: { account: '123456789012', region: 'eu-north-1' },
  repo: 'owner/repo',
});
const template = Template.fromStack(stack);

test('creates the GitHub OIDC provider', () => {
  template.hasResourceProperties('AWS::IAM::OIDCProvider', {
    Url: 'https://token.actions.githubusercontent.com',
    ClientIdList: ['sts.amazonaws.com'],
  });
});

test('trust is limited to the repo main branch', () => {
  template.hasResourceProperties('AWS::IAM::Role', {
    AssumeRolePolicyDocument: {
      Statement: [
        Match.objectLike({
          Action: 'sts:AssumeRoleWithWebIdentity',
          Condition: {
            StringEquals: {
              'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
              'token.actions.githubusercontent.com:sub': 'repo:owner/repo:ref:refs/heads/main',
            },
          },
        }),
      ],
    },
  });
});

test('role can only assume the CDK bootstrap roles', () => {
  const policies = JSON.stringify(template.findResources('AWS::IAM::Policy'));
  expect(policies).toContain('sts:AssumeRole');
  expect(policies).toContain('role/cdk-hnb659fds-*-123456789012-eu-north-1');
  expect(policies).not.toContain('"Resource":"*"');
});
