import asyncio  # noqa: I001

from .utils.crew_executor import execute_crew
from .utils.llm_factory import get_llm

from crewai import Agent, Crew, Task
from crewai_tools import TavilyExtractorTool, TavilySearchTool

deep_research_agent = Agent(
    role="Deep Research Analyst",
    goal=(
        "Single-handedly conduct end-to-end deep research on a user query: plan the "
        "investigation, gather primary-source evidence from the web, and write a cited, "
        "publication-ready research article. Never rely on prior knowledge — every fact "
        "must be grounded in a source retrieved during this session."
    ),
    backstory=(
        "You are a versatile one-person research desk: strategist, investigative "
        "researcher, science writer, and editor rolled into one. You decompose a broad "
        "question into focused angles, search and extract authoritative sources "
        "(academic papers, government reports, reputable industry publications), and "
        "synthesize the evidence into clear, precise prose. You cite every factual claim "
        "with [Source: URL], and before finishing you critically review your own draft "
        "and revise it to fix unsupported claims, weak structure, or citation gaps."
    ),
    llm=get_llm(temperature=0.0, model_env="MODEL_ID"),
    tools=[TavilySearchTool(), TavilyExtractorTool()],
)

deep_research_task = Task(
    description=(
        "USER QUERY: {user_query}\n\n"
        "Carry out the complete deep-research pipeline yourself, in this exact order. "
        "Each step names the tool(s) you must use:\n\n"
        "1. PLAN — Use Tavily Search to scope the topic, then decompose the query into "
        "2 precise, non-overlapping sub-questions that together cover it comprehensively.\n"
        "2. RESEARCH — For each sub-question, use Tavily Search to find authoritative "
        "sources and use the Tavily Extractor to pull the relevant details from the most "
        "relevant URL (top one per sub-question). Record findings with [Source: URL] "
        "citations. Do NOT rely on prior knowledge.\n"
        "3. WRITE — Do NOT use any tools in this step. Using ONLY the findings already "
        "gathered in step 2, synthesize a 1000-1500 word markdown article with a "
        "compelling introduction, body sections aligned to the sub-questions, inline "
        "[Source: URL] citations for every factual claim, and a concise conclusion.\n"
        "4. CRITIQUE — Critically review the draft from step 3 for factual support, "
        "citation completeness, structure, and coherence. Use Tavily Search to verify "
        "questionable claims and identify unsupported or outdated statements. Produce a "
        "specific, actionable list of revision points (do NOT rewrite the article here).\n"
        "5. REVISE — Incorporate every critique point from step 4 into the article. Use "
        "Tavily Search to source any missing, unsupported, or outdated information and add "
        "proper [Source: URL] citations. Output the final, polished article."
    ),
    expected_output=(
        "A final, publication-ready research article in markdown (1000-1500 words) with "
        "proper headings and inline [Source: URL] citations."
    ),
    agent=deep_research_agent,
)

crew = Crew(
    agents=[deep_research_agent],
    tasks=[deep_research_task],
    verbose=True,
)


async def run():
    await execute_crew(crew)


if __name__ == "__main__":
    asyncio.run(run())
