"""Provider adapter factory."""

from __future__ import annotations

from leasegpt.config import ProviderRuntimeConfig
from leasegpt.errors import ConfigError
from leasegpt.providers.anthropic_adapter import AnthropicAdapter
from leasegpt.providers.base import LLMAdapter
from leasegpt.providers.gemini_adapter import GeminiAdapter
from leasegpt.providers.openai_adapter import OpenAIAdapter


def create_adapter(config: ProviderRuntimeConfig) -> LLMAdapter:
    if config.provider == "openai":
        return OpenAIAdapter(
            api_key=config.api_key,
            model=config.model,
            max_output_tokens=config.max_output_tokens,
        )
    if config.provider == "anthropic":
        return AnthropicAdapter(
            api_key=config.api_key,
            model=config.model,
            max_output_tokens=config.max_output_tokens,
        )
    if config.provider == "gemini":
        return GeminiAdapter(
            api_key=config.api_key,
            model=config.model,
            max_output_tokens=config.max_output_tokens,
        )
    raise ConfigError(f"Unsupported provider: {config.provider}")
