"""Form objects for leave-request UI workflows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CancelRequestForm:
    """Represents and validates cancellation input from an employee.

    Args:
        cancellation_reason: Employee-provided cancellation reason text.
    """

    cancellation_reason: str

    def cleaned_reason(self) -> str:
        """Return trimmed cancellation reason or raise a validation error.

        Returns:
            Trimmed non-empty cancellation reason.

        Raises:
            ValueError: If the reason is empty after trimming whitespace.
        """
        cleaned = self.cancellation_reason.strip()
        if not cleaned:
            raise ValueError("Cancellation reason is required")
        return cleaned
