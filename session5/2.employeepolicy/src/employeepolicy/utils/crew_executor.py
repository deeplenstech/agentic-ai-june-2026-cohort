#!/usr/bin/env python
import base64
import os
import warnings

from dotenv import load_dotenv
from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from rich.console import Console
from rich.markdown import Markdown
from .memory import MemoryUtils
from .session import Session
import uuid
from .llm_hooks import LLMHooks

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

if os.getenv("LANGFUSE_PUBLIC_KEY"):
    # Set up OTEL -> Langfuse exporter BEFORE crewai imports
    langfuse_public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
    langfuse_secret_key = os.environ["LANGFUSE_SECRET_KEY"]
    langfuse_host = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")
    auth_header = base64.b64encode(
        f"{langfuse_public_key}:{langfuse_secret_key}".encode()
    ).decode()

    exporter = OTLPSpanExporter(
        endpoint=f"{langfuse_host}/api/public/otel/v1/traces",
        headers={
            "Authorization": f"Basic {auth_header}",
            "x-langfuse-ingestion-version": "4"
        }
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    otel_trace.set_tracer_provider(provider)

    from openinference.instrumentation.crewai import CrewAIInstrumentor
    from openinference.instrumentation.litellm import LiteLLMInstrumentor

    # CrewAIInstrumentor wraps crew/agent/task/tool spans; LiteLLMInstrumentor
    # captures every LLM call (with token usage). Because get_llm() sets
    # is_litellm=True, all calls flow through litellm.completion, so the LiteLLM
    # spans nest correctly under the active agent span.
    CrewAIInstrumentor().instrument()
    LiteLLMInstrumentor().instrument()


def execute_crew(crew):
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
    Session().setEmployeeId(employee_id)
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)
    LLMHooks(memoryUtils).register()

    tracer = otel_trace.get_tracer("employee_policy")
    while True:
        user_query = console.input("[bold yellow]User:[/bold yellow] ").strip()
        inputs = {"user_query": user_query}
        if user_query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        with tracer.start_as_current_span("employee_policy") as span:
            try:
                span.set_attribute("input", str(inputs))
                response = crew.kickoff(inputs=inputs).raw
                console.print("\n[bold green]Assitant:[/bold green]")
                console.print(Markdown(response))
                span.set_attribute("output", str(response or ""))
                memoryUtils.saveMemory(userPrompt=user_query, assistantResponse=response)

            except Exception as e:
                span.record_exception(e)
                console.print(
                    "\n[bold green]Assitant: An exception occurred....[/bold green]"
                )
                console.print(Markdown(str(e)))
                raise Exception(f"An error occurred while running the crew: {e}")
            finally:
                provider.force_flush()
