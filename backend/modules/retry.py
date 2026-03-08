"""Retry utilities for transient OpenAI API failures."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import openai

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def call_openai_with_retry(
    callable: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 10,
    **kwargs: Any,
) -> T:
    """Call an async OpenAI function with exponential backoff retries.

    Args:
        callable: Async function to execute.
        *args: Positional arguments passed to callable.
        max_retries: Maximum number of retry attempts for transient errors.
        **kwargs: Keyword arguments passed to callable.

    Returns:
        Result returned by callable.

    Raises:
        openai.RateLimitError: When retries are exhausted.
        openai.APITimeoutError: When retries are exhausted.
        openai.APIConnectionError: When retries are exhausted.
        Exception: Any non-transient exception raised by callable.
    """
    transient_errors = (
        openai.RateLimitError,
        openai.APITimeoutError,
        openai.APIConnectionError,
    )

    retries = 0
    while True:
        try:
            return await callable(*args, **kwargs)
        except transient_errors:
            if retries >= max_retries:
                raise

            retries += 1
            wait_seconds = min(2**retries, 60)
            logger.warning(
                "Retrying OpenAI call after transient error (attempt %s/%s, wait=%ss)",
                retries,
                max_retries,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)
