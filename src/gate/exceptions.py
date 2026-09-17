"""
Exception hierarchy for Bidirectional Neural Knowledge Gate contracts.
"""


class GateContractError(Exception):
    """Base exception for all Neural Knowledge Gate contract violations."""
    pass


class GateValidationError(GateContractError):
    """Raised when a query, response, or experience payload fails structural validation."""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message)
        self.field = field
        self.details = details or {}


class GateTransportError(GateContractError):
    """Raised when transport, serialization, or network layer interactions fail."""
    pass
