from .utils.crew_executor import execute_crew
from .utils.llm_factory import get_llm

from crewai import Agent, Crew, Task

from .tools.date_tool import GetCurrentDateTool
from .tools.stock_tool import GetStockPriceTool

stock_research_agent = Agent(
    role="Senior Financial Research Analyst",
    goal="Answers queries related to stock prices and financial analysis",
    backstory=(
        "You are a Senior Financial Research Analyst with expertise in stock market "
        "analysis. You have a knack of fetching historical stock data to provide "
        "accurate analysis based on the user query"
    ),
    llm=get_llm(temperature=0.0),
    tools=[GetCurrentDateTool(), GetStockPriceTool()],
)

user_query_task = Task(
    description="{user_query}",
    expected_output=(
        "Provide the analysis in a clear, concise format. If doing comparison of "
        "stock price, include the closing prices for the dates, the dollar "
        "difference, and the percentage change. Present the numerical data in a "
        "markdown table."
    ),
    agent=stock_research_agent,
)

crew = Crew(agents=[stock_research_agent], tasks=[user_query_task], verbose=True)

def run():
    execute_crew(crew)


if __name__ == "__main__":
    run()
