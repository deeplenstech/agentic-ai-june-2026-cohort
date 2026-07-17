import os
from .utils.crew_executor import execute_crew

from crewai import Agent, Crew, Task
from crewai_tools import MCPServerAdapter
from .utils.llm_factory import get_llm
from .utils.mcp_compat import apply_nullable_schema_patch


def create_crew():
    apply_nullable_schema_patch()

    server_params = {
        "url": "https://api.pageindex.ai/mcp",
        "transport": "streamable-http",
        "headers": {
            "Authorization": f"Bearer {os.environ['PAGEINDEX_API_KEY']}"
        },
    }

    all_tools = MCPServerAdapter(server_params).tools

    hr_manager = Agent(
        role="HR Manager",
        goal="Answer the queries from employees on company policies",
        backstory=(
            "You're a seasoned HR Manager. Known to politly reply to queries form the employees "
            "pertaining to the employee policies. You are also known to reply concisely. "
            "You look up the employee handbook using the available PageIndex document tools."
        ),
        llm=get_llm(),
        tools=all_tools
    )

    handbook_query_task = Task(
        description=(
            "Go through the employee handbook to answer employee queries related to the policies.\n"
            "EMPLOYEE_QUERY: {user_query}\n"
        ),
        expected_output=(
            "A detailed answer to the employee query in plain text. The response should be "
            "empathetic, concise and polite irrespective of the frustration level of the employee"
        ),
        agent=hr_manager
    )

    return Crew(
        agents=[hr_manager],
        tasks=[handbook_query_task],
        verbose=False
    )


def run():
    execute_crew(create_crew())


if __name__ == "__main__":
    run()
