# Assignment 2: Jira Management Crew

## Purpose

This project automates Jira project management using [crewAI](https://crewai.com). Two crew versions are provided so you can compare single-agent versus hierarchical multi-agent architectures, both driven by the **Atlassian MCP server**.

### V1 — Single Agent ([crew_v1.py](src/jiramanagement/crew_v1.py))

A single generalist **Atlassian Assistant** with access to all Atlassian MCP tools runs sequentially to complete any Jira or Confluence task.

### V2 — Hierarchical Multi-Agent ([crew_v2.py](src/jiramanagement/crew_v2.py))

A **Jira Project Manager** orchestrates four specialist agents, each scoped to only the tools it needs (via `_filter_tools()` in [crew_v2.py](src/jiramanagement/crew_v2.py)):

| Agent | Responsibility |
|---|---|
| Confluence Reader | Reads pages, spaces, and search results |
| Confluence Writer | Creates and updates pages, adds comments |
| Jira Reader | Queries issues and projects via JQL |
| Jira Writer | Creates, updates, links, and transitions issues |

> **Why scope tools per agent?** This is the [Principle of Least Privilege](https://arxiv.org/pdf/2512.11147) applied to agentic AI — each agent gets exactly what its role requires, nothing more.
>
> - **Reduced blast radius**: a compromised or misbehaving agent (e.g. via prompt injection) can only affect its narrow scope. A read-only agent cannot overwrite or delete data. [OWASP's Top 10 for LLMs](https://owasp.org/www-project-top-10-for-large-language-model-applications/) explicitly lists *Excessive Agency* as a top risk.
> - **Better accuracy**: fewer tools in context means the LLM has less ambiguity when choosing which to call, reducing hallucinated or incorrect tool invocations.
> - **Faster reasoning**: token budgets aren't spent on irrelevant tool descriptions, leaving more room for actual task reasoning.
> - **Cleaner audits**: every action is traceable to an agent with a well-defined, bounded scope — easier to satisfy compliance and security review requirements.

For enhancement requests the manager automatically:
- Assesses whether a **design task** is needed (architectural changes, new integrations, significant UX work)
- Always creates a **security review task** before QA

## How It Works

1. A `jira_request` is passed as input describing what to create and in which project
2. The crew connects to the Atlassian MCP server (`https://mcp.atlassian.com/v1/mcp`) using Basic Auth
3. The agent(s) create an epic and all child tasks with correct dependencies, then return a structured summary of everything created

## Installation

Ensure you have Python >=3.12 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

Install uv if you haven't already:

```bash
pip install uv
```

Install the dependencies:

```bash
uv python pin 3.12
uv --no-config sync
```

### Configuring Environment Variables

Copy the template and fill in your values:

```bash
cp .env.template .env
```

Configure the following keys in your `.env` file:

**Model setup** — set `MODEL_ID` to the model you want to use, and provide the corresponding API key. Every agent (including the V2 manager) uses this single model. The model must support **tool calling**, since the crew drives the Atlassian MCP tools.

```env
# Example: OpenAI
MODEL_ID=openai/gpt-5.4-mini
MODEL_API_KEY=your_openai_api_key

# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
MODEL_API_KEY=your_anthropic_api_key

# Example: Gemini through LiteLLM
MODEL_ID=gemini/gemini-flash-latest
MODEL_API_KEY=your_gemini_api_key
```

#### Using an OpenAI-compatible endpoint

Some providers (Groq, Together, OpenRouter, local vLLM/Ollama, Bedrock's OpenAI-compatible gateway, …) expose an **OpenAI-compatible** API. To use one, set the model **and** a base URL in `.env`:

```env
MODEL_ID=openai/<model-name>
MODEL_API_KEY=your_provider_api_key
MODEL_BASE_URL=https://provider.example.com/v1/
```

> **Note:** The native `bedrock/...` provider does **not** work with this crew — its tool-calling path is incompatible with the Atlassian MCP tools.

For Gemini, prefer the native LiteLLM provider instead:

```env
MODEL_ID=gemini/gemini-flash-latest
MODEL_API_KEY=your_gemini_api_key
# Leave MODEL_BASE_URL unset for gemini/...
```

Using `openai/gemini-...` with Google's OpenAI-compatible endpoint still works, but LiteLLM sees it as a generic OpenAI model and does not mark it as function-calling capable. CrewAI then falls back to a text/ReAct loop, which makes Langfuse traces less detailed. The `gemini/...` model ID keeps calls on LiteLLM while preserving Gemini tool-calling metadata for richer delegation and tool spans.

**Atlassian** — used to authenticate with the Atlassian MCP server:

```env
ATLASSIAN_EMAIL=your_atlassian_account_email
ATLASSIAN_API_KEY=your_atlassian_api_token
```

To get your Atlassian API token:
1. Log in at [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token with Scope**, give it a name, and copy the token

**Langfuse** (optional) — used for tracing and observability. Tracing is skipped if these keys are absent:

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

To get your Langfuse keys:
1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Create or join an organization, then create a project
3. Go to **Project Settings → API Keys** and copy the public and secret keys

**Submitting a request** — when you run either crew version the terminal will prompt you interactively:

```
Welcome to the Jira Management.

User: <type your Jira/Confluence request here>
```

Example request:

```
I have a todo app. Based on the requirements confluence page create one epic in 
the project with the ID 'TIME' in the cloud ID: 'https://deeplenstech.atlassian.net'. 
Also create tasks with the parent as the newly created epic and set task dependencies 
after the tasks have been created. 
Epic requirements confluence page:
'https://deeplenstech.atlassian.net/wiki/spaces/.../pages/360449/Reminder+feature+in+my+ToDo+app'. 
After you are done, update the confluence page and add a table of newly created Jira issues. 
```

## Running the Project

```bash
# V1 — single generalist agent
uv run python -m src.jiramanagement.crew_v1

# V2 — hierarchical multi-agent (recommended)
uv run python -m src.jiramanagement.crew_v2
```

## Observing Traces in Langfuse

If `LANGFUSE_PUBLIC_KEY` is set, every run produces a full trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop, calling Atlassian MCP tools repeatedly until all Jira items are created. Each LLM call is captured via a custom `LLMOtelListener` that hooks into CrewAI's event bus — necessary because CrewAI 0.186+ bypasses litellm and routes calls through provider-native SDKs directly.

In Langfuse you will see:
- A root `jira_management` span for the entire run
- CrewAI agent and task spans (via `CrewAIInstrumentor`)
- Individual LLM call spans with token usage, input messages, and model output
