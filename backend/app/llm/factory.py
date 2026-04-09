from app.llm.gemini import GeminiProvider
from app.llm.openai import OpenAIProvider
from app.llm.anthropic import AnthropicProvider
from app.config import Settings


def create_provider(provider_name: str, model: str, settings: Settings):
    match provider_name:
        case "gemini":
            return GeminiProvider(model=model, api_key=settings.google_api_key)
        case "openai":
            return OpenAIProvider(model=model, api_key=settings.openai_api_key)
        case "anthropic":
            return AnthropicProvider(model=model, api_key=settings.anthropic_api_key)
        case _:
            raise ValueError(f"Unknown LLM provider: {provider_name}")


def get_agent_provider(agent_name: str, settings: Settings):
    """Resolve per-agent provider overrides, falling back to defaults."""
    provider = getattr(settings, f"{agent_name}_provider", None) or settings.llm_provider
    model = getattr(settings, f"{agent_name}_model", None) or settings.llm_model
    return create_provider(provider, model, settings)
