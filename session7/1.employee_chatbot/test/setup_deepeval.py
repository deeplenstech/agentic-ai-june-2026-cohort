import sys
import os
import uuid
import warnings
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Ensure the src directory is in the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# Put the project root first so `test.*` imports resolve to this package rather
# than the standard library's `test` package. This mirrors what pytest does.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from employee_chatbot.crew import create_crew
from deepeval.dataset import EvaluationDataset, Golden, ConversationalGolden
from test.utils.tool_tracker import ToolCallTracker

# Goldens are stored locally as JSON. The test suite reads them back from here,
# so nothing is pushed to or pulled from a hosted platform.
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def generate_and_save_dataset():
    console = Console()
    console.print("[bold cyan]Starting Golden Dataset Generation...[/bold cyan]")

    # Define a list of test queries to bootstrap the golden dataset
    test_queries = [
        "What is the policy for earned leaves?",
        "How many leaves have I taken so far?",
        "I want to apply for 2 days of sick leave starting tomorrow."
    ]

    goldens = []

    for query in test_queries:
        console.print(f"\n[bold blue]Processing Query:[/bold blue] {query}")

        inputs = {
            'employee_query': query,
            'employee_id': str(uuid.uuid4())
        }

        try:
            # ToolCallTracker records which tools the agent calls during this
            # run. Those names become the ground-truth expected_tools for this
            # golden, enabling trajectory evaluation in the test suite.
            with ToolCallTracker() as tracker:
                crew = create_crew()
                response = crew.kickoff(inputs=inputs).raw

            console.print(f"[bold green]Baseline Response Captured:[/bold green]\n{response}")
            console.print(f"[bold yellow]Tools called:[/bold yellow] {tracker.tool_names}")

            # Create a Golden object with expected_tools baked in
            golden = Golden(
                input=query,
                expected_output=response,
                expected_tools = tracker.tool_calls
            )
            goldens.append(golden)

        except Exception as e:
            console.print(f"[bold red]An error occurred generating golden for query '{query}': {e}[/bold red]")
            continue

    if not goldens:
        console.print("[bold red]No goldens were generated. Aborting save.[/bold red]")
        return

    # Create the Evaluation Dataset
    console.print("\n[bold cyan]Saving the EvaluationDataset to local JSON...[/bold cyan]")
    try:
        dataset = EvaluationDataset(goldens=goldens)
        path = dataset.save_as(
            file_type="json",
            directory=DATA_DIR,
            file_name="employee_chatbot_goldens",
        )
        console.print(f"[bold green]Saved {len(goldens)} single-turn goldens to {path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to save dataset: {e}[/bold red]")

def generate_and_save_multi_turn_dataset():
    console = Console()
    console.print("\n[bold cyan]Saving the multi-turn EvaluationDataset to local JSON...[/bold cyan]")

    goldens = [
        ConversationalGolden(
            scenario="Manpreet wants to go for a long vacation starting from the first working day of the coming month and wants to apply earned leave for the same. Manpreet's leave is already approved. This multi-turn interaction will be turn by turn. In the first turn, Manpreet wants to first check how many earned leaves are possible in a calendar year. And then in the second turn, Manpreet wants to check how many earned leaves he has taken in this calendar year. And then in the last turn Manpreet wants to apply for remaining possible earned leaves. While applying leaves, Manpreet wants to ignore Saturdays and Sundays before applying leaves. And hence multiple applications of earned leave might need to be submitted.",
            expected_outcome="Maximum earned leaves submitted into the system.",
            user_description="Manpreet is an employee of DeepLens."
        )
    ]

    try:
        dataset = EvaluationDataset(goldens=goldens)
        path = dataset.save_as(
            file_type="json",
            directory=DATA_DIR,
            file_name="employee_chatbot_multi_turn_goldens",
        )
        console.print(f"[bold green]Saved {len(goldens)} multi-turn golden(s) to {path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to save multi-turn dataset: {e}[/bold red]")

if __name__ == "__main__":
    generate_and_save_dataset()
    generate_and_save_multi_turn_dataset()
