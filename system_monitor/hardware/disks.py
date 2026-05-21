"""Mounted disk discovery and usage."""

from __future__ import annotations

import platform
from pathlib import Path

import psutil

from system_monitor.models import DiskTarget
from system_monitor.settings import SKIP_FSTYPES


def _device_for_mount(mountpoint: str) -> str:
    if platform.system() != "Linux":
        return ""
    mounts_path = Path("/proc/mounts")
    if not mounts_path.is_file():
        return ""
    try:
        for line in mounts_path.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == mountpoint:
                return parts[0]
    except OSError:
        pass
    return ""


def list_disk_targets() -> list[DiskTarget]:
    seen: set[str] = set()
    targets: list[DiskTarget] = []

    for part in psutil.disk_partitions(all=False):
        mp = part.mountpoint
        if mp in seen or part.fstype in SKIP_FSTYPES:
            continue
        seen.add(mp)
        device = _device_for_mount(mp) or part.device
        if mp in ("/", "/home"):
            role = "OS root" if mp == "/" else "Home"
            label = f"{mp} ({role})"
        else:
            label = mp
        targets.append(
            DiskTarget(
                mountpoint=mp,
                label=label,
                device=device,
                fstype=part.fstype,
            )
        )

    targets.sort(key=lambda t: (0 if t.mountpoint == "/" else 1, t.mountpoint))
    return targets


def disk_usage_for(mountpoint: str) -> psutil._common.sdiskusage:
    return psutil.disk_usage(mountpoint)
