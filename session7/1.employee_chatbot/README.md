# Employee Chatbot: Policy & Leave Manager

## Purpose

Welcome to the **Employee Chatbot** project, powered by [crewAI](https://crewai.com) and [DeepEval](https://github.com/confident-ai/deepeval).

This project features a simple HR agent capable of:
1.  **Policy Querying**: Answering questions about company policies by searching an **Amazon Bedrock Knowledge Base**.
2.  **Leave Management**: Handling leave applications and querying leave history using a local SQLite database (`leaves.db`).
3.  **Conversational Memory**: Maintaining context across multiple turns using short-term memory and automated summaries.

## Features

- **Multi-turn Support**: The chatbot tracks conversation history and maintains a summary to provide contextually aware responses.
- **Tool Augmentation**: 
  - `BedrockKBRetrieverTool`: Searches the employee handbook.
  - `insert_leave`: Records new leave requests in the database.
  - `read_leaves`: Retrieves an employee's leave records.
  - `get_current_date`: Provides the current date for date-relative queries.
- **Online Evaluation**: Live metrics (e.g., Knowledge Based Completeness) are reported to [Confident AI](https://www.confident-ai.com/) during interaction.
- **Offline Testing**: Comprehensive test suite for single-turn and multi-turn scenarios using DeepEval's `ConversationSimulator`.
- **Session-Level Tracing**: Every turn of a run is traced to [Langfuse](https://langfuse.com/) and grouped under one session, attributed to the employee.

## Installation

Ensure you have Python >=3.12 <3.13 installed. This project uses [UV](https://docs.astral.sh/uv/) for dependency management.

1.  **Install UV** (if not already installed):
    ```bash
    pip install uv
    ```
2.  **Install Dependencies**:
    ```bash
    uv sync
    ```

## Configuration

Copy the template and fill in your credentials:

```bash
cp .env.template .env
```

### Required Environment Variables

| Variable | Description |
| :--- | :--- |
| `MODEL_ID` | The Bedrock model ID (e.g., `bedrock/us.anthropic.claude-sonnet-4-6`). |
| `BEDROCK_KB_ID` | The ID of your Amazon Bedrock Knowledge Base (setup similarly to Session 3 assignments). |
| `CONFIDENT_API_KEY` | Your API key from [Confident AI](https://www.confident-ai.com/) (ensure it's for a specific project). |
| `OPENAI_API_KEY` | Required by DeepEval for running certain metrics (GEval, etc.). |
| `LANGFUSE_PUBLIC_KEY` | Public key from [Langfuse](https://cloud.langfuse.com). Optional. Tracing is only activated when this is set. |
| `LANGFUSE_SECRET_KEY` | Secret key from Langfuse. |
| `LANGFUSE_BASE_URL` | Langfuse host. Defaults to `https://cloud.langfuse.com`. |

> [!NOTE]
> Ensure your AWS credentials are configured (via `~/.aws/credentials` or environment variables) with permissions for Bedrock and the Knowledge Base.

---

## Assignment 1: AWS AgentCore Memory Setup

### Goal
Configure the chatbot to use **Amazon Bedrock AgentCore** for persistent conversational memory, allowing it to maintain context across sessions via short-term turns and long-term summaries.

### Steps
1.  **AWS Console Setup**:
    - Navigate to the **Amazon Bedrock AgentCore** console.
    - Under **Build**, find **Memory**
    - Create a new **Memory** and note down the `MEMORY_ID`.
    - Configure a **Memory Strategy** for automated summarization and note down the `MEMORY_SUMMARY_STRATEGY_ID`.
2.  **Environment Configuration**:
    - Update your `.env` file with the retrieved IDs:
      ```env
      MEMORY_ID="your_memory_id"
      MEMORY_SUMMARY_STRATEGY_ID="your_memory_summary_strategy_id"
      ```
3.  **Verify Memory Persistence**:
    - Run the chatbot and have a conversation about a specific topic (e.g., your vacation plans). Try to interact multiple times and see if the chatbot remembers the previous messages and provides relevant responses.
    ```bash
    uv run python -m src.employee_chatbot.main
    ```
    - Exit the chatbot by typing `bye`.
4.  **Deep Dive**:
    - Review `src/employee_chatbot/utils/memory.py` to see how `MemoryClient` from `bedrock_agentcore` is used to `create_event`, `get_last_k_turns`, and `retrieve_memories`.
    - Understand the difference between **Short-term Memory** (exact last $K$ turns) and **Long-term Memory** (summaries extracted via memory strategies).

---

## Assignment 2: Online Evaluation

### Goal
Configure the chatbot, interact with it across multiple turns, and observe the live traces and online evaluations in Confident AI.

### Steps
1.  **Setup Environment**: Fill in your `.env` file with all required keys (including the Memory IDs from Assignment 1).
2.  **Set Up Metric Collections & Evaluation Workflows** (in the Confident AI dashboard):
    - **Create two metric collections** under **Metrics → Collections** ([Metric Collections docs](https://www.confident-ai.com/docs/metrics/metric-collections)):
      - A **single-turn** collection (e.g. `Employee Chatbot Trace Metrics`) for evaluating individual traces.
      - A **multi-turn** collection (e.g. `Employee Chatbot Thread Metrics`) for evaluating whole conversations.
    - **Add a trace evaluation rule** so each new trace is scored automatically on arrival: go to **Workflows → Traces → Evaluation Rules → New rule**, set the **Data Model** to **Trace**, attach your **single-turn** collection, and toggle it **Enabled**. Trace rules fire at ingest on every incoming trace ([Workflows docs](https://www.confident-ai.com/docs/llm-tracing/workflows#evaluation-rules)).
    - **Add a thread evaluation rule** so each conversation is scored once it is well-formed: go to **Workflows → Threads → Evaluation Rules → New rule**, attach your **multi-turn** collection, and toggle it **Enabled**. Thread rules fire after the thread has been idle for the configured time limit (default 300s), so evaluation triggers shortly after you type `Bye` ([Workflow docs](https://www.confident-ai.com/docs/llm-tracing/workflows#evaluation-rules)).
3.  **Run the Chatbot**:
    ```bash
    uv run python -m src.employee_chatbot.main
    ```
4.  **Interact**:
    - Ask a policy question (e.g., "What is the sick leave policy?").
    - Apply for a leave (e.g., "I want to take leave from 20th May to 22nd May for a vacation").
    - Ask about your history (e.g., "How many leaves have I taken so far?").
    - Type `Bye` to exit and trigger thread-level evaluation.
5.  **Observe**:
    - Login to [Confident AI](https://www.confident-ai.com/).
    - Navigate to the **Project** and view the **Traces** and the **Threads**.
    - Verify that tool calls are captured and metrics are calculated.

---

## Assignment 3: DeepEval Offline Tests

### Goal
Run automated offline tests to validate the chatbot's performance on single-turn and multi-turn goldens.

### Steps

1.  **Activate the Virtual Environment**:
    - The `deepeval test run` command runs outside of `uv`, so activate the project's virtual environment first:
      ```bash
      source .venv/bin/activate
      ```
2.  **Setup Test Cases**:
    - Before running the tests, make sure the deepeval test cases are setup by running. These would create goldens in Confident AI:
      ```bash
      uv run python test/setup_deepeval.py
      ```
3.  **Single-Turn Tests**:
    - Ensure you have a golden dataset named `"Employee Chatbot Goldens"` in Confident AI (or modify `test/test_chatbot.py` to match your dataset alias).
    - Run the tests:
      ```bash
      deepeval test run test/test_chatbot.py
      ```
4.  **Multi-Turn Tests**:
    - Ensure you have a conversational golden dataset named `"Employee Chatbot Multi Turn Goldens"`.
    - Run the multi-turn simulation tests:
      ```bash
      deepeval test run test/test_multi_turn.py
      ```
5.  **Verify Results**:
    - Review the test results in the terminal.
    - Check the **Test Runs** section in Confident AI for detailed breakdowns of metric scores.

---

## Assignment 4: Langfuse Session Tracing

### Goal
Trace the chatbot to Langfuse and see every turn of a conversation grouped under a single **session**, attributed to the employee who ran it.

### Background
A single question to the chatbot produces one trace. That trace on its own tells you nothing about the conversation it belonged to. Langfuse **sessions** solve this by grouping related traces under a shared session ID, so you can replay a whole conversation in order.

This project sets that up with `propagate_attributes()` from the Langfuse SDK. It is a context manager that writes trace-level attributes into the OpenTelemetry context. Every span created inside it inherits them. See `src/employee_chatbot/utils/crew_executor.py`.

> [!IMPORTANT]
> `propagate_attributes()` must wrap the creation of the root span, not sit inside it. Only the currently active span and spans created after entering the context receive the attributes. Entering it too late is what gets the nested CrewAI and LiteLLM spans left out.

Two things make the propagation actually work:
1. `get_client()` installs Langfuse's own span processor on the global tracer provider. A hand-rolled OTLP exporter does not read propagated values out of the OTEL context, so nothing would be stamped onto spans.
2. The root span is created via `langfuse.start_as_current_observation()`. Langfuse's span processor drops spans that are neither its own nor from a known LLM instrumentor, so a hand-rolled tracer span would be silently discarded and the trace would be orphaned.

### Steps
1.  **Get your Langfuse keys**:
    - Sign up at [cloud.langfuse.com](https://cloud.langfuse.com).
    - Create an organization, then create a project (e.g. `employee-chatbot`). Each project has its own keys.
    - Go to **Project Settings → API Keys** and copy the public and secret keys.
2.  **Configure**: add `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_BASE_URL` to your `.env`.
3.  **Run the Langfuse entry point**:
    ```bash
    uv run python -m src.employee_chatbot.crew
    ```
4.  **Interact**: enter an Employee ID, then send at least three turns in the same run.
    - Ask a policy question (e.g., "What is the sick leave policy?").
    - Apply for a leave (e.g., "I want to take leave from 20th May to 22nd May for a vacation").
    - Ask about your history (e.g., "How many leaves have I taken so far?").
    - Type `Bye` to exit.
5.  **Observe** in the Langfuse dashboard:
    - **Sessions**: one session holding all three turns as separate traces, in order.
    - **Users**: traces attributed to the Employee ID you entered.
    - Open a trace and confirm the root span `employee-chatbot-turn` has input and output, with CrewAI agent, task and tool spans plus LiteLLM generation spans (including token usage) nested beneath it.
    - Click into a nested LiteLLM span and confirm it carries `session.id` and `user.id`. This is the proof that propagation reached the child spans, not just the root.
6.  **Deep Dive**:
    - The session ID is a fresh UUID per run, so one CLI run is one conversation. The same ID is reused as the AgentCore memory session.
    - Try passing `metadata={...}` or extra `tags` to `propagate_attributes()` and filter on them in the dashboard. Metadata values are coerced to strings and capped at 200 characters.
