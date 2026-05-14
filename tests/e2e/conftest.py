"""Spin up a local HTTP server serving docs/ for the duration of the e2e session.

Each test gets `base_url` (e.g. http://127.0.0.1:8769) and can navigate to
relative paths via Playwright's `page.goto("/")`.
"""

from __future__ import annotations

import http.server
import socket
import socketserver
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # silence access logs
        pass


@pytest.fixture(scope="session")
def docs_server():
    port = _free_port()

    class _Handler(_QuietHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(DOCS), **kw)

    httpd = socketserver.TCPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


@pytest.fixture(scope="session")
def base_url(docs_server):
    return docs_server


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    # Default viewport: desktop. Individual tests can override via fixture.
    return {**browser_context_args, "viewport": {"width": 1280, "height": 900}}
