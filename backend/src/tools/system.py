"""System resource monitoring tools."""
from pathlib import Path

import psutil


CPU_WARNING = 80.0
CPU_CRITICAL = 90.0
RAM_WARNING = 80.0
RAM_CRITICAL = 90.0
STORAGE_WARNING = 85.0
STORAGE_CRITICAL = 90.0
CRITICAL_MARKER = "[[ULTRON_SYSTEM_HEALTH_RED]]"


def check_system_health() -> str:
    """Report CPU, RAM, and system-drive usage with safety severity markers."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.cwd().anchor or "/")
    except (OSError, RuntimeError) as exc:
        return f"Error checking system resources: {exc}"

    metrics = [
        ("CPU", cpu, CPU_WARNING, CPU_CRITICAL),
        ("RAM", memory.percent, RAM_WARNING, RAM_CRITICAL),
        ("Storage", disk.percent, STORAGE_WARNING, STORAGE_CRITICAL),
    ]
    critical = [name for name, value, _, limit in metrics if value >= limit]
    warning = [
        name for name, value, warning_limit, critical_limit in metrics
        if warning_limit <= value < critical_limit
    ]

    lines = [
        "system | usage | status",
        "--- | --- | ---",
        *(_format_metric(name, value, warning_limit, critical_limit)
          for name, value, warning_limit, critical_limit in metrics),
    ]
    if critical:
        lines.append(
            f"{CRITICAL_MARKER} CRITICAL: {', '.join(critical)} near a dangerous limit."
        )
    elif warning:
        lines.append(f"WARNING: {', '.join(warning)} usage is elevated.")
    else:
        lines.append("Status: system resources are within normal limits.")
    return "\n".join(lines)


def _format_metric(name: str, value: float, warning: float, critical: float) -> str:
    if value >= critical:
        status = "CRITICAL"
    elif value >= warning:
        status = "WARNING"
    else:
        status = "OK"
    return f"{name} | {value:.1f}% | {status}"
