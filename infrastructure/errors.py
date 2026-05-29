"""
Error hierarchy — framework-agnostic, used across all layers.

All framework-specific error handling lives in web middleware.
"""


class FateTellError(Exception):
    """Base for all application-level errors."""
    status_code: int = 500
    public_message: str = "An unexpected error occurred."

    def __init__(self, message: str = "", detail: str = ""):
        self.message = message or self.public_message
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(FateTellError):
    """Resource not found."""
    status_code = 404
    public_message = "Resource not found."


class ValidationError(FateTellError):
    """Invalid input data."""
    status_code = 400
    public_message = "Invalid input."


class PaymentError(FateTellError):
    """Payment processing failure."""
    status_code = 402
    public_message = "Payment processing failed."
