"""
Окно прогресса удаления файлов.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import customtkinter as ctk

from src.core.deleter import DeleteProgress
from src.ui.components.path_display import PathDisplay
from src.utils.formatters import format_count, format_duration


class DeleteProgressWindow(ctk.CTkToplevel):
    """Попап удаления: статус, ползунок с процентами, текущий файл, Cancel."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkToplevel,
        total: int,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title("Deleting...")
        self.geometry("560x360")
        self.minsize(560, 340)
        self.resizable(True, True)
        self._canceled = False
        self._on_cancel_callback = on_cancel
        self._total = max(total, 1)

        self._started_at = time.monotonic()
        self._last_counter: int | None = None
        self._elapsed_seconds = 0.0
        self._estimated_seconds: float | None = None

        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.request_cancel)

        footer = ctk.CTkFrame(self, fg_color="transparent", height=48)
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        footer.pack_propagate(False)

        self.cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            width=110,
            height=30,
            fg_color="#b33a3a",
            hover_color="#8f2e2e",
            command=self.request_cancel,
        )
        self.cancel_btn.pack(side="right")

        frame = ctk.CTkFrame(self)
        frame.pack(side="top", fill="both", expand=True, padx=16, pady=(16, 8))

        self.phase_label = ctk.CTkLabel(
            frame,
            text="Moving files to Recycle Bin...",
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        self.phase_label.pack(fill="x", padx=10, pady=(10, 6))

        self.status_label = ctk.CTkLabel(
            frame,
            text=f"0 / {format_count(total)}",
            anchor="w",
            text_color="gray80",
        )
        self.status_label.pack(fill="x", padx=10, pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(frame, height=16)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.progress_bar.set(0)

        self.percent_label = ctk.CTkLabel(frame, text="0%", anchor="e")
        self.percent_label.pack(fill="x", padx=10, pady=(0, 2))

        self.time_label = ctk.CTkLabel(
            frame,
            text="Elapsed: 0:00  |  Estimated: —",
            anchor="e",
            text_color="gray75",
        )
        self.time_label.pack(fill="x", padx=10, pady=(0, 8))

        self.path_display = PathDisplay(frame, height=120)
        self.path_display.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.after(50, self._activate_modal)

    def _activate_modal(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:  # noqa: BLE001
            pass

    @property
    def canceled(self) -> bool:
        return self._canceled

    def request_cancel(self) -> None:
        if self._canceled:
            return
        self._canceled = True
        self.phase_label.configure(text="Canceling...")
        self.status_label.configure(text="Stopping deletion...")
        self.cancel_btn.configure(text="Canceling...", state="disabled")
        if self._on_cancel_callback:
            self._on_cancel_callback()

    def _update_timing(self, current: int, total: int) -> None:
        """Elapsed/Estimated; elapsed пересчитывается при смене каунтера."""
        if current != self._last_counter:
            self._last_counter = current
            self._elapsed_seconds = time.monotonic() - self._started_at

            if current > 0 and total > 0:
                ratio = current / total
                if ratio > 0.001:
                    remaining = max(0.0, self._elapsed_seconds / ratio - self._elapsed_seconds)
                    self._estimated_seconds = remaining
                else:
                    self._estimated_seconds = None
            else:
                self._estimated_seconds = None

        elapsed_text = format_duration(self._elapsed_seconds)
        if self._estimated_seconds is None:
            estimated_text = "—"
        else:
            estimated_text = format_duration(self._estimated_seconds)

        self.time_label.configure(
            text=f"Elapsed: {elapsed_text}  |  Estimated: {estimated_text}"
        )

    def update_progress(self, progress: DeleteProgress) -> None:
        if self._canceled and not progress.canceled:
            self.phase_label.configure(text="Canceling...")
            return

        total = max(progress.total, 1)
        ratio = progress.current / total
        self.progress_bar.set(max(0.0, min(1.0, ratio)))
        self.percent_label.configure(text=f"{int(ratio * 100)}%")
        self._update_timing(progress.current, total)
        self.status_label.configure(
            text=(
                f"{format_count(progress.current)} / {format_count(progress.total)} "
                f"file(s)"
            )
        )
        self.path_display.set_path(progress.current_path or "")

    def finish(self) -> None:
        try:
            self.grab_release()
        except Exception:  # noqa: BLE001
            pass
        self.progress_bar.set(1.0)
        self.cancel_btn.configure(state="disabled")
