import * as path from 'node:path';
import * as cdk from 'aws-cdk-lib/core';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ecr_assets from 'aws-cdk-lib/aws-ecr-assets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { loadBedrockModels, BedrockModel } from './models';

export interface AppStackProps extends cdk.StackProps {
  /** Overridable for tests; defaults to backend/models.yaml. */
  readonly models?: BedrockModel[];
  /** Placeholder until the Vercel domain exists. */
  readonly corsOrigins?: string[];
}

export class ThirstyTokensStack extends cdk.Stack {
  public readonly table: dynamodb.Table;
  public readonly fn: lambda.DockerImageFunction;

  constructor(scope: Construct, id: string, props: AppStackProps = {}) {
    super(scope, id, props);
    const models = props.models ?? loadBedrockModels();

    // Spend cap and rate-limit counters (Session 2). On-demand, so zero idle cost.
    this.table = new dynamodb.Table(this, 'Table', {
      partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'sk', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const logGroup = new logs.LogGroup(this, 'LogGroup', {
      retention: logs.RetentionDays.TWO_WEEKS,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    this.fn = new lambda.DockerImageFunction(this, 'Api', {
      // Build context is the repo root because pyproject.toml and uv.lock live there.
      code: lambda.DockerImageCode.fromImageAsset(path.resolve(__dirname, '../..'), {
        file: 'backend/Dockerfile',
        platform: ecr_assets.Platform.LINUX_ARM64,
      }),
      architecture: lambda.Architecture.ARM_64,
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      logGroup,
      environment: {
        // Lambda Web Adapter: enable response streaming for Session 2.
        AWS_LWA_INVOKE_MODE: 'response_stream',
        TT_AWS_REGION: 'eu-north-1',
        TABLE_NAME: this.table.tableName,
        HOME: '/tmp',
      },
    });

    // Bedrock invoke permissions, scoped to the registry models only.
    //
    // The EU inference profiles (eu.*) route a request to a foundation model in any EU region
    // the profile covers. Bedrock authorises both resources, so we need:
    //   1. the inference profile itself, in our region and account, and
    //   2. the underlying foundation model, in any EU region, but only when the call arrives
    //      through one of our profiles (bedrock:InferenceProfileArn condition). That blocks
    //      calling the foundation model directly in other regions.
    const profileArns = models.map(
      (m) =>
        `arn:${this.partition}:bedrock:${this.region}:${this.account}:inference-profile/${m.profileId}`,
    );
    const foundationModelArns = models.map(
      (m) => `arn:${this.partition}:bedrock:eu-*::foundation-model/${m.foundationModelId}`,
    );
    const actions = ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'];
    this.fn.addToRolePolicy(new iam.PolicyStatement({ actions, resources: profileArns }));
    this.fn.addToRolePolicy(
      new iam.PolicyStatement({
        actions,
        resources: foundationModelArns,
        conditions: { StringLike: { 'bedrock:InferenceProfileArn': profileArns } },
      }),
    );

    this.table.grantReadWriteData(this.fn);

    const url = this.fn.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
      invokeMode: lambda.InvokeMode.RESPONSE_STREAM,
      cors: {
        allowedOrigins: props.corsOrigins ?? ['http://localhost:3000'],
        allowedMethods: [lambda.HttpMethod.GET, lambda.HttpMethod.POST],
        allowedHeaders: ['content-type'],
      },
    });

    new cdk.CfnOutput(this, 'FunctionUrl', { value: url.url });
    new cdk.CfnOutput(this, 'TableName', { value: this.table.tableName });
  }
}
