"""Gemini provider adapter using the Google GenAI SDK."""

from __future__ import annotations

from google import genai

from leasegpt.errors import ProviderInvocationError


class GeminiAdapter:
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str, max_output_tokens: int) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        self._client = genai.Client(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            # google-genai returns response.text for text parts.
            return response.text or ""
        except Exception as exc:  # SDK error classes vary by transport/version.
            raise ProviderInvocationError(
                f"Gemini request failed for model '{self.model}': {exc}"
            ) from exc
