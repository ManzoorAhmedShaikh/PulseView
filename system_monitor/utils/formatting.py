"""Display formatting helpers."""

from __future__ import annotations

from system_monitor.models import DiskTarget
from system_monitor.settings import (
    BAR_CRITICAL_PERCENT,
    BAR_WARN_PERCENT,
    COLOR_BAR_CRITICAL,
    COLOR_BAR_OK,
    COLOR_BAR_WARN,
)


def format_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} PB"


def bar_color_for_percent(percent: float) -> str:
    if percent >= BAR_CRITICAL_PERCENT:
        return COLOR_BAR_CRITICAL
    if percent >= BAR_WARN_PERCENT:
        return COLOR_BAR_WARN
    return COLOR_BAR_OK


def short_gpu_name(name: str) -> str:
    if "Radeon" in name or "AMD" in name:
        for token in ("Radeon", "R5 ", "R7 ", "RX "):
            idx = name.find(token)
            if idx >= 0:
                snippet = name[idx : idx + 40]
                return snippet.split("[")[0].strip()
    if len(name) > 48:
        return name[:45] + "…"
    return name


def disk_option_label(target: DiskTarget) -> str:
    dev = target.device
    if dev.startswith("/dev/"):
        dev = dev.replace("/dev/", "")
    return f"{target.label}  [{dev}, {target.fstype}]"
