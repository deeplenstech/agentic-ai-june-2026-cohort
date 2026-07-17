from .utils.crew_executor import execute_crew
from .utils.llm_factory import get_llm

from crewai import Agent, Crew, Task
from crewai_tools import TavilySearchTool

from .tools.date_tool import GetCurrentDateTool

generalist_agent = Agent(
    role="Generalist Agent",
    goal="Answer general questions based on user query. You must use Tavily search to get latest data.",
    backstory="",
    llm=get_llm(temperature=0.0),
    tools=[GetCurrentDateTool(), TavilySearchTool()],
)

user_query_task = Task(
    description="{user_query}",
    expected_output="",
    agent=generalist_agent,
)

crew = Crew(
    agents=[generalist_agent],
    tasks=[user_query_task],
    planning=True,
    planning_llm=get_llm(temperature=0.0),
    verbose=True,
)

def run():
    execute_crew(crew)


if __name__ == "__main__":
    run()
