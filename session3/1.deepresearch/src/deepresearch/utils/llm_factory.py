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


def get_llm(temperature: float = 0.0, model_env: str = "MODEL_ID") -> LLM:
    """Build an LLM from the model named by ``model_env``.

    The model is taken from the environment variable ``model_env`` (defaults to
    ``MODEL_ID``; pass ``"BETTER_MODEL_ID"`` for the stronger manager model).
    When ``MODEL_API_KEY`` is set it is passed through as the LLM's API key, and
    when ``MODEL_BASE_URL`` is set it is passed through as the LLM's base URL.
    """
    kwargs = {
        "model": os.environ[model_env],
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

    return LLM(**kwargs)
