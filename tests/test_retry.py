"""Tests for utils/retry.py — exponential backoff and circuit breaker."""
import time
import pytest
from utils.retry import retry_with_backoff, CircuitBreaker, CircuitBreakerOpenError


# ---------------------------------------------------------------------------
# retry_with_backoff tests
# ---------------------------------------------------------------------------

class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""

    def test_success_no_retry(self):
        """Function succeeds on first call — no retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        assert result == "ok"
        assert call_count == 1

    def test_retry_then_succeed(self):
        """Function fails twice then succeeds on third attempt."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient error")
            return "recovered"

        result = fail_twice()
        assert result == "recovered"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Function fails all attempts — raises last exception."""
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fail():
            raise TimeoutError("always fails")

        with pytest.raises(TimeoutError, match="always fails"):
            always_fail()

    def test_non_retryable_exception_not_retried(self):
        """Non-retryable exceptions are raised immediately."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, retryable_exceptions=(ConnectionError,))
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            raise_value_error()
        assert call_count == 1  # No retry

    def test_backoff_delay_increases(self):
        """Verify delay increases with each retry (exponential)."""
        call_count = 0
        call_times = []

        @retry_with_backoff(max_retries=2, base_delay=0.05, max_delay=1.0)
        def track_timing():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise ConnectionError("retry")
            return "done"

        track_timing()
        assert len(call_times) == 3
        # Second delay should be roughly 2x the first
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        assert delay2 > delay1 * 1.5  # Allow some margin


# ---------------------------------------------------------------------------
# CircuitBreaker tests
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_closed_state_passes_through(self):
        """Normal operation — calls pass through."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        result = breaker.call(lambda: "ok")
        assert result == "ok"
        assert breaker.state == "closed"

    def test_opens_after_threshold(self):
        """Circuit opens after reaching failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert breaker.state == "open"
        assert breaker.failures == 3

    def test_open_rejects_immediately(self):
        """When open, calls are rejected with CircuitBreakerOpenError."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        # Force open
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
            except RuntimeError:
                pass

        assert breaker.state == "open"
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "should not execute")

    def test_half_open_recovery(self):
        """After recovery timeout, circuit goes half-open and recovers on success."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)

        # Force open
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
            except RuntimeError:
                pass

        assert breaker.state == "open"

        # Wait for recovery
        time.sleep(0.1)

        # Should succeed and close
        result = breaker.call(lambda: "recovered")
        assert result == "recovered"
        assert breaker.state == "closed"
        assert breaker.failures == 0

    def test_is_available_property(self):
        """is_available returns correct state."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        assert breaker.is_available is True

        try:
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        except RuntimeError:
            pass

        assert breaker.is_available is False

    def test_success_resets_failures(self):
        """Successful call resets failure count."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        # Fail once
        try:
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("x")))
        except RuntimeError:
            pass
        assert breaker.failures == 1

        # Succeed
        breaker.call(lambda: "ok")
        assert breaker.failures == 0
