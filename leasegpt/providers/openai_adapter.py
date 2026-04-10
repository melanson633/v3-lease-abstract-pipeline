"""OpenAI provider adapter using the Responses API."""

from __future__ import annotations

from openai import OpenAI
from openai import OpenAIError

from leasegpt.errors import ProviderInvocationError


class OpenAIAdapter:
    provider_name = "openai"

    def __init__(self, api_key: str, model: str, max_output_tokens: int) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = OpenAI(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        try:
            response = self._client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=self.max_output_tokens,
            )
            return response.output_text
        except OpenAIError as exc:
            raise ProviderInvocationError(
                f"OpenAI request failed for model '{self.model}': {exc}"
            ) from exc
