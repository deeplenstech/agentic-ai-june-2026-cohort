# Deep Research Crew

## Purpose

Welcome to the Deep Research project, powered by [crewAI](https://crewai.com).

This project uses a multi-agent AI crew to conduct deep, structured research on any topic. Given a research question, the crew decomposes it into sub-questions, investigates each using live web search and content extraction, writes a comprehensive cited article, and applies a critic-review feedback loop before producing the final output.

The project ships **three implementations of the same pipeline** so you can compare CrewAI orchestration styles, from the simplest single-agent setup up to full hierarchical delegation:

- **`crew_v1`** — a **single agent** crew. One **Deep Research Analyst** carries out the entire pipeline — planning, investigation, writing, and self-critique/revision — within a single task. The simplest baseline.
- **`crew_v2`** — a **hierarchical** crew. A dedicated **Manager** agent (run on a stronger model) is given a single multi-step task and delegates each step — planning, investigation, writing, critique, and feedback incorporation — to the right specialist at runtime.
- **`crew_v3`** — a **sequential** crew with explicit, wired-up tasks and **structured (Pydantic) outputs** at every step. The two sub-questions are researched **in parallel** (each by its own researcher agent via async execution), then synthesized, critiqued, and revised in a fixed order.


## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to the project folder:

```bash
cd session3/1.deepresearch
```

Then install the dependencies:

Lock the dependencies and install them by using the CLI command:
```bash
uv python pin 3.12
uv --no-config sync
```
### Customizing

**Set up your `.env` file by copying the template:**

```bash
cp .env.template .env
```

Then configure the following keys in your `.env` file:

**Model setup** — set `MODEL_ID` to the model you want to use, and provide the corresponding API key (in case you are not using AWS Bedrock hosted models).

`BETTER_MODEL_ID` is a second, typically stronger model used by the **Manager** agent in `crew_v2` (the hierarchical crew) to coordinate delegation. It is not used by `crew_v1` or `crew_v3`.

```env
# Example: AWS Bedrock
MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0
BETTER_MODEL_ID=bedrock/us.anthropic.claude-sonnet-4-6

# Example: Gemini through LiteLLM
MODEL_ID=gemini/gemini-flash-latest
BETTER_MODEL_ID=gemini/gemini-2.5-flash
MODEL_API_KEY=your_gemini_api_key

# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
ANTHROPIC_API_KEY=your_anthropic_api_key

# Example: OpenAI
MODEL_ID=openai/gpt-4o
OPENAI_API_KEY=your_openai_api_key
```

#### Using an OpenAI-compatible endpoint

Some providers (Groq, Together, OpenRouter, local vLLM/Ollama, …) expose an
**OpenAI-compatible** API. To use one, set the model **and** a base URL in `.env`:

```env
MODEL_ID=openai/<model-name>
BETTER_MODEL_ID=openai/<stronger-model-name>
MODEL_API_KEY=your_provider_api_key
MODEL_BASE_URL=https://provider.example.com/v1/
```

For Gemini, prefer the native LiteLLM provider instead:

```env
MODEL_ID=gemini/gemini-flash-latest
BETTER_MODEL_ID=gemini/gemini-2.5-flash
MODEL_API_KEY=your_gemini_api_key
# Leave MODEL_BASE_URL unset for gemini/...
```

Using `openai/gemini-...` with Google's OpenAI-compatible endpoint still works, but
LiteLLM sees it as a generic OpenAI model and does not mark it as function-calling
capable. CrewAI then falls back to a text/ReAct loop, which makes Langfuse traces
less detailed. The `gemini/...` model ID keeps calls on LiteLLM while preserving
Gemini tool-calling metadata for richer delegation and tool spans.

> **Note:** Provider free tiers can be very restrictive (e.g. Gemini `gemini-2.5-flash`
> free tier allows only ~20 requests/day *per model*). A single crew run makes several
> LLM calls, and `NUM_RETRIES` in `llm_factory.py` means a rate-limited call retries
> (each retry counts against quota). If you hit HTTP 429 `RESOURCE_EXHAUSTED`, switch to
> a model that still has quota, enable billing, or wait for the daily reset.

If you are using AWS Bedrock hosted models, you need to install and configure the AWS CLI by following the [official AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html). Once installed, run:

```bash
aws configure
```

You'll be prompted for your AWS Access Key ID, Secret Access Key, default region (`us-east-1`), and output format (`json`).

**Tavily** — used by the agent to search the web for data:

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
3. ***Create a project*** — inside your organization, create a new project (e.g. `deepresearch`); each project has its own set of API keys and trace history
4. ***Get your API keys*** — go to **Project Settings → API Keys** and create a new key pair; copy the public and secret keys into your `.env` file

## Running the Project

To kickstart your crew of AI agents and begin task execution, run one of the two crew implementations from the root folder of your project:

```bash
# Single-agent crew (one analyst does everything — simplest)
$ uv run python -m src.deepresearch.crew_v1

# Hierarchical crew (manager delegates to specialists)
$ uv run python -m src.deepresearch.crew_v2

# Sequential crew (explicit tasks, structured outputs, parallel research)
$ uv run python -m src.deepresearch.crew_v3
```

This initializes the Deep Research crew, assembles the agents, and executes the research pipeline. Once asked, you may mention the topic you would like the agent to perform deep research on. It will take around 10 minutes to produce a structured research article on the asked query.

## Observing the ReAct Cycle in Langfuse

Once you've configured Langfuse and run the crew, you can observe the agent's full reasoning trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agents follow a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM thinks about what it knows and what it needs
2. **Act** — CrewAI calls a tool (e.g. Tavily web search, URL extractor)
3. **Observe** — LLM reads the tool result
4. **Repeat** — until it has enough information to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span. This makes it easy to understand how the agent arrived at its answer and where time or tokens were spent.

## Understanding Your Crew

The `crew_v2` and `crew_v3` implementations share the same set of specialist roles — a **Planner**, **Researcher(s)**, **Writer**, **Critic**, and **Reviser** — that collaborate to produce a cited research article with a built-in critic-and-revise step. `crew_v1` collapses all of those roles into a single generalist agent. They differ in how the work is orchestrated:

### `crew_v1` — Single Agent

One **Deep Research Analyst** agent, equipped with the Tavily web-search and content-extraction tools, runs the entire pipeline inside a single task: it plans the sub-questions, researches each one, writes the article, and then self-critiques and revises its own draft. There is no delegation and no inter-agent handoff — the simplest possible baseline for comparison against the multi-agent versions.

### `crew_v2` — Hierarchical

A **Manager** agent (run on `BETTER_MODEL_ID`) receives a single multi-step task and delegates each step to the right specialist at runtime via CrewAI's `Process.hierarchical`. The manager decides the order and handoffs; the Reviser ("Feedback Incorporation Specialist") produces the final deliverable after applying the critic's feedback.

### `crew_v3` — Sequential

Tasks are explicitly wired together with `context=[...]` dependencies and run via `Process.sequential`. Every step emits a **structured Pydantic output** (`ResearchPlan`, `ResearchFindings`, `Article`, `Critique`), making the data flow between agents typed and predictable. The Planner produces exactly two sub-questions, which are then researched **in parallel** by two independent researcher agents (`async_execution=True`) — each with its own agent instance to keep concurrent tool-call histories from interleaving — before the Writer synthesizes, the Critic reviews, and the Reviser finalizes the article.
