"""GPU selection and unified VRAM access."""

from __future__ import annotations

from system_monitor.hardware import amd, nvidia
from system_monitor.models import GpuInfo, VramStats


def pick_gpu() -> GpuInfo | None:
    """Prefer AMD discrete GPU when present, else NVIDIA."""
    discovered = amd.discover_amd_gpu()
    if discovered is not None:
        return discovered
    return nvidia.init_nvidia()


def read_vram(gpu: GpuInfo) -> tuple[VramStats | None, str]:
    if gpu.vendor == "amd":
        return amd.read_amd_vram(gpu)
    if gpu.vendor == "nvidia":
        stats = nvidia.read_nvidia_vram()
        return stats, "" if stats else "NVIDIA VRAM read failed"
    return None, "Unsupported GPU"


def shutdown_gpu() -> None:
    nvidia.shutdown_nvidia()
