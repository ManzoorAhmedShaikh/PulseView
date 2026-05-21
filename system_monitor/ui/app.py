"""Main application window."""

from __future__ import annotations

import platform
import threading
import time

import customtkinter as ctk
import psutil

from system_monitor.hardware import list_disk_targets, pick_gpu, read_vram, shutdown_gpu
from system_monitor.metrics import collect_metrics
from system_monitor.models import DiskTarget, GpuInfo, MetricSnapshot
from system_monitor.settings import (
    APP_TITLE,
    COLOR_CPU,
    COLOR_DISK,
    COLOR_RAM,
    COLOR_VRAM,
    CTK_APPEARANCE_MODE,
    CTK_COLOR_THEME,
    REFRESH_MS,
    THEME_OPTIONS,
    THEME_TO_MODE,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)
from system_monitor.ui.metric_card import MetricCard
from system_monitor.utils.formatting import (
    disk_option_label,
    format_bytes,
    short_gpu_name,
)


class SystemMonitorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        ctk.set_default_color_theme(CTK_COLOR_THEME)
        ctk.set_appearance_mode(CTK_APPEARANCE_MODE)

        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._gpu: GpuInfo | None = pick_gpu()
        self._vram_hint = ""
        if self._gpu is not None:
            _, self._vram_hint = read_vram(self._gpu)

        self._poll_id: str | None = None
        self._collecting = False
        self._disk_targets = list_disk_targets()
        self._disk_by_label: dict[str, DiskTarget] = {
            disk_option_label(t): t for t in self._disk_targets
        }
        default_disk = disk_option_label(
            next((t for t in self._disk_targets if t.mountpoint == "/"), self._disk_targets[0])
        )

        self._build_ui(default_disk)
        psutil.cpu_percent(interval=None)
        self._schedule_poll()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _selected_disk_mount(self) -> str:
        label = self.disk_var.get()
        target = self._disk_by_label.get(label)
        return target.mountpoint if target else "/"

    def _build_ui(self, default_disk_label: str) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 8))
        header.grid_columnconfigure(0, weight=1)

        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_block,
            text=APP_TITLE,
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w")

        host = f"{platform.node()} · {platform.system()} {platform.release()}"
        ctk.CTkLabel(
            title_block,
            text=host,
            font=ctk.CTkFont(size=12),
            text_color=("gray45", "gray60"),
        ).pack(anchor="w", pady=(2, 0))

        theme_frame = ctk.CTkFrame(header, fg_color="transparent")
        theme_frame.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(
            theme_frame,
            text="Theme",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray55"),
        ).pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value="System")
        ctk.CTkSegmentedButton(
            theme_frame,
            values=list(THEME_OPTIONS),
            variable=self.theme_var,
            command=self._on_theme_change,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 4))
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            controls,
            text="Disk to monitor",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray35", "gray60"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.disk_var = ctk.StringVar(value=default_disk_label)
        ctk.CTkOptionMenu(
            controls,
            variable=self.disk_var,
            values=list(self._disk_by_label.keys()),
            width=420,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=1, sticky="ew")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, sticky="nsew", padx=28, pady=(8, 12))
        body.grid_columnconfigure((0, 1), weight=1, uniform="cols")
        body.grid_rowconfigure((0, 1), weight=1, uniform="rows")

        self.cpu_card = MetricCard(body, "CPU", "⚡", COLOR_CPU)
        self.cpu_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.ram_card = MetricCard(body, "Memory", "🧠", COLOR_RAM)
        self.ram_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        gpu_sub = short_gpu_name(self._gpu.name) if self._gpu else "No GPU detected"
        if self._gpu and self._gpu.driver == "radeon":
            gpu_sub += " · legacy radeon driver"
        self.vram_card = MetricCard(body, "VRAM", "🎮", COLOR_VRAM)
        self.vram_card.subtitle.configure(text=gpu_sub)
        self.vram_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))

        self.disk_card = MetricCard(body, "Disk", "💾", COLOR_DISK)
        self.disk_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 20))

        self.status_label = ctk.CTkLabel(
            footer,
            text="Live · updating every second",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        )
        self.status_label.pack(side="left")

        self.clock_label = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray55"),
        )
        self.clock_label.pack(side="right")

    def _on_theme_change(self, choice: str) -> None:
        ctk.set_appearance_mode(THEME_TO_MODE.get(choice, "system"))

    def _schedule_poll(self) -> None:
        self._poll_id = self.after(REFRESH_MS, self._poll)

    def _poll(self) -> None:
        if not self._collecting:
            self._collecting = True
            mount = self._selected_disk_mount()
            threading.Thread(
                target=self._fetch_and_apply,
                args=(mount,),
                daemon=True,
            ).start()
        self._poll_id = self.after(REFRESH_MS, self._poll)

    def _fetch_and_apply(self, mount: str) -> None:
        try:
            snap = collect_metrics(mount, self._gpu)
            self.after(0, lambda: self._apply_snapshot(snap, mount))
        finally:
            self._collecting = False

    def _apply_snapshot(self, snapshot: MetricSnapshot, mount: str) -> None:
        cores = psutil.cpu_count(logical=True) or "?"
        self.cpu_card.update(snapshot.cpu_percent, f"{cores} logical cores")

        self.ram_card.update(
            snapshot.ram_percent,
            f"{format_bytes(snapshot.ram_used)} / {format_bytes(snapshot.ram_total)}",
        )

        self._update_vram_card(snapshot)
        self._update_disk_card(snapshot, mount)

        now = time.strftime("%H:%M:%S")
        self.clock_label.configure(text=now)
        self.status_label.configure(text=f"Live · last refresh {now}")

    def _update_vram_card(self, snapshot: MetricSnapshot) -> None:
        gpu_name = short_gpu_name(self._gpu.name) if self._gpu else "GPU"

        if snapshot.vram_capacity_only and snapshot.vram_total is not None:
            self.vram_card.show_capacity_only(
                total_label=format_bytes(snapshot.vram_total),
                detail="Live % needs radeontop · sudo apt install radeontop",
                subtitle=gpu_name,
                accent=COLOR_VRAM,
            )
        elif (
            snapshot.vram_percent is not None
            and snapshot.vram_used is not None
            and snapshot.vram_total is not None
        ):
            self.vram_card.update(
                snapshot.vram_percent,
                f"{format_bytes(snapshot.vram_used)} / {format_bytes(snapshot.vram_total)}",
                subtitle=gpu_name,
            )
        else:
            hint = self._vram_hint or "GPU not detected or drivers missing"
            self.vram_card.update(
                None,
                hint,
                subtitle="VRAM unavailable",
                unavailable=True,
            )

    def _update_disk_card(self, snapshot: MetricSnapshot, mount: str) -> None:
        target = self._disk_by_label.get(self.disk_var.get())
        self.disk_card.update(
            snapshot.disk_percent,
            f"{format_bytes(snapshot.disk_used)} / {format_bytes(snapshot.disk_total)}",
            subtitle=target.device if target else mount,
        )

    def _on_close(self) -> None:
        if self._poll_id:
            self.after_cancel(self._poll_id)
        shutdown_gpu()
        self.destroy()
