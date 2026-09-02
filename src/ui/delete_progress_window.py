"""
Окно прогресса удаления файлов.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from src.core.deleter import DeleteProgress
from src.ui.components.path_display import PathDisplay
from src.utils.formatters import format_count


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
        self.geometry("560x280")
        self.minsize(560, 260)
        self.resizable(True, True)
        self._canceled = False
        self._on_cancel_callback = on_cancel
        self._total = max(total, 1)

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
        self.percent_label.pack(fill="x", padx=10, pady=(0, 8))

        self.path_display = PathDisplay(frame, height=80)
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

    def update_progress(self, progress: DeleteProgress) -> None:
        if self._canceled and not progress.canceled:
            self.phase_label.configure(text="Canceling...")
            return

        total = max(progress.total, 1)
        ratio = progress.current / total
        self.progress_bar.set(max(0.0, min(1.0, ratio)))
        self.percent_label.configure(text=f"{int(ratio * 100)}%")
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
