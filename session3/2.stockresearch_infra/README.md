# Stock Research — CDK Infrastructure

## Purpose

This folder contains the AWS CDK infrastructure for deploying the [Stock Research agent](../../session2/1.stockresearch/) to **Amazon Bedrock AgentCore Runtime**.

It provisions all the cloud resources needed to run the agent as a containerised, serverless endpoint on AWS:

- Builds a Docker image from the `session2/1.stockresearch` source directory and pushes it to **Amazon ECR**
- Creates an **IAM execution role** with the permissions the runtime needs (Bedrock, ECR, CloudWatch, X-Ray)
- Deploys an **Amazon Bedrock AgentCore Runtime** that serves the agent over a public network endpoint

## Architecture

```
session2/1.stockresearch/   ← agent source code
        │
        ▼
  Docker build (via CDK asset)
        │
        ▼
  Amazon ECR repository   ← stores the container image
        │
        ▼
  Bedrock AgentCore Runtime  (stock_research_agent_june)
        │  IAM execution role with permissions for:
        │    • Bedrock model invocation
        │    • ECR image pull
        │    • CloudWatch Logs & Metrics
        │    • X-Ray tracing
```

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) configured with credentials
- [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) installed (`npm install -g aws-cdk`)
- Python ≥ 3.11
- [UV](https://docs.astral.sh/uv/) (used to generate `requirements.txt` before the Docker build)
- Docker running locally (CDK uses it to build the container image)

## Installation

Install Python dependencies:

```bash
uv sync
```

## Configuration

The stack reads `TAVILY_API_KEY` directly from the sibling project's `.env` file at `../../session2/1.stockresearch/.env`. Make sure that file exists and contains the key before deploying:

```env
TAVILY_API_KEY=your_tavily_api_key
```

The container is configured to use the following model by default (set in `src/AgentCoreStack.py`):

```
MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0
```

## Deploying

### 1. Bootstrap (first time only)

CDK bootstrap provisions S3 and ECR assets in your AWS account. Run once per account/region:

```bash
uv run cdk bootstrap
```

### 2. Synthesize (optional — preview CloudFormation template)

```bash
uv run cdk synth
```

### 3. Deploy

```bash
uv run cdk deploy
```

CDK will:
1. Run `generateRequirements.sh` to freeze `uv` dependencies into `requirements.txt`
2. Build the Docker image from `../../session2/1.stockresearch/`
3. Push it to ECR
4. Create the IAM execution role and attach the required policy
5. Deploy the Bedrock AgentCore Runtime

On success, the following outputs are printed:

| Output | Description |
|--------|-------------|
| `RuntimeArn` | ARN of the deployed AgentCore Runtime (also exported as `AgentCoreRuntimeArn` for cross-stack use) |
| `RuntimeId` | ID of the AgentCore Runtime |
| `RoleArn` | ARN of the IAM execution role |

## Invoking the Deployed Agent

Once deployed, you can invoke the agent directly via the AWS CLI or the Boto3 SDK. The agent accepts a JSON payload with a `prompt` key (see [agentCoreHandler.py](../../session2/1.stockresearch/src/stockresearch/agentCoreHandler.py)).

### AWS CLI

Replace `<RUNTIME_ARN>` with the `RuntimeArn` output from the deploy step:

```bash
aws bedrock-agentcore invoke-agent-runtime \
  --agent-runtime-arn <RUNTIME_ARN> \
  --payload '{"prompt": "What is the current stock price of Apple?"}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  out.txt

# The response is streamed into out.txt — view it with:
cat out.txt
```

> **Note:** `--cli-binary-format raw-in-base64-out` is required because the AWS CLI v2 treats `--payload` as base64-encoded by default. Without it you'll get an `Invalid base64` error.

### Python (Boto3)

Replace `<RUNTIME_ARN>` with the `RuntimeArn` output from the deploy step:

```python
import boto3
import json

client = boto3.client("bedrock-agentcore", region_name="us-east-1")

response = client.invoke_agent_runtime(
    agentRuntimeArn="<RUNTIME_ARN>",
    payload=json.dumps({"prompt": "Compare Google and Microsoft stock performance this month."}),
)

# The response body is a streaming blob — read and decode it
print(response["response"].read().decode())
```

### What to Expect

The agent runs the full CrewAI pipeline inside the container — searching the web, analyzing data, and returning a structured research report as a string. Cold starts (first invocation after a period of inactivity) may take 30–60 seconds.

## Checking Logs

The runtime streams container `stdout`/`stderr` (including the CrewAI pipeline output and the `ENV VARS:` diagnostics printed by [agentCoreHandler.py](../../session2/1.stockresearch/src/stockresearch/agentCoreHandler.py)) to **Amazon CloudWatch Logs**. Because `tracing_enabled=True` in the stack, traces are also available in the **CloudWatch GenAI Observability / X-Ray** console.

The runtime log group follows the pattern `/aws/bedrock-agentcore/runtimes/<RUNTIME_ID>-DEFAULT`, where `<RUNTIME_ID>` is the `RuntimeId` output from the deploy step.

### Find the log group

```bash
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/bedrock-agentcore/runtimes/" \
  --region us-east-1 \
  --query "logGroups[].logGroupName" --output text
```

### Tail logs live

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/<RUNTIME_ID>-DEFAULT \
  --region us-east-1 \
  --follow --since 15m
```

Drop `--follow` for a one-off dump, and adjust `--since` (e.g. `1h`, `2026-07-03T10:00:00`) to widen the window. You can also browse the same logs and traces visually under **CloudWatch → Log groups** and **CloudWatch → GenAI Observability** in the AWS Console.

## Updating the Agent

After changing the agent code in `../../session2/1.stockresearch/`, re-deploy with:

```bash
uv run cdk deploy
```

CDK detects the changed Docker asset, rebuilds and pushes a new image, and updates the runtime.

## Tearing Down

To destroy all resources created by this stack (AgentCore Runtime, IAM role, ECR repository):

```bash
uv run cdk destroy
```

You will be prompted to confirm. This is **irreversible** — the ECR repository and all pushed images will be deleted.

> **Note:** The ECR repository may retain images if the CDK asset removal policy is set to `RETAIN`. Check the ECR console and delete the repository manually if needed.

## Stack Details

- **Stack name:** `StockResearchAgent` (set in [app.py](app.py))
- **Stack file:** [src/AgentCoreStack.py](src/AgentCoreStack.py)
- **Entry point:** [app.py](app.py)
- **CDK config:** [cdk.json](cdk.json)
- **Agent source:** [../../session2/1.stockresearch/](../../session2/1.stockresearch/)
- **Network mode:** Public
- **Agent name in Bedrock:** `stock_research_agent_june`
