"""Read-only, fixed-target Linux evidence. No shell or remediation interface."""
from __future__ import annotations

import os
import platform
import socket
import subprocess
import time
from datetime import datetime, timezone

import psutil

LAB_MOUNT = "/var/lib/paf-linux-lab/disk"
DEMO_SERVICE = "paf-lab-demo.service"


def evidence(collect):
    started = time.monotonic()
    result = {
        "host": socket.gethostname(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ok", "data": {}, "errors": [],
    }
    try:
        collect(result)
    except (OSError, ValueError, psutil.Error, subprocess.SubprocessError) as exc:
        result["errors"].append({"check": "collection", "error": type(exc).__name__})
    result["measurement_interval_seconds"] = round(time.monotonic() - started, 3)
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    if result["errors"]:
        result["status"] = "partial" if result["data"] else "unavailable"
    return result


def host_summary():
    def collect(out):
        out["data"] = {
            "os": platform.system(), "kernel": platform.release(),
            "cpu_count_logical": psutil.cpu_count(),
            "uptime_seconds": round(time.time() - psutil.boot_time()),
            "load_average_1_5_15_minutes": list(os.getloadavg()),
            "scope": "This host only; current evidence, no stored history.",
        }
    return evidence(collect)


def performance(seconds=2):
    if type(seconds) is not int or not 1 <= seconds <= 5:
        raise ValueError("seconds must be an integer from 1 to 5")

    def collect(out):
        before = psutil.swap_memory()
        started = time.monotonic()
        cpu = psutil.cpu_times_percent(interval=seconds)
        elapsed = time.monotonic() - started
        after = psutil.swap_memory()
        memory = psutil.virtual_memory()
        # guest counters are already included in user/nice. Idle and iowait are
        # not executing CPU work; report iowait independently.
        out["data"] = {
            "cpu_busy_percent": round(max(0, 100 - cpu.idle - getattr(cpu, "iowait", 0)), 2),
            "cpu_iowait_percent": getattr(cpu, "iowait", 0),
            "cpu_count_logical": psutil.cpu_count(),
            "load_average_1_5_15_minutes": list(os.getloadavg()),
            "memory_total_bytes": memory.total,
            "memory_available_bytes": memory.available,
            "memory_available_percent": round(100 * memory.available / memory.total, 2),
            "swap_total_bytes": after.total, "swap_used_bytes": after.used,
            "swap_in_bytes_per_second": max(0, after.sin - before.sin) / elapsed,
            "swap_out_bytes_per_second": max(0, after.sout - before.sout) / elapsed,
            "sample_interval_seconds": round(elapsed, 3),
        }
    return evidence(collect)


def filesystem_usage():
    def collect(out):
        rows = []
        for mount in ("/", LAB_MOUNT):
            try:
                # Never silently report the parent filesystem as the lab disk.
                if not os.path.ismount(mount):
                    raise ValueError("expected_mount_missing")
                usage = psutil.disk_usage(mount)
                stat = os.statvfs(mount)
                rows.append({
                    "mount": mount, "total_bytes": usage.total,
                    "used_bytes": usage.used, "available_bytes": usage.free,
                    "used_percent": usage.percent,
                    "inodes_total": stat.f_files, "inodes_available": stat.f_favail,
                    "inodes_used_percent": (
                        round(100 * (stat.f_files - stat.f_ffree) / stat.f_files, 2)
                        if stat.f_files else None),
                })
            except (OSError, ValueError) as exc:
                out["errors"].append({"check": mount, "error": str(exc)})
        if rows:
            out["data"]["filesystems"] = rows
        out["scope"] = "Only root and the dedicated lab mount are checked."
    return evidence(collect)


def top_processes(limit=5):
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError("limit must be an integer from 1 to 10")

    def collect(out):
        processes = []
        skipped = 0
        for scanned, proc in enumerate(psutil.process_iter()):
            if scanned >= 4096:
                out["errors"].append({"check": "processes", "error": "4096 process scan limit reached"})
                break
            try:
                proc.cpu_percent(None)
                processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                skipped += 1
        time.sleep(1)
        rows = []
        for proc in processes:
            try:
                rows.append({"pid": proc.pid, "name": proc.name()[:80],
                             "cpu_percent_one_core": proc.cpu_percent(None),
                             "rss_bytes": proc.memory_info().rss})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                skipped += 1
        out["data"] = {
            "processes": sorted(rows, key=lambda row: row["cpu_percent_one_core"], reverse=True)[:limit],
            "skipped_processes": skipped,
            "cpu_percent_basis": "100 percent is one logical CPU; multithreaded processes can exceed 100",
        }
        if skipped:
            out["errors"].append({"check": "processes", "error": "processes exited or access was denied"})
    return evidence(collect)


def demo_service_status():
    def collect(out):
        result = subprocess.run(
            ["/usr/bin/systemctl", "show", DEMO_SERVICE, "--no-pager",
             "--property=LoadState,ActiveState,SubState,Result"],
            capture_output=True, text=True, timeout=3, check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        if result.returncode:
            out["errors"].append({"check": DEMO_SERVICE, "error": "systemctl failed"})
            return
        values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        if values.get("LoadState") != "loaded":
            out["errors"].append({"check": DEMO_SERVICE, "error": "demo unit not loaded"})
            return
        if not {"ActiveState", "SubState", "Result"} <= values.keys():
            raise ValueError("incomplete service evidence")
        out["data"] = {"service": DEMO_SERVICE, **values}
    return evidence(collect)
