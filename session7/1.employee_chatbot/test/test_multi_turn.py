import sys
import os
import uuid
from typing import List
from dotenv import load_dotenv
import pytest
from deepeval import assert_test
from deepeval.test_case import Turn
from deepeval.simulator import ConversationSimulator
from deepeval.metrics import TurnRelevancyMetric, ConversationCompletenessMetric
from crewai.hooks import clear_before_llm_call_hooks

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

load_dotenv()

from employee_chatbot.crew import create_crew
from employee_chatbot.utils.memory import MemoryUtils
from employee_chatbot.utils.llm_hooks import LLMHooks

from test.utils.goldens import load_dataset

dataset = load_dataset("employee_chatbot_multi_turn_goldens")

relevancy = TurnRelevancyMetric()
conversationCompleteness = ConversationCompletenessMetric()


@pytest.fixture
def memory():
    """
    Fresh memory session per golden.

    ``before_llm_call`` registers into a process-global hook list, so the
    registration has to be undone after each test or hooks from earlier
    goldens keep firing against a stale memory session.
    """
    memoryUtils = MemoryUtils(sessionId=str(uuid.uuid4()), actorId=str(uuid.uuid4()))
    LLMHooks(memoryUtils).register()
    try:
        yield memoryUtils
    finally:
        clear_before_llm_call_hooks()


@pytest.mark.parametrize("golden", dataset.goldens)
def test_multi_turn(golden, memory):
    # Wrap your chatbot in a callback func
    def model_callback(turns: List[Turn]) -> Turn:
        # 1. Get latest simulated user input
        user_input = turns[-1].content

        # 2. Call chatbot
        inputs = {
            'employee_query': user_input,
            'employee_id': memory.actorId
        }

        crew = create_crew()
        response = crew.kickoff(inputs=inputs).raw
        memory.saveMemory(userPrompt=user_input, assistantResponse=response)

        # 3. Return chatbot turn
        return Turn(role="assistant", content=response)

    # async_mode=False is required: the callback is synchronous, and DeepEval's
    # async path would invoke crew.kickoff() from inside a running event loop,
    # which CrewAI rejects.
    simulator = ConversationSimulator(model_callback=model_callback, async_mode=False)
    test_cases = simulator.simulate(conversational_goldens=[golden])

    assert_test(test_cases[0], [relevancy, conversationCompleteness])
