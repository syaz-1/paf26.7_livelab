"""Streamable HTTP MCP protected by a pre-shared lab bearer token and TLS.

This is direct bearer authentication for PAF, not an OAuth authorization server.
"""
from __future__ import annotations

import hmac
import os
import ssl
from pathlib import Path
from urllib.parse import urlsplit

import uvicorn
import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import Field
from typing import Annotated

import collectors


class FixedToolsMCP(FastMCP):
    async def call_tool(self, name, arguments):
        # Reject extra target/command arguments instead of letting the SDK's
        # permissive argument model silently discard them.
        parameters = {"get_host_summary": {}, "get_filesystem_usage": {},
                      "get_demo_service_status": {},
                      "sample_performance": {"seconds": (1, 5)},
                      "get_top_processes": {"limit": (1, 10)}}
        if name not in parameters:
            raise ToolError("Unknown diagnostic tool")
        arguments = arguments or {}
        if set(arguments) - parameters[name].keys():
            raise ToolError("Unsupported argument; targets are fixed")
        for key, value in arguments.items():
            lower, upper = parameters[name][key]
            if type(value) is not int or not lower <= value <= upper:
                raise ToolError(f"{key} must be an integer from {lower} to {upper}")
        return await super().call_tool(name, arguments)


class BearerGate:
    def __init__(self, app, token):
        if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError("Provide a random ASCII token of at least 32 characters")
        self.app, self.expected = app, ("Bearer " + token).encode("ascii")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            values = [v for k, v in scope["headers"] if k.lower() == b"authorization"]
            if len(values) != 1 or not hmac.compare_digest(values[0], self.expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"www-authenticate", b"Bearer"),
                                        (b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def build_app(token, public_url):
    url = urlsplit(public_url)
    if (url.scheme != "https" or not url.hostname or url.path != "/mcp"
            or url.username or url.password or url.query or url.fragment):
        raise ValueError("PAF_LAB_PUBLIC_URL must be https://your-host:8443/mcp")
    mcp = FixedToolsMCP(
        "Linux Health Assistant Lab", stateless_http=True, json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[url.netloc], allowed_origins=[f"https://{url.netloc}"],
        ),
    )
    # Serialize expensive snapshots, and reject excess concurrent work instead
    # of accumulating unbounded sampling tasks.
    lock = anyio.Lock()

    async def run(check, *args):
        try:
            with anyio.fail_after(0.1):
                await lock.acquire()
        except TimeoutError:
            return {"host": collectors.socket.gethostname(), "status": "unavailable",
                    "observed_at_utc": collectors.datetime.now(collectors.timezone.utc).isoformat(),
                    "measurement_interval_seconds": 0, "data": {},
                    "errors": [{"check": "collector", "error": "busy; retry sequentially"}]}
        try:
            # Keep the lock until the worker finishes, even on disconnect.
            with anyio.CancelScope(shield=True):
                return await anyio.to_thread.run_sync(check, *args, abandon_on_cancel=False)
        finally:
            lock.release()

    annotation = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

    @mcp.tool(annotations=annotation)
    async def get_host_summary() -> dict[str, object]:
        """Current identity, uptime, CPU count and load averages for this host."""
        return await run(collectors.host_summary)

    @mcp.tool(annotations=annotation)
    async def sample_performance(seconds: Annotated[int, Field(strict=True, ge=1, le=5)] = 2) -> dict[str, object]:
        """Sample CPU, available memory and swap activity for 1–5 seconds; no history."""
        return await run(collectors.performance, seconds)

    @mcp.tool(annotations=annotation)
    async def get_filesystem_usage() -> dict[str, object]:
        """Capacity and inode usage for root and the dedicated lab filesystem only."""
        return await run(collectors.filesystem_usage)

    @mcp.tool(annotations=annotation)
    async def get_top_processes(limit: Annotated[int, Field(strict=True, ge=1, le=10)] = 5) -> dict[str, object]:
        """Top 1–10 processes by sampled CPU over approximately one second; no command lines."""
        return await run(collectors.top_processes, limit)

    @mcp.tool(annotations=annotation)
    async def get_demo_service_status() -> dict[str, object]:
        """Read the fixed paf-lab-demo.service state; cannot change it."""
        return await run(collectors.demo_service_status)

    return BearerGate(mcp.streamable_http_app(), token)


def main():
    token = Path(os.environ["PAF_LAB_TOKEN_FILE"]).read_text().strip()
    app = build_app(token, os.environ["PAF_LAB_PUBLIC_URL"])
    uvicorn.run(app, host="0.0.0.0", port=8443, access_log=False,
                limit_concurrency=16, timeout_keep_alive=5,
                ssl_certfile=os.environ["PAF_LAB_TLS_CERT"],
                ssl_keyfile=os.environ["PAF_LAB_TLS_KEY"],
                ssl_version=ssl.PROTOCOL_TLS_SERVER)


if __name__ == "__main__":
    main()
