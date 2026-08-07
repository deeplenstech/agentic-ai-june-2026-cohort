import logging

from crewai.hooks import before_llm_call

from .memory import MemoryUtils

logger = logging.getLogger(__name__)


class LLMHooks:
    """
    Registers CrewAI LLM hooks for the employee chatbot.

    - Memory (``_register_memory``): a pre-LLM hook that loads the
      conversation's memory, and session summary and 
      injects it ahead of the current query so the agent answers 
      with context of prior turns.
    """

    def __init__(self, memory: MemoryUtils):
        self.memory = memory

    def register(self):
        self._register_memory()

    # ── memory ───────────────────────────────────────────────────────
    def _register_memory(self):
        """Register the pre-LLM hook that loads memory."""

        @before_llm_call
        def load_memory_before_llm(context):
            """Load memory and inject it ahead of the current query."""
            if self.memory is None or not context.messages:
                return None

            try:
                history = self.memory.loadShortTermMemory()
                summary = self.memory.extractSummary()
            except Exception as e:
                logger.error(f"Failed to load memory: {str(e)}")
                return None

            if not history:
                return None

            # Avoid re-injecting on subsequent LLM calls within the same run
            # (e.g. after tool calls) where memory is already present.
            existing = {(m.get("role"), m.get("content")) for m in context.messages}
            history = [
                turn for turn in history
                if (turn.get("role"), turn.get("content")) not in existing
            ]
            if not history:
                return None

            # Inject history right after the first system message, so it sits
            # ahead of the conversation but below the system prompt.
            first_system = next(
                (i for i, m in enumerate(context.messages)
                 if m.get("role") == "system"),
                None,
            )
            insert_at = first_system + 1 if first_system is not None else 0
            offset = 0
            if summary:
                context.messages.insert(insert_at, summary)
                offset = 1
            context.messages[insert_at+offset:insert_at+offset] = history

            logger.info(f"Injected {len(history)} short-term memory message(s).")
            return None