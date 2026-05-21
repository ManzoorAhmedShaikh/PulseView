"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInfo:
    card: str
    name: str
    vendor: str  # "amd" | "nvidia"
    driver: str


@dataclass
class VramStats:
    used: int
    total: int
    source: str


@dataclass(frozen=True)
class DiskTarget:
    mountpoint: str
    label: str
    device: str
    fstype: str


@dataclass
class MetricSnapshot:
    cpu_percent: float
    ram_percent: float
    ram_used: int
    ram_total: int
    vram_percent: float | None
    vram_used: int | None
    vram_total: int | None
    vram_capacity_only: bool
    disk_percent: float
    disk_used: int
    disk_total: int
