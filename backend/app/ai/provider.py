"""AI integration boundary.

The provider only *explains* findings the deterministic backend has already calculated and
validated. It must never calculate financial totals, generate candidates, decide feasibility or
approve changes. No vendor SDK is wired in yet; see DESIGN.md section 8.
"""

from typing import Any, Protocol


class ExplanationProvider(Protocol):
    """Implemented by a hosted-API adapter now, and an open-weight inference adapter later."""

    name: str

    def explain(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Return a structured explanation for a bounded, validated evidence object."""
        ...


class ProviderNotConfiguredError(RuntimeError):
    pass


class NotConfiguredProvider:
    name = "not-configured"

    def explain(self, evidence: dict[str, Any]) -> dict[str, Any]:
        raise ProviderNotConfiguredError("No AI explanation provider is configured")


def get_explanation_provider() -> ExplanationProvider:
    return NotConfiguredProvider()
