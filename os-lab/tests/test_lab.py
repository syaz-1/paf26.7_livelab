import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collectors
from server import BearerGate, build_app
import httpx


class CollectorTests(unittest.TestCase):
    def test_sampling_rejects_unbounded_and_coerced_values(self):
        for value in (0, 6, -1, 1.5, "2", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                collectors.performance(value)
        for value in (0, 11, -1, "5", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                collectors.top_processes(value)

    def test_low_free_memory_does_not_replace_available(self):
        swap = SimpleNamespace(total=1000, used=500, sin=200, sout=300)
        memory = SimpleNamespace(total=10000, available=8000, free=100)
        cpu = SimpleNamespace(idle=70, iowait=10)
        with patch.object(collectors.psutil, "swap_memory", return_value=swap), \
             patch.object(collectors.psutil, "virtual_memory", return_value=memory), \
             patch.object(collectors.psutil, "cpu_times_percent", return_value=cpu):
            result = collectors.performance(1)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["memory_available_percent"], 80)
        self.assertEqual(result["data"]["swap_in_bytes_per_second"], 0)
        self.assertEqual(result["data"]["swap_out_bytes_per_second"], 0)
        self.assertEqual(result["data"]["cpu_busy_percent"], 20)

    def test_missing_mount_is_not_parent_filesystem(self):
        usage = SimpleNamespace(total=100, used=10, free=90, percent=10)
        stat = SimpleNamespace(f_files=100, f_favail=95, f_ffree=95)
        with patch.object(collectors.os.path, "ismount", side_effect=lambda path: path == "/"), \
             patch.object(collectors.psutil, "disk_usage", return_value=usage) as disk, \
             patch.object(collectors.os, "statvfs", return_value=stat):
            result = collectors.filesystem_usage()
        disk.assert_called_once_with("/")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["errors"][0]["check"], collectors.LAB_MOUNT)

    def test_total_storage_failure_is_unavailable(self):
        with patch.object(collectors.os.path, "ismount", return_value=False):
            result = collectors.filesystem_usage()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(result["errors"]), 2)

    def test_inode_accounting_and_unsupported_inode_total(self):
        usage = SimpleNamespace(total=100, used=90, free=10, percent=90)
        stat = SimpleNamespace(f_files=100, f_favail=2, f_ffree=2)
        with patch.object(collectors.os.path, "ismount", return_value=True), \
             patch.object(collectors.psutil, "disk_usage", return_value=usage), \
             patch.object(collectors.os, "statvfs", return_value=stat):
            result = collectors.filesystem_usage()
            self.assertEqual(result["data"]["filesystems"][0]["inodes_used_percent"], 98)
            stat.f_files = 0
            self.assertIsNone(collectors.filesystem_usage()["data"]["filesystems"][0]["inodes_used_percent"])

    def test_service_fixed_argv_and_inactive_is_valid_evidence(self):
        completed = subprocess.CompletedProcess([], 0, "LoadState=loaded\nActiveState=inactive\nSubState=dead\nResult=success\n")
        with patch.object(collectors.subprocess, "run", return_value=completed) as run:
            result = collectors.demo_service_status()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["ActiveState"], "inactive")
        self.assertEqual(run.call_args.args[0][2], collectors.DEMO_SERVICE)
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertEqual(run.call_args.kwargs["timeout"], 3)

    def test_service_failure_never_claims_state(self):
        for outcome in (PermissionError(), subprocess.TimeoutExpired("systemctl", 3)):
            with patch.object(collectors.subprocess, "run", side_effect=outcome):
                result = collectors.demo_service_status()
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(result["data"], {})
        for code, output in ((1, ""), (0, "LoadState=not-found\n"), (0, "LoadState=loaded\n")):
            with patch.object(collectors.subprocess, "run", return_value=subprocess.CompletedProcess([], code, output)):
                self.assertEqual(collectors.demo_service_status()["status"], "unavailable")

    def test_process_ranking_bounds_and_no_arguments(self):
        def process(pid, percent):
            return SimpleNamespace(pid=pid, cpu_percent=lambda _: percent,
                                   name=lambda: f"process-{pid}",
                                   memory_info=lambda: SimpleNamespace(rss=100))
        with patch.object(collectors.psutil, "process_iter", return_value=[process(1, 10), process(2, 99)]), \
             patch.object(collectors.time, "sleep"):
            result = collectors.top_processes(1)
        self.assertEqual(result["data"]["processes"], [
            {"pid": 2, "name": "process-2", "cpu_percent_one_core": 99, "rss_bytes": 100}])

    def test_host_envelope(self):
        result = collectors.host_summary()
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["observed_at_utc"].endswith("+00:00"))
        self.assertGreaterEqual(result["measurement_interval_seconds"], 0)


def protocol_test(method):
    async def wrapped(self):
        app = build_app("x" * 48, "https://lab.example:8443/mcp")
        # AnyIO lifespan task groups must enter and exit in the same task.
        async with app.app.router.lifespan_context(app.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="https://lab.example:8443",
                                         headers={"Authorization": "Bearer " + "x" * 48,
                                                  "Accept": "application/json, text/event-stream"}) as client:
                self.client = client
                await method(self)
    return wrapped


class MCPTests(unittest.IsolatedAsyncioTestCase):

    async def rpc(self, method, params=None):
        response = await self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                                        "method": method, "params": params or {}})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["result"]

    @protocol_test
    async def test_auth_applies_to_every_http_method(self):
        for method in ("GET", "POST", "DELETE", "OPTIONS"):
            for value in ("", "Bearer invalid", "Bearer " + "x" * 47):
                response = await self.client.request(method, "/mcp", headers={"Authorization": value})
                self.assertEqual(response.status_code, 401)
                self.assertNotIn("x" * 48, response.text)

    @protocol_test
    async def test_duplicate_authorization_rejected(self):
        response = await self.client.post("/mcp", headers=[("Authorization", "Bearer " + "x" * 48),
                                                          ("Authorization", "Bearer " + "x" * 48)])
        self.assertEqual(response.status_code, 401)

    @protocol_test
    async def test_real_protocol_discovery_and_all_tools(self):
        initialized = await self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                                    "clientInfo": {"name": "lab-tests", "version": "1"}})
        self.assertIn("protocolVersion", initialized)
        notification = await self.client.post("/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.assertEqual(notification.status_code, 202)
        tools = (await self.rpc("tools/list"))["tools"]
        names = {tool["name"] for tool in tools}
        self.assertEqual(names, {"get_host_summary", "sample_performance", "get_filesystem_usage",
                                "get_top_processes", "get_demo_service_status"})
        for tool in tools:
            self.assertTrue(tool["annotations"]["readOnlyHint"])
        # The collectors' semantics are checked above; exercise each MCP binding.
        for name, collector in (("get_host_summary", "host_summary"), ("sample_performance", "performance"),
                                ("get_filesystem_usage", "filesystem_usage"),
                                ("get_top_processes", "top_processes"),
                                ("get_demo_service_status", "demo_service_status")):
            evidence = collectors.evidence(lambda out: out["data"].update({"test": True}))
            with patch.object(collectors, collector, return_value=evidence) as check:
                result = await self.rpc("tools/call", {"name": name, "arguments": {}})
            check.assert_called_once()
            self.assertFalse(result.get("isError", False))
            self.assertEqual(result["structuredContent"], evidence)

    @protocol_test
    async def test_tool_validation_cannot_execute_unbounded_work(self):
        for name, arguments in (("sample_performance", {"seconds": 6}),
                                ("sample_performance", {"seconds": True}),
                                ("sample_performance", {"seconds": "2"}),
                                ("get_top_processes", {"limit": 11}),
                                ("get_demo_service_status", {"service": "sshd"}),
                                ("execute_shell", {"command": "id"})):
            result = await self.rpc("tools/call", {"name": name, "arguments": arguments})
            self.assertTrue(result.get("isError"), result)

    @protocol_test
    async def test_untrusted_host_and_origin_rejected(self):
        for headers in ({"Host": "evil.example"}, {"Origin": "https://evil.example"}):
            response = await self.client.post("/mcp", headers=headers, json={})
            self.assertIn(response.status_code, (403, 421))

    @protocol_test
    async def test_busy_collector_is_unavailable(self):
        import time
        original = collectors.host_summary
        with patch.object(collectors, "host_summary", side_effect=lambda: (time.sleep(0.4), original())[1]):
            first = asyncio.create_task(self.rpc("tools/call", {"name": "get_host_summary"}))
            await asyncio.sleep(0.05)
            second = await self.rpc("tools/call", {"name": "get_host_summary"})
            self.assertEqual(second["structuredContent"]["status"], "unavailable")
            await first


class ConfigTests(unittest.TestCase):
    def test_no_weak_secret_or_invalid_public_url(self):
        for token in ("", "short", "x" * 32 + "\n", "é" * 48):
            with self.assertRaises(ValueError):
                BearerGate(None, token)
        for url in ("http://lab/mcp", "https://lab/", "https://u:p@lab/mcp", "https://lab/mcp?secret=x"):
            with self.assertRaises(ValueError):
                build_app("x" * 48, url)


if __name__ == "__main__":
    unittest.main()
