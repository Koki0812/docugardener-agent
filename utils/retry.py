"""Retry utilities with exponential backoff for DocuAlign AI.

Provides decorators and utilities for automatic retry of transient failures,
particularly for external API calls (Gemini, Firestore, Drive).
"""
import time
import logging
import functools
from typing import Any, Callable

logger = logging.getLogger(__name__)


# Default retryable exceptions
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
)

# Try to import Google Cloud specific exceptions
try:
    from google.api_core import exceptions as gcp_exceptions
    RETRYABLE_EXCEPTIONS = RETRYABLE_EXCEPTIONS + (
        gcp_exceptions.ServiceUnavailable,
        gcp_exceptions.DeadlineExceeded,
        gcp_exceptions.TooManyRequests,
        gcp_exceptions.InternalServerError,
    )
except ImportError:
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS,
) -> Callable:
    """Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay cap in seconds
        retryable_exceptions: Tuple of exception types to retry on
        
    Returns:
        Decorated function with retry logic
        
    Usage:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        def call_gemini_api(prompt: str):
            return model.generate_content(prompt)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{max_retries + 1} "
                        f"failed: {e}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
            
            raise last_exception  # Should never reach here, but just in case
        
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern to prevent cascade failures.
    
    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Too many failures, requests are rejected immediately
        HALF_OPEN: Testing if service has recovered
    
    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        try:
            result = breaker.call(api_function, arg1, arg2)
        except CircuitBreakerOpenError:
            # Service is down, use fallback
        except Exception:
            # Original error from api_function
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before trying again (half-open)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "closed"
        self.last_failure_time: float = 0.0
    
    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute function through circuit breaker.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from func
        """
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half_open"
                logger.info(f"🔄 Circuit breaker half-open, testing recovery...")
            else:
                remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Recovery in {remaining:.0f}s. "
                    f"({self.failures} consecutive failures)"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Record successful call."""
        if self.state == "half_open":
            logger.info("✅ Circuit breaker recovered, closing circuit")
        self.failures = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Record failed call."""
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.error(
                f"🔴 Circuit breaker OPEN after {self.failures} failures. "
                f"Will retry in {self.recovery_timeout}s."
            )

    @property
    def is_available(self) -> bool:
        """Check if service is available (circuit not open)."""
        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                return True
            return False
        return True


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and requests are rejected."""
    pass


# Pre-configured circuit breakers for external services
gemini_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
firestore_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
drive_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
