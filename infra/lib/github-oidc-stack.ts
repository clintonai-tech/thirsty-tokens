import * as cdk from 'aws-cdk-lib/core';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface GithubOidcStackProps extends cdk.StackProps {
  /** GitHub "owner/repo" allowed to assume the deploy role. */
  readonly repo: string;
  readonly branch?: string;
}

/**
 * GitHub Actions OIDC provider and deploy role. Deployed manually once by the owner;
 * the deploy workflow then uses short-lived credentials, never access keys.
 */
export class GithubOidcStack extends cdk.Stack {
  public readonly deployRole: iam.Role;

  constructor(scope: Construct, id: string, props: GithubOidcStackProps) {
    super(scope, id, props);
    const branch = props.branch ?? 'main';

    const provider = new iam.OidcProviderNative(this, 'GithubProvider', {
      url: 'https://token.actions.githubusercontent.com',
      clientIds: ['sts.amazonaws.com'],
    });

    this.deployRole = new iam.Role(this, 'DeployRole', {
      roleName: 'thirsty-tokens-github-deploy',
      maxSessionDuration: cdk.Duration.hours(1),
      // Trust: this repo, main branch only. Pull requests and forks cannot assume it.
      assumedBy: new iam.WebIdentityPrincipal(provider.oidcProviderArn, {
        StringEquals: {
          'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com',
          'token.actions.githubusercontent.com:sub': `repo:${props.repo}:ref:refs/heads/${branch}`,
        },
      }),
    });

    // `cdk deploy` does its work through the roles created by `cdk bootstrap`
    // (deploy, file/image publishing, lookup). This role may only assume those.
    this.deployRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ['sts:AssumeRole'],
        resources: [
          `arn:${this.partition}:iam::${this.account}:role/cdk-hnb659fds-*-${this.account}-${this.region}`,
        ],
      }),
    );

    new cdk.CfnOutput(this, 'DeployRoleArn', { value: this.deployRole.roleArn });
  }
}
