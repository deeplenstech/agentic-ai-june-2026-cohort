#!/usr/bin/env python
import os
import warnings
from contextlib import contextmanager

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
import uuid

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

TRACE_NAME = "employee-chatbot-turn"

langfuse = None
propagate_attributes = None

if os.getenv("LANGFUSE_PUBLIC_KEY"):
    # Set up Langfuse BEFORE crewai imports.
    # get_client() reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL, then
    # installs LangfuseSpanProcessor on the global tracer provider. That processor is what
    # stamps propagate_attributes() values (session id, user id) onto every span, including
    # the CrewAI and LiteLLM spans created by the instrumentors below. A raw OTLP exporter
    # cannot do this: nothing would read the propagated values out of the OTEL context.
    from langfuse import get_client, propagate_attributes

    langfuse = get_client()

    from openinference.instrumentation.crewai import CrewAIInstrumentor
    from openinference.instrumentation.litellm import LiteLLMInstrumentor

    # CrewAIInstrumentor wraps crew/agent/task/tool spans; LiteLLMInstrumentor
    # captures every LLM call (with token usage). Because get_llm() sets
    # is_litellm=True, all calls flow through litellm.completion, so the LiteLLM
    # spans nest correctly under the active agent span.
    CrewAIInstrumentor().instrument()
    LiteLLMInstrumentor().instrument()


# Imported after the Langfuse setup above: .memory pulls in bedrock_agentcore, which
# installs its own global TracerProvider on import. get_client() registers the Langfuse
# provider first, so bedrock's later call is the one OTEL refuses ("Overriding of current
# TracerProvider is not allowed") and our span processor stays active.
from .memory import MemoryUtils
from .session import Session
from .guardrailUtils import GuardrailBlockedError

# Also imported here (not at the top of the file) so crewai is not pulled in
# before get_client() has registered the Langfuse tracer provider above.
from crewai.flow.flow import Flow
import re

EMPLOYEE_ID_PATTERN = re.compile(
    r"[a-zA-Z0-9][a-zA-Z0-9-_/]*(?::[a-zA-Z0-9-_/]+)*[a-zA-Z0-9-_/]*"
)


@contextmanager
def trace_turn(session_id, employee_id, inputs):
    """Root Langfuse observation for one chat turn.

    propagate_attributes() must wrap the root span, not sit inside it. Only the active span
    and spans created after entering the context receive the attributes, so entering it first
    is what gets session id and user id onto the nested CrewAI and LiteLLM spans.

    Yields None when Langfuse is not configured, so the chatbot still runs without keys.
    """
    if langfuse is None:
        yield None
        return

    with propagate_attributes(
        session_id=session_id,
        user_id=employee_id,
        trace_name=TRACE_NAME,
        tags=["employee-chatbot"],
    ):
        with langfuse.start_as_current_observation(name=TRACE_NAME, input=inputs) as span:
            yield span


def run_turn(runnable, inputs):
    # Run one chat turn against a Crew or a Flow and return the response text.
    
    if isinstance(runnable, Flow):
        for field, value in inputs.items():
            setattr(runnable.state, field, value)
        runnable.state.final_response = ""
        runnable.kickoff()
        return runnable.state.final_response
    return runnable.kickoff(inputs=inputs).raw


def execute(factory):
    """Interactive CLI loop for one conversation, driven by a Crew or a Flow.

    Takes a factory (a createCrew function or a Flow class), not a built object.
    MemoryUtils needs the employee id and the session id, both of which are only
    known once this loop starts, and the agent modules need that MemoryUtils to
    register their hooks. So the factory is called here, after both ids exist.
    """
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    while True:
        employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
        if EMPLOYEE_ID_PATTERN.fullmatch(employee_id):
            break
        console.print("[bold red]Invalid Employee ID. Please try again.[/bold red]")
    Session().setEmployeeId(employee_id)

    # One CLI run is one conversation, so it maps to one Langfuse session. The same id is
    # already used as the AgentCore memory session.
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)

    # The factory registers its own hooks, memory included, so nothing is
    # registered here: a second memory hook would inject the history twice.
    runnable = factory(memoryUtils)

    while True:
        user_query = console.input("[bold yellow]User:[/bold yellow] ").strip()
        inputs = {
            "employee_id": employee_id,
            "employee_query": user_query
        }
        if user_query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        with trace_turn(session_id, employee_id, inputs) as span:
            try:
                response = run_turn(runnable, inputs)
                console.print("\n[bold green]Assitant:[/bold green]")
                console.print(Markdown(response))
                if span:
                    span.update(output=response)
                memoryUtils.saveMemory(userPrompt=user_query, assistantResponse=response)

            except GuardrailBlockedError as e:
                # e.blocked_message holds the guardrail's configured block text.
                console.print("\n[bold red]Assistant:[/bold red]")
                console.print(Markdown(e.blocked_message))
                console.print("\n" + "-"*50 + "\n")
            except Exception as e:
                if span:
                    span.update(level="ERROR", status_message=str(e))
                console.print(
                    "\n[bold red]Assitant: An exception occurred....[/bold red]"
                )
                console.print(Markdown(str(e)))
                raise Exception(f"An error occurred while running the crew: {e}")
            finally:
                if langfuse:
                    langfuse.flush()
