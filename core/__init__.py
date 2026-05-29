"""
Backward-compatible wrapper — delegates to infrastructure.errors.
"""
from infrastructure.errors import FateTellError, NotFoundError, ValidationError, PaymentError  # noqa: F401
