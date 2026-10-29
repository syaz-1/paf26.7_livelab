"""Live, read-only protocol smoke check. Uses TLS verification and private token file."""
import argparse
import asyncio
import json
import ssl
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

TOOLS = {"get_host_summary", "sample_performance", "get_filesystem_usage",
         "get_top_processes", "get_demo_service_status"}


async def check(args):
    token = Path(args.token_file).read_text().strip()
    context = ssl.create_default_context(cafile=args.ca_file)
    headers = {"Authorization": "Bearer " + token}
    # Verify rejection before doing authenticated protocol negotiation.
    async with httpx.AsyncClient(verify=context, timeout=10) as client:
        for auth in ({}, {"Authorization": "Bearer invalid"}):
            response = await client.post(args.url, headers=auth, json={})
            if response.status_code != 401:
                raise RuntimeError("Missing/invalid bearer credentials were not rejected")

    def factory(headers=None, timeout=None, auth=None):
        return httpx.AsyncClient(headers=headers, timeout=timeout, auth=auth, verify=context)

    async with streamablehttp_client(args.url, headers=headers, httpx_client_factory=factory) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {tool.name for tool in (await session.list_tools()).tools}
            if names != TOOLS:
                raise RuntimeError("Unexpected tool inventory")
            for name in sorted(TOOLS):
                result = await session.call_tool(name, {})
                data = result.structuredContent
                if data is None:
                    data = json.loads(result.content[0].text)
                if result.isError or data.get("status") != "ok":
                    raise RuntimeError(f"{name}: incomplete evidence; inspect locally")
                if not all(key in data for key in ("host", "observed_at_utc", "measurement_interval_seconds", "errors")):
                    raise RuntimeError(f"{name}: missing evidence envelope")
                print(f"PASS {name}")
            for name, arguments in (("sample_performance", {"seconds": 0}),
                                    ("sample_performance", {"seconds": 6}),
                                    ("get_top_processes", {"limit": 11})):
                if not (await session.call_tool(name, arguments)).isError:
                    raise RuntimeError("Out-of-range input accepted")
    print("PASS auth, discovery, initialization, five tool calls and bounds; review PAF traces separately")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--ca-file")
    args = parser.parse_args()
    if not args.url.startswith("https://"):
        parser.error("HTTPS required")
    asyncio.run(check(args))
