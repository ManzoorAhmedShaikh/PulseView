"""Linux sysfs and PCI helpers."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from system_monitor.settings import PCI_PREFETCHABLE_FLAG


def read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def pci_bar_vram_total(device: Path) -> int | None:
    """Largest prefetchable PCI BAR — often maps dedicated VRAM on discrete GPUs."""
    resource = device / "resource"
    if not resource.is_file():
        return None
    best = 0
    try:
        for line in resource.read_text().splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            start, end, flags = int(parts[0], 16), int(parts[1], 16), int(parts[2], 16)
            if start == 0 and end == 0:
                continue
            size = end - start + 1
            if flags & PCI_PREFETCHABLE_FLAG and size > best:
                best = size
    except OSError:
        return None
    return best or None


def pci_slot_for_lspci(pci_slot: str) -> str:
    """Sysfs uses 0000:0d:00.0; lspci expects 0d:00.0 on most systems."""
    if re.match(r"^\d{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9]$", pci_slot, re.I):
        return pci_slot[5:]
    return pci_slot


def gpu_name_from_lspci(pci_slot: str) -> str | None:
    if shutil.which("lspci") is None:
        return None
    try:
        out = subprocess.check_output(
            ["lspci", "-s", pci_slot_for_lspci(pci_slot)],
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        ).strip()
        for sep in (
            " Display controller: ",
            " VGA compatible controller: ",
            " 3D controller: ",
        ):
            if sep in out:
                return out.split(sep, 1)[1].strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return None
