"""Custom exceptions for the AI Gateway application."""


class AIGatewayException(Exception):
    """Base exception for AI Gateway."""

    pass


class RateLimitException(AIGatewayException):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutException(AIGatewayException):
    """Raised when a timeout occurs."""

    pass


class ProviderException(AIGatewayException):
    """Raised when a provider error occurs."""

    def __init__(self, message: str, provider: str, status_code: int = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class GuardrailViolationException(AIGatewayException):
    """Raised when a guardrail violation occurs."""

    def __init__(self, message: str, violations: list):
        super().__init__(message)
        self.violations = violations


class BudgetExceededException(AIGatewayException):
    """Raised when budget is exceeded."""

    def __init__(self, message: str = "Budget exceeded", current_spend: float = None, limit: float = None):
        super().__init__(message)
        self.current_spend = current_spend
        self.limit = limit


class AuthenticationException(AIGatewayException):
    """Raised when authentication fails."""

    pass


class ValidationException(AIGatewayException):
    """Raised when validation fails."""

    pass


class CacheException(AIGatewayException):
    """Raised when cache operation fails."""

    pass


class DatabaseException(AIGatewayException):
    """Raised when database operation fails."""

    pass

