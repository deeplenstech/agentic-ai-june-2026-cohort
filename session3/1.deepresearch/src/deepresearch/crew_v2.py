import asyncio  # noqa: I001

from .utils.crew_executor import execute_crew
from .utils.llm_factory import get_llm

from crewai import Agent, Crew, Process, Task
from crewai_tools import TavilyExtractorTool, TavilySearchTool

deep_research_planner = Agent(
    role="Deep Research Planner",
    goal=(
        "Decompose a broad research question into 2 precise, non-overlapping sub-question "
        "that together provide comprehensive coverage of the question."
    ),
    backstory=(
        "You are an expert research strategist with a background in academic literature review "
        "and investigative journalism. You excel at identifying the key dimensions of a complex "
        "question and formulating targeted questions that will yield actionable insights when "
        "answered independently and then synthesized. You think like an editor commissioning "
        "a cover story: what are the essential angles a reader needs to understand the full picture? "
    ),
    llm=get_llm(temperature=0.0),
    tools=[TavilySearchTool()],
)

researcher_agent = Agent(
    role="Deep Research Investigator",
    goal=(
        "Research a specific research sub-question thoroughly using web search and URL content extraction. "
        "Produce a comprehensive findings summary with full source citations. "
        "It is important that you don't rely on your knowledge, rather rely on information searched "
        "and extracted from the internet. "
        "When extracting URL content, limit extraction to the top one most relevant URL per sub-question — "
        "do not extract content from every search result. "
    ),
    backstory=(
        "You are a skilled investigative researcher who gathers primary source evidence using "
        "web search and content extraction. You are meticulous about citing sources — for every claim "
        "you make, you record the source URL, the exact excerpt that supports the claim. "
        "You never rely on prior knowledge: every fact must be grounded in a source retrieved "
        "during this session. You prioritize authoritative sources such as academic papers, "
        "peer-reviewed journals, government reports, and reputable industry publications. "
    ),
    llm=get_llm(temperature=0.0),
    tools=[TavilySearchTool(), TavilyExtractorTool()],
)

writer_agent = Agent(
    role="Research Article Writer",
    goal=(
        "Write a structured, authoritative 1000-1500 word research article based on the provided "
        "research and synthesizing findings into a cohesive narrative with proper inline citations. "
    ),
    backstory=(
        "You are a professional science and technology writer with experience writing for "
        "publications like MIT Technology Review and Wired. You write in clear, precise prose, "
        "cite every factual claim with its source URL in the format [Source: URL], and structure "
        "articles with a compelling introduction, logically ordered body sections aligned to the "
        "research plan, and a concise conclusion. You never invent facts — everything you write "
        "is grounded in sources retrieved from the knowledge base. When critic feedback is "
        "provided, you address every point specifically and improve the article accordingly. "
    ),
    llm=get_llm(temperature=0.0),
)

critic_agent = Agent(
    role="Research Article Critic",
    goal=(
        "Review a research article draft for factual support, structural quality, citation "
        "completeness, and logical coherence. Produce a structured critique with specific "
        "actionable revision instructions, or output APPROVED if ready for publication. "
    ),
    backstory=(
        "You are a rigorous peer reviewer and editorial standards enforcer with experience "
        "in academic publishing and long-form journalism. You identify unsupported claims, "
        "structural weaknesses, missing perspectives, and citation gaps. Your critiques are "
        "specific and constructive: you flag exact sentences or sections that need revision "
        "and explain precisely how to fix them. You understand that the article should cite "
        "every factual claim with [Source: URL] format. You output blank string only when the "
        "article meets high publication standards. "
    ),
    llm=get_llm(temperature=0.0),
    tools=[TavilySearchTool()],
)

revision_agent = Agent(
    role="Feedback Incorporation Specialist",
    goal=(
        "Produce the final, publication-ready research article by incorporating the critic's "
        "feedback into the article written by the Research Article Writer. You receive two inputs: "
        "(1) the article drafted by the writer, and (2) the structured critique from the critic. "
        "Address every point of feedback specifically, and when the critique identifies missing, "
        "unsupported, or outdated information, use web search to find authoritative sources and "
        "fill the gaps with proper [Source: URL] citations. Your output is the final article."
    ),
    backstory=(
        "You are a senior revision editor who specialises in taking a draft article together with "
        "a reviewer's critique and turning it into a polished, fully-supported final piece. You "
        "treat the critic's feedback as a checklist: for each point you make a concrete change to "
        "the article. You are not afraid to run additional web searches to verify claims, replace "
        "weak sources, or add the evidence the critic asked for. You preserve the writer's voice and "
        "structure where it is strong, and you cite every factual claim with [Source: URL]. "
        "Your revised article is the definitive final version — it must read as a complete, "
        "standalone publication with no remaining open critique."
    ),
    llm=get_llm(temperature=0.0),
    tools=[TavilySearchTool()],
)

manager_agent = Agent(
    role="Deep Research Manager",
    goal=(
        "Orchestrate the full deep research workflow by delegating each step to the right specialist: "
        "planning to the Research Planner, investigation to the Research Investigator, "
        "writing to the Article Writer, critique to the Article Critic, and final feedback "
        "incorporation to the Feedback Incorporation Specialist. "
        "Ensure each step completes fully before the next begins. The Feedback Incorporation "
        "Specialist always produces the final article by applying the critic's feedback to the "
        "writer's draft, and its output is the final deliverable."
    ),
    backstory=(
        "You are a senior research director who has led large investigative teams at top-tier "
        "publications. You do not do the research yourself — you assign the right work to the "
        "right specialist, review their outputs for completeness, and coordinate handoffs between "
        "planning, investigation, writing, and editorial review. "
        "You are decisive and keep the team focused: you never allow a step to be skipped and "
        "you ensure the critic's feedback is fully acted on before the final article is delivered."
    ),
    llm=get_llm(temperature=0.0, model_env="BETTER_MODEL_ID"),
    allow_delegation=True,
)

research_task = Task(
    description=(
        "USER QUERY: {user_query}\n\n"
        "Execute the following steps in order:\n\n"
        "Step 1 — Research Planning\n"
        "Analyse the user query and decompose it into 2 precise, non-overlapping sub-questions "
        "that together provide comprehensive coverage of the topic. "
        "Output the numbered list of sub-questions before proceeding.\n\n"
        "Step 2 — Sub-Question Investigation\n"
        "Work through each sub-question from Step 1 IN PARALLEL. For each sub-question: "
        "search for relevant sources, extract detailed content from the most promising URLs, "
        "and compile a comprehensive findings summary with inline [Source: URL] citations. "
        "Finish all research for one sub-question before moving to the next. "
        "Do NOT rely on prior knowledge — every fact must come from a retrieved source. "
        "Output a findings summary for each sub-question before proceeding.\n\n"
        "Step 3 — Article Writing\n"
        "Using the sub-questions from Step 1 and all the findings from Step 2, write a comprehensive "
        "1500-3000 word research article in markdown format. Structure it with a compelling "
        "introduction, body sections aligned to each sub-question, inline [Source: URL] citations "
        "for every factual claim, and a concise conclusion. "
        "Do NOT invent facts — every claim must be grounded in the Step 2 findings.\n\n"
        "Step 4 — Critical Review (performed only once)\n"
        "Have the Article Critic critically review the article written in Step 3 for: factual "
        "support and citation completeness, structural quality and logical coherence, coverage of "
        "all sub-questions, and writing clarity. The critic produces a structured critique with "
        "specific, actionable feedback referencing exact sentences or sections (or notes that a "
        "section is already strong). The critic does NOT rewrite the article.\n\n"
        "Step 5 — Feedback Incorporation (final step)\n"
        "Hand BOTH the article from Step 3 AND the critique from Step 4 to the Feedback "
        "Incorporation Specialist. This specialist incorporates every point of the critic's "
        "feedback into the article, using web search to source any missing, unsupported, or "
        "outdated information and adding proper [Source: URL] citations. The specialist's revised "
        "article is the FINAL deliverable — output it as the final answer. Do NOT loop back to "
        "earlier steps after this."
    ),
    expected_output=(
        "The final, publication-ready research article in markdown format (1000-1500 words) with "
        "proper headings and inline [Source: URL] citations, produced by the Feedback "
        "Incorporation Specialist after applying the critic's feedback to the writer's draft."
    ),
)

crew = Crew(
    agents=[deep_research_planner, researcher_agent, writer_agent, critic_agent, revision_agent],
    tasks=[research_task],
    process=Process.hierarchical,
    manager_agent=manager_agent,
    verbose=True,
)


async def run():
    await execute_crew(crew)


if __name__ == "__main__":
    asyncio.run(run())
