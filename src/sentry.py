"""Sentry integration for error tracking."""

import os
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


def init_sentry(dsn: str = None, environment: str = None, release: str = None) -> None:
    """
    Initialize Sentry for error tracking.
    
    Args:
        dsn: Sentry DSN (or SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version
    """
    dsn = dsn or os.getenv("SENTRY_DSN")
    environment = environment or os.getenv("SENTRY_ENVIRONMENT", "production")
    release = release or os.getenv("SENTRY_RELEASE", "apas@0.1.0-canary")
    
    if not dsn:
        print("⚠️ Sentry DSN not configured. Error tracking disabled.")
        return
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        # Configure logging integration
        integrations=[
            LoggingIntegration(
                level=os.getenv("SENTRY_LOG_LEVEL", "ERROR"),  # Capture errors and above
                breadcrumb_level=logging.INFO,  # Breadcrumbs for info and above
            ),
        ],
    )
    
    print(f"✅ Sentry initialized: {environment} / {release}")


def capture_exception(exception: Exception, **kwargs) -> None:
    """
    Capture an exception with Sentry.
    
    Args:
        exception: The exception to capture
        **kwargs: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **kwargs) -> None:
    """
    Capture a message with Sentry.
    
    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, critical)
        **kwargs: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def set_user(user_id: int, username: str = None) -> None:
    """
    Set user context for Sentry.
    
    Args:
        user_id: Telegram user ID
        username: Telegram username
    """
    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
    })


def add_breadcrumb(category: str, message: str, level: str = "info", **kwargs) -> None:
    """
    Add a breadcrumb for debugging.
    
    Args:
        category: Breadcrumb category
        message: Breadcrumb message
        level: Severity level
        **kwargs: Additional data
    """
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=kwargs,
    )
