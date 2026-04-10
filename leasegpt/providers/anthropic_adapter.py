"""Anthropic provider adapter using the Messages API."""

from __future__ import annotations

from anthropic import Anthropic
from anthropic import APIError as AnthropicAPIError

from leasegpt.errors import ProviderInvocationError


class AnthropicAdapter:
    provider_name = "anthropic"

    def __init__(self, api_key: str, model: str, max_output_tokens: int) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = Anthropic(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=self.max_output_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            text_parts = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text_parts.append(block.text)
            return "\n".join(text_parts).strip()
        except AnthropicAPIError as exc:
            raise ProviderInvocationError(
                f"Anthropic request failed for model '{self.model}': {exc}"
            ) from exc
