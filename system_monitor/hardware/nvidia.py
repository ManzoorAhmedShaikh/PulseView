"""NVIDIA GPU VRAM via NVML."""

from __future__ import annotations

from system_monitor.models import GpuInfo, VramStats

_nvml = None


def init_nvidia() -> GpuInfo | None:
    global _nvml
    try:
        import pynvml

        pynvml.nvmlInit()
        _nvml = pynvml
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        raw = pynvml.nvmlDeviceGetName(handle)
        name = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        return GpuInfo(card="nvidia0", name=name, vendor="nvidia", driver="nvidia")
    except Exception:
        _nvml = None
        return None


def read_nvidia_vram() -> VramStats | None:
    if _nvml is None:
        return None
    try:
        handle = _nvml.nvmlDeviceGetHandleByIndex(0)
        info = _nvml.nvmlDeviceGetMemoryInfo(handle)
        return VramStats(used=info.used, total=info.total, source="nvidia-ml")
    except Exception:
        return None


def shutdown_nvidia() -> None:
    global _nvml
    if _nvml is not None:
        try:
            _nvml.nvmlShutdown()
        except Exception:
            pass
        _nvml = None
