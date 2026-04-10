"""Provider adapter interface."""

from __future__ import annotations

from typing import Protocol


class LLMAdapter(Protocol):
    provider_name: str
    model: str

    def generate_text(self, prompt: str) -> str:
        """Generate text completion for the given prompt."""
