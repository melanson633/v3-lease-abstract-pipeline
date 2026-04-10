"""Runtime configuration and provider key/model resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from leasegpt.errors import ConfigError

SUPPORTED_PROVIDERS = ("openai", "anthropic", "gemini")


@dataclass(slots=True)
class ProviderRuntimeConfig:
    provider: str
    api_key: str
    model: str
    max_output_tokens: int


DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-5",
    "anthropic": "claude-sonnet-4-5",
    "gemini": "gemini-2.0-flash",
}


def load_environment(dotenv_path: Path | None = None) -> None:
    """Load .env if present."""
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
        return
    load_dotenv(override=False)


def _resolve_provider_key(provider: str) -> str:
    if provider == "openai":
        value = os.getenv("OPENAI_API_KEY", "")
    elif provider == "anthropic":
        value = os.getenv("ANTHROPIC_API_KEY", "")
    elif provider == "gemini":
        value = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    else:
        raise ConfigError(f"Unsupported provider: {provider}")

    if not value:
        if provider == "gemini":
            raise ConfigError(
                "Missing Gemini API key. Set GEMINI_API_KEY (preferred) or GOOGLE_API_KEY."
            )
        raise ConfigError(
            f"Missing {provider} API key. Set the environment variable for this provider."
        )
    return value


def auto_select_provider() -> str:
    """Pick provider when exactly one provider key is configured."""
    present = []
    if os.getenv("OPENAI_API_KEY"):
        present.append("openai")
    if os.getenv("ANTHROPIC_API_KEY"):
        present.append("anthropic")
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        present.append("gemini")

    if not present:
        raise ConfigError(
            "No provider keys found. Set one of OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY/GOOGLE_API_KEY."
        )
    if len(present) > 1:
        raise ConfigError(
            "Multiple provider keys detected. Pass --provider to choose one explicitly."
        )
    return present[0]


def resolve_provider_config(
    provider: str | None,
    model: str | None,
    max_output_tokens: int = 4096,
) -> ProviderRuntimeConfig:
    selected = provider or auto_select_provider()
    if selected not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"Unsupported provider '{selected}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}."
        )
    key = _resolve_provider_key(selected)
    selected_model = model or os.getenv(f"LEASEGPT_{selected.upper()}_MODEL") or DEFAULT_MODELS[selected]
    return ProviderRuntimeConfig(
        provider=selected,
        api_key=key,
        model=selected_model,
        max_output_tokens=max_output_tokens,
    )
