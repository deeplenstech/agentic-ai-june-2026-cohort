import os
import subprocess
from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import (
    aws_bedrockagentcore as agentcore,
)
from aws_cdk import (
    aws_ecr_assets as ecr_assets,
)
from aws_cdk import (
    aws_iam as iam,
)
from constructs import Construct

# Load TAVILY_API_KEY from 1.stockresearch/.env if the file exists, else blank.
_env_file = Path(__file__).parent / ".." / ".." / "session2" / "1.stockresearch" / ".env"
_tavily_api_key = ""
try:
    for _line in _env_file.read_text().splitlines():
        if _line.startswith("TAVILY_API_KEY="):
            _tavily_api_key = _line.split("=", 1)[1].strip().strip('"').strip("'")
            break
except FileNotFoundError:
    pass


class AgentCoreStack(Stack):
    """Deploys the Stock Research agent on Amazon Bedrock AgentCore Runtime.

    Uses the L2 ``Runtime`` construct (same approach as the TypeScript stack): it
    builds the ARM64 container from 1.stockresearch/Dockerfile, pushes it to a
    CDK-managed ECR, and auto-provisions the execution role with the baseline
    permissions (CloudWatch logs, ECR pull, X-Ray tracing). The only policy we add
    by hand is Bedrock model invoke -- everything else is handled by the construct.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Refresh requirements.txt for the Docker build before bundling the asset.
        subprocess.run(["sh", "generateRequirements.sh"], check=True, cwd=".")

        # Container image -- built from 1.stockresearch/Dockerfile, pushed to ECR, ARM64
        # (AgentCore Runtime requires linux/arm64).
        artifact = agentcore.AgentRuntimeArtifact.from_asset(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "session2", "1.stockresearch"),
            platform=ecr_assets.Platform.LINUX_ARM64,
            asset_name="stockresearchimages",
        )

        # The AgentCore Runtime. The L2 construct creates the execution role and
        # grants the baseline logs / ECR / X-Ray permissions itself, so we don't
        # hand-roll any of that boilerplate.
        runtime = agentcore.Runtime(
            self,
            "StockResearchAgent",
            runtime_name="stock_research_agent_june",
            description="Stock Research agent with IAM authentication",
            agent_runtime_artifact=artifact,
            protocol_configuration=agentcore.ProtocolType.HTTP,
            network_configuration=agentcore.RuntimeNetworkConfiguration.using_public_network(),
            tracing_enabled=True,
            environment_variables={
                "AWS_REGION": self.region,
                "AWS_DEFAULT_REGION": self.region,
                "CREWAI_DISABLE_TELEMETRY": "true",
                "LITELLM_LOCAL_MODEL_COST_MAP": "true",
                "OTEL_TRACES_SAMPLER": "always_on",
                "OTEL_LOG_LEVEL": "debug",
                "TAVILY_API_KEY": _tavily_api_key,
                "MODEL_ID": "bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0",
            },
        )

        # The one permission that isn't baseline: invoke the Bedrock model. The
        # cross-region inference profile (us.anthropic.*) fans out to foundation
        # models in multiple regions, so allow both resource shapes.
        runtime.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:*:{self.account}:inference-profile/*",
                ],
            )
        )

        # Outputs used by the invoke scripts and the README walkthrough.
        CfnOutput(
            self,
            "RuntimeArn",
            value=runtime.agent_runtime_arn,
            description="ARN of the AgentCore Runtime",
            export_name="AgentCoreRuntimeArn",
        )
        CfnOutput(
            self,
            "RuntimeId",
            value=runtime.agent_runtime_id,
            description="ID of the AgentCore Runtime",
        )
        CfnOutput(
            self,
            "RoleArn",
            value=runtime.role.role_arn,
            description="ARN of the AgentCore Execution Role",
        )
