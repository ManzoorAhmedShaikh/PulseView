"""Aggregate CPU, RAM, VRAM, and disk metrics."""

from __future__ import annotations

import psutil

from system_monitor.hardware import disk_usage_for, read_vram
from system_monitor.models import GpuInfo, MetricSnapshot


def collect_metrics(disk_mount: str, gpu: GpuInfo | None) -> MetricSnapshot:
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = disk_usage_for(disk_mount)

    vram_pct = vram_used = vram_total = None
    capacity_only = False

    if gpu is not None:
        stats, _ = read_vram(gpu)
        if stats is not None:
            vram_used = stats.used
            vram_total = stats.total
            vram_pct = (stats.used / stats.total * 100) if stats.total else 0.0
            capacity_only = stats.source.startswith("pci bar")

    return MetricSnapshot(
        cpu_percent=cpu,
        ram_percent=mem.percent,
        ram_used=mem.used,
        ram_total=mem.total,
        vram_percent=vram_pct,
        vram_used=vram_used,
        vram_total=vram_total,
        vram_capacity_only=capacity_only,
        disk_percent=disk.percent,
        disk_used=disk.used,
        disk_total=disk.total,
    )
