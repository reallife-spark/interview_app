"""HTTP session helpers for provider adapters."""

from __future__ import annotations

import socket

import requests
import urllib3.util.connection as connection


def prefer_ipv4_session() -> requests.Session:
    """Return a requests session that prefers IPv4.

    Some development hosts resolve dual-stack services to IPv6 first but have no
    IPv6 route, which makes a default requests call hang. Provider tests inject
    their own fake session; this helper is only used for the real adapter.
    """

    connection.allowed_gai_family = lambda: socket.AF_INET
    return requests.Session()
