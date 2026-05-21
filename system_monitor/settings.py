"""Application constants and UI configuration."""

from __future__ import annotations

from pathlib import Path

# Window
APP_TITLE = "System Monitor"
WINDOW_WIDTH = 740
WINDOW_HEIGHT = 660
WINDOW_MIN_WIDTH = 660
WINDOW_MIN_HEIGHT = 580

# Polling
REFRESH_MS = 1000

# CustomTkinter
CTK_COLOR_THEME = "blue"
CTK_APPEARANCE_MODE = "system"
THEME_OPTIONS = ("System", "Dark", "Light")
THEME_TO_MODE = {"System": "system", "Dark": "dark", "Light": "light"}

# UI chrome
CARD_CORNER_RADIUS = 16
CARD_PADDING_X = 20

# Metric card accent colors
COLOR_CPU = "#3498DB"
COLOR_RAM = "#9B59B6"
COLOR_VRAM = "#E67E22"
COLOR_DISK = "#1ABC9C"

# Progress bar thresholds
COLOR_BAR_OK = "#2ECC71"
COLOR_BAR_WARN = "#F39C12"
COLOR_BAR_CRITICAL = "#E74C3C"
BAR_WARN_PERCENT = 75
BAR_CRITICAL_PERCENT = 90

# Linux DRM / PCI (hardware probing)
DRM_ROOT = Path("/sys/class/drm")
VENDOR_AMD = "0x1002"
VENDOR_NVIDIA = "0x10de"
PCI_PREFETCHABLE_FLAG = 0x2000

# Disk discovery
SKIP_FSTYPES = frozenset(
    {
        "squashfs",
        "tmpfs",
        "devtmpfs",
        "devfs",
        "overlay",
        "autofs",
        "proc",
        "sysfs",
        "cgroup",
        "cgroup2",
        "pstore",
        "bpf",
        "tracefs",
        "debugfs",
        "securityfs",
        "hugetlbfs",
        "mqueue",
        "fusectl",
        "configfs",
    }
)
