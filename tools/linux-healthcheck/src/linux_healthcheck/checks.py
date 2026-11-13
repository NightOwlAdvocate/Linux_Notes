"""Individual, read-only Linux health checks."""

import re
import subprocess
from typing import Dict, Iterable, List, Sequence

from linux_healthcheck.host import Host
from linux_healthcheck.models import CheckResult


DEFAULT_CHECKS = (
    "system",
    "uptime",
    "memory",
    "disk",
    "services",
    "packages",
    "dkms",
    "reboot",
)


def _key_values(text: str, separator: str = "=") -> Dict[str, str]:
    values = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or separator not in line:
            continue
        key, value = line.split(separator, 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _read(host: Host, path: str) -> str:
    try:
        return host.read_text(path)
    except (OSError, UnicodeError):
        return ""


def check_system(host: Host) -> CheckResult:
    release = _key_values(_read(host, "/etc/os-release"))
    uname = host.uname()
    os_name = release.get("PRETTY_NAME", release.get("NAME", "Unknown Linux"))
    return CheckResult(
        "system",
        "System",
        "ok",
        f"{os_name}; kernel {uname.release}; {uname.machine}",
        metrics={
            "os": os_name,
            "kernel": uname.release,
            "architecture": uname.machine,
        },
    )


def check_uptime(host: Host) -> CheckResult:
    uptime_text = _read(host, "/proc/uptime")
    try:
        uptime_seconds = int(float(uptime_text.split()[0]))
        one, five, fifteen = host.load_average()
    except (IndexError, ValueError, OSError):
        return CheckResult("uptime", "Uptime and load", "skip", "Metrics are unavailable")

    cpus = max(host.cpu_count(), 1)
    load_per_cpu = one / cpus
    status = "ok"
    if load_per_cpu >= 2.0:
        status = "critical"
    elif load_per_cpu >= 1.0:
        status = "warning"

    days, remainder = divmod(uptime_seconds, 86400)
    hours = remainder // 3600
    return CheckResult(
        "uptime",
        "Uptime and load",
        status,
        f"Uptime {days}d {hours}h; load {one:.2f}, {five:.2f}, {fifteen:.2f}",
        metrics={
            "uptime_seconds": uptime_seconds,
            "load_1m": round(one, 2),
            "load_5m": round(five, 2),
            "load_15m": round(fifteen, 2),
            "cpu_count": cpus,
        },
    )


def check_memory(host: Host) -> CheckResult:
    raw = _read(host, "/proc/meminfo")
    values = {}
    for line in raw.splitlines():
        match = re.match(r"^(\w+):\s+(\d+)", line)
        if match:
            values[match.group(1)] = int(match.group(2))

    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    if total <= 0:
        return CheckResult("memory", "Memory", "skip", "Memory metrics are unavailable")

    available_percent = available * 100 / total
    status = "ok"
    if available_percent <= 5:
        status = "critical"
    elif available_percent <= 15:
        status = "warning"

    return CheckResult(
        "memory",
        "Memory",
        status,
        f"{available_percent:.1f}% available",
        metrics={
            "total_kib": total,
            "available_kib": available,
            "available_percent": round(available_percent, 1),
        },
    )


def _disk_result(host: Host, path: str) -> CheckResult:
    try:
        usage = host.disk_usage(path)
    except OSError as error:
        return CheckResult("disk", "Disk space", "skip", f"Cannot read {path}: {error}")

    used_percent = usage.used * 100 / usage.total if usage.total else 0
    status = "ok"
    if used_percent >= 97:
        status = "critical"
    elif used_percent >= 90:
        status = "warning"

    free_gib = usage.free / (1024 ** 3)
    return CheckResult(
        "disk",
        "Disk space",
        status,
        f"{path}: {used_percent:.1f}% used, {free_gib:.1f} GiB free",
        metrics={
            "path": path,
            "used_percent": round(used_percent, 1),
            "free_bytes": usage.free,
            "total_bytes": usage.total,
        },
    )


def check_disk(host: Host) -> CheckResult:
    return _disk_result(host, "/")


def _command_check(
    host: Host,
    check_id: str,
    title: str,
    command_name: str,
    command: Sequence[str],
    empty_summary: str,
) -> CheckResult:
    executable = host.which(command_name)
    if not executable:
        return CheckResult(check_id, title, "skip", f"{command_name} is not installed")

    try:
        completed = host.run([executable, *command[1:]])
    except (OSError, subprocess.SubprocessError) as error:
        return CheckResult(check_id, title, "skip", f"Cannot run {command_name}: {error}")

    output = completed.stdout.strip()
    if completed.returncode != 0:
        reason = completed.stderr.strip() or f"exit code {completed.returncode}"
        return CheckResult(check_id, title, "skip", f"Check unavailable: {reason}")
    if not output:
        return CheckResult(check_id, title, "ok", empty_summary)

    lines = output.splitlines()
    return CheckResult(
        check_id,
        title,
        "warning",
        f"Found {len(lines)} item(s) requiring review",
        details=lines[:20],
        metrics={"item_count": len(lines)},
    )


def check_services(host: Host) -> CheckResult:
    return _command_check(
        host,
        "services",
        "Failed services",
        "systemctl",
        ["systemctl", "--failed", "--no-legend", "--plain"],
        "No failed systemd units",
    )


def check_packages(host: Host) -> CheckResult:
    return _command_check(
        host,
        "packages",
        "Package state",
        "dpkg",
        ["dpkg", "--audit"],
        "dpkg reports no incomplete package operations",
    )


def check_dkms(host: Host) -> CheckResult:
    result = _command_check(
        host,
        "dkms",
        "DKMS modules",
        "dkms",
        ["dkms", "status"],
        "No DKMS modules are registered",
    )
    if result.status != "warning":
        return result

    questionable = [
        line for line in result.details if not re.search(r":\s+installed(?:\s|$)", line)
    ]
    if not questionable:
        return CheckResult(
            "dkms",
            "DKMS modules",
            "ok",
            f"{len(result.details)} registered module(s) are installed",
            details=result.details,
            metrics={"module_count": len(result.details)},
        )
    result.summary = f"{len(questionable)} DKMS entry/entries are not marked installed"
    result.details = questionable
    result.metrics = {"review_count": len(questionable)}
    return result


def check_reboot(host: Host) -> CheckResult:
    path = "/var/run/reboot-required"
    if not host.exists(path):
        return CheckResult("reboot", "Reboot", "ok", "No reboot marker found")
    reason = _read(host, path).strip() or "System restart required"
    return CheckResult("reboot", "Reboot", "warning", reason)


CHECK_FUNCTIONS = {
    "system": check_system,
    "uptime": check_uptime,
    "memory": check_memory,
    "disk": check_disk,
    "services": check_services,
    "packages": check_packages,
    "dkms": check_dkms,
    "reboot": check_reboot,
}


def collect_checks(host: Host, selected: Iterable[str]) -> List[CheckResult]:
    return [CHECK_FUNCTIONS[name](host) for name in selected]
