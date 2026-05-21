"""AMD GPU discovery and VRAM (amdgpu sysfs, radeontop, PCI BAR)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

from system_monitor.models import GpuInfo, VramStats
from system_monitor.settings import DRM_ROOT, VENDOR_AMD
from system_monitor.utils.sysfs import gpu_name_from_lspci, pci_bar_vram_total, read_int


def discover_amd_gpu() -> GpuInfo | None:
    if not DRM_ROOT.is_dir():
        return None
    for card_dir in sorted(DRM_ROOT.glob("card[0-9]")):
        device = card_dir / "device"
        vendor_path = device / "vendor"
        if not vendor_path.is_file():
            continue
        if vendor_path.read_text().strip() != VENDOR_AMD:
            continue
        driver = "unknown"
        driver_link = device / "driver"
        if driver_link.is_symlink():
            driver = os.path.basename(os.path.realpath(driver_link))

        pci_slot = os.path.basename(os.path.realpath(device))
        name = gpu_name_from_lspci(pci_slot) or f"AMD GPU ({pci_slot})"
        return GpuInfo(card=card_dir.name, name=name, vendor="amd", driver=driver)
    return None


def _vram_from_amdgpu_sysfs(device: Path) -> VramStats | None:
    total = read_int(device / "mem_info_vram_total")
    used = read_int(device / "mem_info_vram_used")
    if total is None or used is None or total <= 0:
        return None
    return VramStats(used=used, total=total, source="amdgpu sysfs")


def _vram_from_radeontop(card_index: int) -> VramStats | None:
    if shutil.which("radeontop") is None:
        return None
    bus = f"drm/{card_index}"
    try:
        out = subprocess.check_output(
            ["radeontop", "-d", "-", "-l", "1", "-b", bus],
            text=True,
            timeout=4,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.SubprocessError, OSError):
        try:
            out = subprocess.check_output(
                ["radeontop", "-d", "-", "-l", "1"],
                text=True,
                timeout=4,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.SubprocessError, OSError):
            return None

    match = re.search(r"vram\s+([\d.]+)%\s+([\d.]+)\s*mb", out, re.I)
    if not match:
        return None
    used_mb = float(match.group(2))
    used = int(used_mb * 1024 * 1024)
    pct = float(match.group(1))
    total = int(used / (pct / 100.0)) if pct > 0 else used
    return VramStats(used=used, total=total, source="radeontop")


def read_amd_vram(gpu: GpuInfo) -> tuple[VramStats | None, str]:
    device = DRM_ROOT / gpu.card / "device"
    card_index = int(gpu.card.replace("card", ""))

    stats = _vram_from_amdgpu_sysfs(device)
    if stats is not None:
        return stats, ""

    stats = _vram_from_radeontop(card_index)
    if stats is not None:
        return stats, ""

    total = pci_bar_vram_total(device)
    if total is not None:
        return (
            VramStats(used=0, total=total, source="pci bar (capacity only)"),
            "Install radeontop for live VRAM usage: sudo apt install radeontop",
        )

    return None, "Could not read AMD VRAM (try: sudo apt install radeontop)"
