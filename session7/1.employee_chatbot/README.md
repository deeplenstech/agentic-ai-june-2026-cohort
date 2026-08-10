# Employee Chatbot: Policy & Leave Manager

## Purpose

Welcome to the **Employee Chatbot** project, powered by [crewAI](https://crewai.com), [Langfuse](https://langfuse.com/) and [DeepEval](https://github.com/confident-ai/deepeval).

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
- **Session-Level Tracing**: Every turn of a run is traced to [Langfuse](https://langfuse.com/) and grouped under one session, attributed to the employee.
- **Online Evaluation**: Those traces can be scored automatically by a Langfuse LLM-as-a-judge evaluator (e.g. Conciseness), with the score attached to the trace.
- **Offline Evaluation**: Test suite for single-turn and multi-turn scenarios using DeepEval, with goldens stored locally as JSON. Nothing is pushed to a hosted evaluation platform.

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

### Environment Variables

| Variable | Description |
| :--- | :--- |
| `MODEL_ID` | The model ID used by the agent (e.g., `bedrock/us.anthropic.claude-sonnet-4-6`). Required. |
| `MODEL_API_KEY` | API key for the model provider. Optional. Only needed when the provider is not authenticated another way (e.g., AWS credentials for Bedrock). |
| `MODEL_BASE_URL` | Base URL for the model provider. Optional. Useful for OpenAI-compatible gateways. |
| `BEDROCK_KB_ID` | The ID of your Amazon Bedrock Knowledge Base (setup similarly to Session 5 assignments). Required. |
| `MEMORY_ID` | Amazon Bedrock AgentCore memory ID. Optional. Memory is skipped when empty. Set it up as in the Session 5 assignments. |
| `MEMORY_SUMMARY_STRATEGY_ID` | AgentCore summary strategy ID. Optional. Summaries are skipped when empty. |
| `LANGFUSE_PUBLIC_KEY` | Public key from [Langfuse](https://cloud.langfuse.com). Optional. Tracing is only activated when this is set. |
| `LANGFUSE_SECRET_KEY` | Secret key from Langfuse. |
| `LANGFUSE_BASE_URL` | Langfuse host. Defaults to `https://cloud.langfuse.com`. |
| `OPENAI_API_KEY` | Required by DeepEval for the offline test metrics and the conversation simulator. |

> [!NOTE]
> Ensure your AWS credentials are configured (via `~/.aws/credentials` or environment variables) with permissions for Bedrock and the Knowledge Base.

## Running the Chatbot

There is a single entry point:

```bash
cd session7/1.employee_chatbot
uv run python -m src.employee_chatbot.crew
```

You are asked for an Employee ID first, then for queries. Type `Bye` to exit.

---

## Assignment 1: Online Evaluation with Langfuse

### Goal
Have an **LLM-as-a-judge evaluator** (e.g. Conciseness) score the chatbot's live traffic in Langfuse automatically, and read the score back on the trace.

### Background
An evaluator is a judge prompt that Langfuse runs server-side on traces as they arrive. The resulting **score** is attached to the trace it judged. This is online evaluation. It grades real traffic.

The unit of evaluation is one trace, which here is one turn of the conversation. Langfuse groups the turns of a run under a **session** so you can replay the conversation, but sessions cannot be evaluated. Judge the turns.

Nothing in this repo has to change for the assignment. The evaluator reads what `execute_crew()` already records on the root span `employee-chatbot-turn`: the input is the crew inputs dict (`employee_id`, `employee_query`) and the output is the assistant's reply.

### Steps
1.  **Get your Langfuse keys**:
    - Sign up at [cloud.langfuse.com](https://cloud.langfuse.com).
    - Create an organization, then create a project (e.g. `employee-chatbot`). Each project has its own keys.
    - Go to **Project Settings → API Keys** and copy the public and secret keys.
2.  **Configure**: add `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_BASE_URL` to your `.env`.
3.  **Run the chatbot**:
    ```bash
    uv run python -m src.employee_chatbot.crew
    ```
4.  **Interact**: enter an Employee ID, then send couple of turns in the same run.
    - Ask a policy question (e.g., "What is the sick leave policy?").
    - Apply for a leave (e.g., "I want to take casual leave from coming Monday for 3 days").
    - Ask about your history (e.g., "How many leaves have I taken so far?").
    - Type `Bye` to exit.
5.  **Confirm the traces arrived**: in the Langfuse dashboard, open one trace and check that the root span `employee-chatbot-turn` has both an input and an output. That pair is what the judge will read, so an empty one means the evaluator has nothing to score. Ensure the `type` filter on the left has only `SPAN` selected. And `Is Root Observation` has `True` selected.
6.  **Add a judge model**: go to **Project Settings → LLM Connections** and add a provider key (OpenAI, Anthropic, Azure OpenAI or AWS Bedrock). This provider would be used for `LLM as a judge` in subsequent steps. This Readme was tested with OpenAI. 
7.  **Create the evaluator**: go to **Evaluation → Evaluators → Set up Evaluator**.
    - Pick the managed **Conciseness** evaluator from the Langfuse library, or write a custom one with your own prompt, `{{variables}}` and score type (numeric, boolean or categorical).
    - **Filter**: restrict it to trace name `employee-chatbot-turn`. Also restrict to `Is Root Observation` with value `True`. Without a filter the judge also fires on the nested CrewAI and LiteLLM spans, which costs tokens and scores things you do not care about. 
    - **Variable mapping**: map the judge's output/generation variable to the trace **Output**. For the query variable, map to the trace **Input** with the JSONPath `$.employee_query`, since the input is the crew inputs dict, not a bare string. Use the live preview to confirm the populated prompt looks right.
    - **Sampling**: 100% while you are learning. Lower it once you understand the token cost.
8.  **Generate scored traces**: evaluators run on traces that arrive after they are created, so run the chatbot again and send a few more turns.
9.  **Read the score back**:
    - Open one of the new traces and find the **Conciseness** score, with the judge's reasoning as a comment.
    - Check the **Scores** column in the trace list, and filter the list by that score to find the worst turns.
10. **Deep Dive**:
    - Ask the same question twice, once plainly and once with "explain in as much detail as possible", and compare the two Conciseness scores.
    - Add a second evaluator (e.g. Helpfulness or Toxicity) and see both scores land on the same trace.
    - Read a low score's reasoning, then decide whether you trust it. An online judge is itself an LLM call, and an unreliable judge produces confident numbers about nothing.

---

## Assignment 2: Offline Evaluation with DeepEval

### Goal
Run automated offline tests to validate the chatbot's performance on single-turn and multi-turn goldens, before a change ships.

### Background
Where Assignment 1 grades live conversations after the fact, this grades a fixed dataset on demand, so a regression shows up in a test run instead of in production traces.

Goldens live as JSON files under `test/data/`, loaded by `test/utils/goldens.py`. They are checked into the repo. `test/setup_deepeval.py` regenerates them by running the crew and recording its answers plus the tools it called.

The single-turn suite scores each answer on `AnswerRelevancyMetric`, a `Correctness` GEval metric, and `ToolCorrectnessMetric`. The multi-turn suite drives the crew through DeepEval's `ConversationSimulator` and scores the conversation on `TurnRelevancyMetric` and `ConversationCompletenessMetric`.

### Steps

1.  **Activate the Virtual Environment**:
    - The `deepeval test run` command runs outside of `uv`, so activate the project's virtual environment first:
      ```bash
      source .venv/bin/activate
      ```
2.  **(Optional) Regenerate the Goldens**:
    - The goldens are already committed. Regenerate them only if you changed the agent, the tools or the knowledge base:
      ```bash
      uv run python test/setup_deepeval.py
      ```
    - This overwrites `test/data/employee_chatbot_goldens.json` and `test/data/employee_chatbot_multi_turn_goldens.json`. The expected outputs become whatever the crew answers on that run, so review the printed baseline responses before trusting them.
3.  **Single-Turn Tests**:
    ```bash
    deepeval test run test/test_chatbot.py
    ```
4.  **Multi-Turn Tests**:
    ```bash
    deepeval test run test/test_multi_turn.py
    ```
    - The simulator generates user turns with the DeepEval model, so `OPENAI_API_KEY` must be set.
5.  **Verify Results**:
    - Review the metric scores and failure reasons printed in the terminal.
    - Investigate failures against the Langfuse traces from the same run.

> [!NOTE]
> Run both commands from the project root. The tests import helpers as `test.utils.*`, which only resolves from there.

---
