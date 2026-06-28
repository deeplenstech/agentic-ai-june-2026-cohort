# Stockresearch Crew

## Purpose

Welcome to the Stockresearch Crew project, powered by [crewAI](https://crewai.com). 

This project explores different CrewAI configurations to automate stock research, ranging from a simple single-agent setup to a hierarchical multi-agent crew. Given a user query (like a stock ticker or company name), the crew researches the company, analyzes relevant financial and market data, and produces a research report. It is intended as a starting point for building AI-powered investment research workflows using crewAI.


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to the project folder:

```bash
cd session2/1.stockresearch
```

Then install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
uv sync
```
### Customizing

**Set up your `.env` file by copying the template:**

```bash
cp .env.template .env
```

Then configure the following keys in your `.env` file:

**Model setup** — set `MODEL_ID` to the model you want to use, and provide the corresponding API key (in case you are not using AWS Bedrock hosted models).

```env
# Example: AWS Bedrock
MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0

# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
ANTHROPIC_API_KEY=your_anthropic_api_key

# Example: OpenAI
MODEL_ID=openai/gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

If you are using AWS Bedrock hosted models, you need to install and configure the AWS CLI by following the [official AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). Once installed, run:

```bash
aws configure
```

You'll be prompted for your AWS Access Key ID, Secret Access Key, default region (`us-east-1`), and output format (`json`).

**Tavily** — used by the agent to search the web for stock data:

```env
TAVILY_API_KEY=your_tavily_api_key
```

Get a free Tavily key at [tavily.com](https://tavily.com).

**Langfuse** — used for tracing and observability:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. ***Create an account*** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. ***Create an organization*** — after login, you'll be prompted to create or join an organization (this is the top-level workspace, e.g. your team or company name)
3. ***Create a project*** — inside your organization, create a new project (e.g. `stockresearch`); each project has its own set of API keys and trace history
4. ***Get your API keys*** — go to **Project Settings → API Keys** and create a new key pair; copy the public and secret keys into your `.env` file

## Running the Project

To kickstart your crew of AI agents and begin task execution, run one of the crew scripts from the root folder of your project. Each command runs a different agent architecture, so you can compare them side by side:

```bash
# V1 — Single generalist agent (web search only)
$ uv run python -m src.stockresearch.crew_v1

# V1 + Planning — same single agent, but plans its steps before acting
$ uv run python -m src.stockresearch.crew_v1_with_planning

# V2 — Single specialized Financial Analyst (custom stock tools, structured output)
$ uv run python -m src.stockresearch.crew_v2

# V3 — Hierarchical crew (Manager delegates to Analyst or Generalist)
$ uv run python -m src.stockresearch.crew_v3
```

How the versions differ:

- **`crew_v1`** — A single generalist agent that answers broad queries using web search. The simplest setup; best for general information.
- **`crew_v1_with_planning`** — The same single agent with CrewAI **planning** enabled. Before executing, the crew drafts a step-by-step plan, which can improve reasoning on multi-step queries at the cost of extra LLM calls. Use this to see the effect of planning versus the plain `crew_v1`.
- **`crew_v2`** — A single **Senior Financial Research Analyst** with specialized tools (stock price, dates) that outputs data in structured markdown tables. More accurate for financial queries than `crew_v1`.
- **`crew_v3`** — A **hierarchical** crew where a **Manager Agent** analyzes the query intent and delegates to the Financial Analyst (for stocks) or the Generalist (for broad topics). The most autonomous version; handles diverse queries.

Each command initializes the stockResearch Crew, assembling the agent(s) and assigning them tasks as defined.

The script will prompt you in the terminal for a user query. Below are example queries:
1. Compare Google's (GOOGL) current stock price to its price exactly one month ago. 
2. What is the impact of AI on the stock prices?

> **Tip for the generalist agent (`crew_v1` and `crew_v1_with_planning`):** because the generalist agent has no specialized tools or structured-output prompting, a short query may produce vague results. Giving it a more detailed prompt — specifying the role, the action, and the expected output format — yields much better answers. For example:
>
> **Role:** You are a senior financial research assistant at a top investment firm.
>
> **Action:** Compare Google's (GOOGL) current stock price to its price exactly one month ago.
>
> **Expectation:** Provide the comparison in a clear, concise format. Include the current closing price, the previous month's closing price, the dollar difference, and the percentage change. Present the numerical data in a markdown table.

## Observing the ReAct Cycle in Langfuse

Once you've configured Langfuse and run the crew, you can observe the agent's full reasoning trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM thinks about what it knows and what it needs
2. **Act** — CrewAI(based on Agent configuration) calls a tool (e.g. Tavily web search, date tool, stock price tool)
3. **Observe** — LLM reads the tool result
4. **Repeat** — until it has enough information to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span. This makes it easy to understand how the agent arrived at its answer and where time or tokens were spent.

## Crew Versions

This project includes several versions of the crew to demonstrate the evolution of agentic architectures:

| Version | Command | Architecture | Agents | Description |
| :--- | :--- | :--- | :--- | :--- |
| **V1** | `crew_v1` | **Single Agent** | Generalist Agent | A simple setup that uses a generalist agent to answer broad queries using web search. Best for general information. |
| **V1 + Planning** | `crew_v1_with_planning` | **Single Agent** | Generalist Agent | Same single agent as V1 with CrewAI **planning** enabled — the crew drafts a step-by-step plan before acting. Useful for comparing planned vs. unplanned reasoning. |
| **V2** | `crew_v2` | **Single Agent** | Senior Financial Research Analyst | Focused specifically on financial data. It uses specialized tools to fetch stock prices and is prompted to output data in structured markdown tables. |
| **V3** | `crew_v3` | **Hierarchical** | Manager, Financial Analyst, Generalist | The advanced version. A **Manager Agent** receives the user query, analyzes the intent, and delegates the task to either the Financial Analyst (for stocks) or the Generalist (for broad topics). |

### Key Differences
- **Autonomy**: V1 and V2 are straightforward executions. V3 introduces a "Manager" that makes decisions about who should handle the work.
- **Planning**: `crew_v1_with_planning` adds an explicit planning step before execution, while all other versions act directly on the query.
- **Specialization**: V2 and V3 introduce a specialized Financial Analyst agent with custom tools for stock data, whereas V1 is a "jack of all trades".
- **Complexity**: V3 demonstrates **hierarchical process** and **agent delegation**, allowing for more robust handling of diverse user queries.

