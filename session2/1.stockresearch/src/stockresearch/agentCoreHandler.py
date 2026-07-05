import os

from bedrock_agentcore import BedrockAgentCoreApp
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor

# Attach the OpenInference instrumentors to the global TracerProvider that
# `opentelemetry-instrument` (see Dockerfile CMD) has already configured to
# export to CloudWatch. We deliberately do NOT call set_tracer_provider here:
# doing so would replace the ADOT provider and the crew's LLM/tool/agent spans
# would never reach CloudWatch. These calls are what produce the child spans
# (agent delegations, LiteLLM completions, tool calls) under the runtime span.
CrewAIInstrumentor().instrument()
LiteLLMInstrumentor().instrument()

from .crew_v3 import crew

# Create AgentCore App
app = BedrockAgentCoreApp()

# Print env vars to stdout for CloudWatch diagnostics
print("ENV VARS:", {k: v for k, v in os.environ.items()}, flush=True)


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")

    if not prompt:
        raise ValueError("Missing required payload parameters")

    inputs = {"user_query": prompt}

    try:
        # Trigger the Crew
        response = crew.kickoff(inputs=inputs).raw
    except Exception:
        response = "An unknown error occurred while processing your request."

    return response


if __name__ == "__main__":
    app.run()
