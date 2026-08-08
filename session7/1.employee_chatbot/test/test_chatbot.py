import sys
import os
import uuid
import pytest
from dotenv import load_dotenv

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

load_dotenv()

from deepeval.metrics import AnswerRelevancyMetric, GEval, ToolCorrectnessMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import assert_test
from employee_chatbot.crew import create_crew

from test.utils.tool_tracker import ToolCallTracker
from test.utils.goldens import load_dataset

# 1. Load the golden dataset from local JSON
dataset = load_dataset("employee_chatbot_goldens")

# 2. Define the metrics to evaluate
answer_relevancy_metric = AnswerRelevancyMetric(threshold=0.5)

correctness_metric = GEval(
    name="Correctness",
    criteria="Determine whether the actual output accurately conveys the same information and intent as the expected output, answering the user's query.",
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    threshold=0.5
)

# ToolCorrectnessMetric checks that the agent called the right tools
# (matched against the expected_tools recorded on each golden).
tool_correctness_metric = ToolCorrectnessMetric(threshold=0.9, should_consider_ordering=True)

# 3. Parametrize the test function to run for every golden in the dataset
@pytest.mark.parametrize("golden", dataset.goldens)
def test_employee_chatbot_response(golden):
    # ── Trajectory capture via CrewAI event bus ───────────────────────────
    # ToolCallTracker subscribes to ToolUsageFinishedEvent for the duration
    # of the with-block, then tears down automatically — no handler leakage.
    with ToolCallTracker() as tracker:
        crew = create_crew()

        inputs = {
            'employee_query': golden.input,
            'employee_id': str(uuid.uuid4()),  # mock employee ID per run
        }

        # Execute the crew — ToolUsageFinishedEvent fires for every tool call
        actual_output = crew.kickoff(inputs=inputs).raw

    # ── Assemble DeepEval test case ───────────────────────────────────────
    test_case = LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        expected_output=golden.expected_output,
        tools_called=tracker.tool_calls,
        expected_tools=golden.expected_tools,
    )

    metrics = [answer_relevancy_metric, correctness_metric, tool_correctness_metric]

    assert_test(test_case, metrics)
