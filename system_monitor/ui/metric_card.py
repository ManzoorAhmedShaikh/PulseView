"""Single metric display card."""

from __future__ import annotations

import customtkinter as ctk

from system_monitor.settings import CARD_CORNER_RADIUS, CARD_PADDING_X
from system_monitor.utils.formatting import bar_color_for_percent


class MetricCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        icon: str,
        accent: str,
        **kwargs,
    ):
        super().__init__(master, corner_radius=CARD_CORNER_RADIUS, **kwargs)
        self._accent = accent

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=CARD_PADDING_X, pady=(18, 4))

        ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=22),
            width=36,
        ).pack(side="left")

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        self.subtitle = ctk.CTkLabel(
            title_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray45", "gray60"),
            anchor="w",
        )
        self.subtitle.pack(fill="x")

        percent_row = ctk.CTkFrame(self, fg_color="transparent")
        percent_row.pack(fill="x", padx=CARD_PADDING_X, pady=(8, 4))

        self.percent_label = ctk.CTkLabel(
            percent_row,
            text="—%",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=accent,
        )
        self.percent_label.pack(side="left")

        self.detail_label = ctk.CTkLabel(
            percent_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray55"),
        )
        self.detail_label.pack(side="right", padx=(8, 0))

        self.progress = ctk.CTkProgressBar(
            self,
            height=10,
            corner_radius=5,
            progress_color=accent,
        )
        self.progress.pack(fill="x", padx=CARD_PADDING_X, pady=(4, 20))
        self.progress.set(0)

    def update(
        self,
        percent: float | None,
        detail: str,
        subtitle: str = "",
        unavailable: bool = False,
    ) -> None:
        self.subtitle.configure(text=subtitle)
        if unavailable or percent is None:
            self.percent_label.configure(text="N/A", text_color=("gray50", "gray45"))
            self.detail_label.configure(text=detail)
            self.progress.set(0)
            self.progress.configure(progress_color=("gray70", "gray35"))
            return

        pct = max(0.0, min(100.0, percent))
        color = bar_color_for_percent(pct)
        self.percent_label.configure(text=f"{pct:.0f}%", text_color=color)
        self.detail_label.configure(text=detail)
        self.progress.configure(progress_color=color)
        self.progress.set(pct / 100.0)

    def show_capacity_only(
        self,
        total_label: str,
        detail: str,
        subtitle: str,
        accent: str,
    ) -> None:
        """VRAM total without live usage (legacy radeon without radeontop)."""
        self.subtitle.configure(text=subtitle)
        self.percent_label.configure(text=total_label, text_color=accent)
        self.detail_label.configure(text=detail)
        self.progress.set(0)
        self.progress.configure(progress_color=("gray70", "gray35"))
