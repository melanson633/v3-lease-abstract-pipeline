"""Custom exceptions for the LeaseGPT runtime."""


class LeaseGPTError(Exception):
    """Base exception for runtime and pipeline errors."""


class ConfigError(LeaseGPTError):
    """Raised when provider/runtime configuration is invalid."""


class InputValidationError(LeaseGPTError):
    """Raised when user input files or JSON payloads are invalid."""


class ProviderInvocationError(LeaseGPTError):
    """Raised when an upstream model provider request fails."""
