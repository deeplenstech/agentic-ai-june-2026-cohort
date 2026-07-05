import os

from crewai import LLM

# Some upstream providers (notably OpenRouter's free ":free" models) are served
# on shared, capacity-limited backends that intermittently reply with an
# HTTP-200 body carrying an error (e.g. Nvidia "ResourceExhausted") and
# ``choices: null``. Routing through LiteLLM (``is_litellm=True``) surfaces
# those error bodies as proper, retryable exceptions, and ``num_retries`` is
# forwarded to ``litellm.completion`` so transient upstream exhaustion is
# retried instead of aborting the whole crew run.
NUM_RETRIES = 3


def _build_litellm_llm(kwargs: dict) -> LLM:
    """Build a CrewAI LLM while keeping Gemini on LiteLLM.

    CrewAI 1.15 imports its native Gemini provider before it honors
    ``is_litellm=True``. That makes ``gemini/...`` model IDs fail unless the
    native Google extra is installed, even though we want LiteLLM to handle the
    call. Allocate with a neutral provider prefix, then initialize with the real
    LiteLLM model so capability checks still see ``gemini/...``.
    """
    model = kwargs["model"]
    if model.startswith(("gemini/", "google/")):
        placeholder_model = f"litellm_passthrough/{model.rsplit('/', 1)[-1]}"
        llm = LLM.__new__(LLM, model=placeholder_model, is_litellm=True)
        LLM.__init__(llm, **kwargs)
        return llm

    return LLM(**kwargs)


def get_llm(temperature: float = 0.0) -> LLM:
    """Build an LLM from ``MODEL_ID``.

    The model is always taken from the ``MODEL_ID`` environment variable. When
    ``MODEL_API_KEY`` is set it is passed through as the LLM's API key, and when
    ``MODEL_BASE_URL`` is set it is passed through as the LLM's base URL.
    """
    kwargs = {
        "model": os.environ["MODEL_ID"],
        "temperature": temperature,
        "is_litellm": True,
        "num_retries": NUM_RETRIES,
    }

    api_key = os.getenv("MODEL_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key

    base_url = os.getenv("MODEL_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url

    return _build_litellm_llm(kwargs)
