#!/usr/bin/env python
import base64
import os
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from rich.console import Console
from rich.markdown import Markdown
import uuid
import re
from deepeval.integrations.crewai import instrument_crewai
from deepeval.tracing import trace, update_current_trace

instrument_crewai()

EMPLOYEE_ID_PATTERN = re.compile(
    r"[a-zA-Z0-9][a-zA-Z0-9-_/]*(?::[a-zA-Z0-9-_/]+)*[a-zA-Z0-9-_/]*"
)

from .memory import MemoryUtils
from .session import Session
from .llm_hooks import LLMHooks

def execute_crew(crew):
    console = Console()
    console.print("[bold magenta]Welcome to the Employee Chatbot. Type 'Bye' to exit.[/bold magenta]\n")
    while True:
        employee_id = console.input("[bold yellow]Enter your Employee ID:[/bold yellow] ").strip()
        if EMPLOYEE_ID_PATTERN.fullmatch(employee_id):
            break
        console.print("[bold red]Invalid Employee ID. Please try again.[/bold red]")
    Session().setEmployeeId(employee_id)
    session_id = str(uuid.uuid4())
    memoryUtils = MemoryUtils(sessionId=session_id, actorId=employee_id)
    LLMHooks(memoryUtils).register()

    while True:
        user_query = console.input("[bold yellow]User:[/bold yellow] ").strip()
        if user_query.strip().lower() == 'bye':
            console.print("[bold green]Chatbot:[/bold green] Goodbye!")
            break

        try:
            trace_kwargs = {
                "thread_id": session_id,
                "user_id": employee_id,
                "input": user_query,
                "name": "Employee Chatbot Interaction"
            }
            with trace(**trace_kwargs):
                inputs = {
                    'employee_query': user_query,
                    'employee_id': employee_id
                }
                response = crew.kickoff(inputs=inputs).raw
                console.print("\n[bold green]Assitant:[/bold green]")
                console.print(Markdown(response))
                update_current_trace(output=response)
                memoryUtils.saveMemory(userPrompt=user_query, assistantResponse=response)
        except Exception as e:
            console.print(
                "\n[bold green]Assitant: An exception occurred....[/bold green]"
            )
            console.print(Markdown(str(e)))

