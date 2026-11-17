"""HTTP session helpers for provider adapters."""

from __future__ import annotations

import contextlib
import socket
import time
from typing import Any

import requests
import urllib3.util.connection as connection

_RETRY_STATUSES_IDEMPOTENT = frozenset({429, 500, 502, 503, 504})
_RETRY_STATUSES_POST = frozenset({429})


def prefer_ipv4_session() -> requests.Session:
    """Return a requests session that prefers IPv4.

    Some development hosts resolve dual-stack services to IPv6 first but have no
    IPv6 route, which makes a default requests call hang. Provider tests inject
    their own fake session; this helper is only used for the real adapter.
    """

    connection.allowed_gai_family = lambda: socket.AF_INET
    return requests.Session()


def request_with_retries(
    session: Any,
    method: str,
    url: str,
    *,
    idempotent: bool = False,
    retries: int = 2,
    backoff: float = 0.5,
    sleep=time.sleep,
    **kwargs: Any,
):
    """Call a requests-like session with a small bounded retry policy.

    A POST is not retried on a generic 5xx because the provider may have
    processed it before the response was lost. It is retried only on 429,
    which means the request was not accepted.
    """

    call = getattr(session, method.lower())
    retry_statuses = (
        _RETRY_STATUSES_IDEMPOTENT if idempotent else _RETRY_STATUSES_POST
    )
    attempts = max(0, retries)
    for attempt in range(attempts + 1):
        try:
            response = call(url, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if attempt >= attempts:
                raise
            sleep(backoff * (2**attempt))
            continue
        if response.status_code in retry_statuses and attempt < attempts:
            delay = backoff * (2**attempt)
            headers = getattr(response, "headers", None) or {}
            retry_after = (
                headers.get("Retry-After") if hasattr(headers, "get") else None
            )
            if retry_after:
                with contextlib.suppress(TypeError, ValueError):
                    delay = max(delay, float(retry_after))
            sleep(delay)
            continue
        return response
    raise AssertionError("unreachable retry state")
