# Assignment 2: Employee Policy Crew

## Purpose

Welcome to the Employee Policy Crew project, powered by [crewAI](https://crewai.com).

This project answers employee questions about company policies by retrieving relevant content from the employee handbook. A single **HR Manager** agent looks up the handbook and returns a concise, empathetic, policy-grounded response.

The project ships **two retrieval variants** — mirroring the two knowledge-base approaches you built in Assignment 1 (`1.knowledgebase`). Both use the same single HR Manager agent following a **ReAct** (Reason + Act) loop; they differ only in *how* the handbook is retrieved.

## The Two Variants

| Variant | Module | Retrieval | Requires |
|---|---|---|---|
| **Vector RAG** | [crew_vector_rag.py](src/employeepolicy/crew_vector_rag.py) | `BedrockKBRetrieverTool` — top-K vector similarity over an Amazon Bedrock Knowledge Base | `BEDROCK_KB_ID` + AWS credentials |
| **Vectorless RAG** | [crew_vectorless_rag.py](src/employeepolicy/crew_vectorless_rag.py) | **PageIndex MCP** server — LLM reasoning / tree search over a document outline (no embeddings) | `PAGEINDEX_API_KEY` |

The Vector RAG variant also supports optional **reranking** (see [below](#optional-reranking-vector-variant)).

## How It Works

1. The app starts and prompts you for your **Employee ID**, then enters an interactive chat loop.
2. You type a question at the `User:` prompt.
3. The **HR Manager** agent uses its retrieval tool (Bedrock KB or PageIndex MCP, depending on the variant) to search the employee handbook, reasoning through the ReAct loop until it has enough context.
4. The agent returns a polite, concise answer grounded in the retrieved policy content.
5. Keep asking questions, or type **`Bye`** to exit.

When memory is configured (see [Memory](#memory-optional)), prior turns and a running conversation summary for that Employee ID are injected ahead of each query, so the agent answers with awareness of the conversation so far.

## Installation

Ensure you have Python >=3.12 <3.13 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling.

First, if you haven't already, install uv:

```bash
pip install uv
```

Navigate to the project directory and install the dependencies:

```bash
uv python pin 3.12
uv --no-config sync
```

### Configuring Environment Variables

Copy the template and fill in your values:

```bash
cp .env.template .env
```

Then configure the following keys in your `.env` file.

#### Model setup

Set `MODEL_ID` to the model you want to use, and provide the corresponding API key via `MODEL_API_KEY`. Both variants drive tools (the KB retriever or the PageIndex MCP tools), so the model **must support tool calling**.

```env
# Example: Anthropic
MODEL_ID=anthropic/claude-sonnet-4-6
MODEL_API_KEY=your_anthropic_api_key

# Example: OpenAI
MODEL_ID=openai/gpt-5.4-mini
MODEL_API_KEY=your_openai_api_key

# Example: Gemini through LiteLLM
MODEL_ID=gemini/gemini-flash-latest
MODEL_API_KEY=your_gemini_api_key

# Example: AWS Bedrock (uses your AWS credentials — no MODEL_API_KEY needed)
MODEL_ID=bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0
```

##### Using an OpenAI-compatible endpoint

Some providers (Groq, Together, OpenRouter, local vLLM/Ollama, Bedrock's OpenAI-compatible gateway, …) expose an **OpenAI-compatible** API. To use one, set the model **and** a base URL in `.env`:

```env
MODEL_ID=openai/<model-name>
MODEL_API_KEY=your_provider_api_key
MODEL_BASE_URL=https://provider.example.com/v1/
```

For Gemini, prefer the native LiteLLM provider instead:

```env
MODEL_ID=gemini/gemini-flash-latest
MODEL_API_KEY=your_gemini_api_key
# Leave MODEL_BASE_URL unset for gemini/...
```

Using `openai/gemini-...` with Google's OpenAI-compatible endpoint still works, but LiteLLM sees it as a generic OpenAI model and does not mark it as function-calling capable. CrewAI then falls back to a text/ReAct loop, which makes Langfuse traces less detailed. The `gemini/...` model ID keeps calls on LiteLLM while preserving Gemini tool-calling metadata for richer tool spans.

> If you use the **Vector RAG** variant, your AWS credentials must be configured (via `~/.aws/credentials`, IAM role, or environment variables) with permission to query the Knowledge Base — this is independent of which `MODEL_ID` provider you choose.

#### Knowledge Base — Vector RAG variant

The ID of the Amazon Bedrock Knowledge Base containing the employee handbook. This was created per the instructions in the `1.knowledgebase` folder.

```env
BEDROCK_KB_ID=your_bedrock_knowledge_base_id
```

#### PageIndex — Vectorless RAG variant

The API key for the PageIndex MCP server used by the vectorless variant.

```env
PAGEINDEX_API_KEY=your_pageindex_api_key
```

#### Memory (optional)

Enables per-employee conversational memory backed by **AWS Bedrock AgentCore**. When set, short-term turns and a session summary are loaded (keyed by Employee ID) and injected ahead of each query. Omit these to run the chatbot statelessly.

```env
MEMORY_ID=your_agentcore_memory_id
MEMORY_SUMMARY_STRATEGY_ID=your_summary_strategy_id
```

`MEMORY_ID` enables short-term turn recall; `MEMORY_SUMMARY_STRATEGY_ID` additionally enables the running conversation summary. If either is empty, the corresponding feature is skipped.

#### Langfuse (optional)

Used for tracing and observability. Tracing is only activated when `LANGFUSE_PUBLIC_KEY` is present in the environment; you can omit these keys to run without observability.

```env
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

To get your Langfuse keys:

1. **Create an account** — sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. **Create an organization** — after login, create or join an organization
3. **Create a project** — create a new project (e.g. `employeepolicy`); each project has its own API keys
4. **Get your API keys** — go to **Project Settings → API Keys** and copy the public and secret keys

## Running the Project

Run one of the two variants from the project root:

```bash
# Vector RAG — Amazon Bedrock Knowledge Base
uv run python -m src.employeepolicy.crew_vector_rag

# Vectorless RAG — PageIndex MCP
uv run python -m src.employeepolicy.crew_vectorless_rag
```

The app will greet you, ask for your Employee ID, and then loop on questions:

```
Welcome to the Employee Chatbot. Type 'Bye' to exit.

Enter your Employee ID: E1234
User: How many sick leaves are allowed in a year?
```

Type `Bye` at the `User:` prompt to exit.

## Optional: Reranking (Vector variant)

[crew_vector_rag.py](src/employeepolicy/crew_vector_rag.py) includes a commented-out `BedrockKBRetrieverTool` configuration that enables reranking. Reranking improves retrieval quality by having a second model score and reorder retrieved chunks by relevance — useful when you want to cast a wide initial search net but only pass the most relevant chunks to the LLM.

Uncomment the reranking block in [crew_vector_rag.py](src/employeepolicy/crew_vector_rag.py) and set `modelArn` to a supported reranker in your region. See [Amazon Bedrock reranking docs](https://docs.aws.amazon.com/bedrock/latest/userguide/rerank-supported.html) for supported models and regions. (Reranking applies only to the Vector RAG variant.)

## Observing Traces in Langfuse

Once configured, every run produces a full trace at [cloud.langfuse.com](https://cloud.langfuse.com).

The agent follows a **ReAct** (Reason + Act) loop:

1. **Reason** — the LLM considers the query and what it needs to look up
2. **Act** — the agent calls its retrieval tool (Bedrock KB or PageIndex MCP) to search the handbook
3. **Observe** — the LLM reads the retrieved content
4. **Repeat** — until it has enough context to produce the final answer

In the Langfuse trace view you will see each LLM call, tool invocation, and intermediate output as a separate span.
