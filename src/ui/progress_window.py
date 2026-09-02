"""
Окно прогресса сканирования.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

import customtkinter as ctk

from src.core.models import ScanProgress
from src.ui.components.path_display import PathDisplay
from src.utils.formatters import format_count, format_duration


class ProgressWindow(ctk.CTkToplevel):
    """Окно прогресса: этап, статус, проценты, текущий файл, Cancel."""

    def __init__(
        self,
        parent: ctk.CTk,
        title: str = "Duplicate Finder",
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry("640x400")
        self.minsize(640, 380)
        self.resizable(True, True)
        self._canceled = False
        self._on_cancel_callback = on_cancel
        self._indeterminate = True

        self._step_phase: str | None = None
        self._step_started_at = time.monotonic()
        self._last_counter: int | None = None
        self._elapsed_seconds = 0.0
        self._estimated_seconds: float | None = None

        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.request_cancel)

        # Cancel вне контент-фрейма — размер не прыгает
        footer = ctk.CTkFrame(self, fg_color="transparent", height=52)
        footer.pack(side="bottom", fill="x", padx=20, pady=(0, 16))
        footer.pack_propagate(False)

        self.cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            width=120,
            height=32,
            fg_color="#b33a3a",
            hover_color="#8f2e2e",
            command=self.request_cancel,
        )
        self.cancel_btn.pack(side="right")

        frame = ctk.CTkFrame(self)
        frame.pack(side="top", fill="both", expand=True, padx=20, pady=(20, 8))

        self.phase_label = ctk.CTkLabel(
            frame,
            text="Preparing scan...",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        )
        self.phase_label.pack(fill="x", padx=12, pady=(12, 4))

        self.status_label = ctk.CTkLabel(
            frame,
            text="Starting...",
            anchor="w",
            text_color="gray80",
        )
        self.status_label.pack(fill="x", padx=12, pady=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(frame, height=18)
        self.progress_bar.pack(fill="x", padx=12, pady=(0, 6))
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        self.percent_label = ctk.CTkLabel(frame, text="", anchor="e")
        self.percent_label.pack(fill="x", padx=12, pady=(0, 2))

        self.time_label = ctk.CTkLabel(
            frame,
            text="Elapsed: 0:00  |  Estimated: —",
            anchor="e",
            text_color="gray75",
        )
        self.time_label.pack(fill="x", padx=12, pady=(0, 8))

        self.stats_label = ctk.CTkLabel(
            frame,
            text="Files scanned: 0",
            anchor="w",
        )
        self.stats_label.pack(fill="x", padx=12)

        self.path_display = PathDisplay(frame, height=110)
        self.path_display.pack(fill="both", expand=True, padx=12, pady=(10, 12))

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
        """Запросить остановку сканирования в любой момент."""
        if self._canceled:
            return
        self._canceled = True
        self.phase_label.configure(text="Canceling...")
        self.status_label.configure(text="Stopping scan, please wait...")
        self.cancel_btn.configure(text="Canceling...", state="disabled")
        if self._on_cancel_callback:
            self._on_cancel_callback()

    def _step_counter(self, progress: ScanProgress) -> int:
        if progress.phase == "enumerating":
            return progress.files_scanned
        if progress.phase == "hashing":
            return progress.files_hashed
        if progress.phase == "matching":
            if progress.percent is not None:
                return int(progress.percent * 10000)
            return progress.groups_found
        return progress.files_scanned + progress.files_hashed

    def _step_ratio(self, progress: ScanProgress) -> float | None:
        if progress.total_files > 0 and progress.phase == "hashing":
            return progress.files_hashed / max(progress.total_files, 1)
        if progress.percent is not None:
            return max(0.0, min(1.0, progress.percent))
        return None

    def _update_timing(self, progress: ScanProgress) -> None:
        """Elapsed/Estimated для текущего шага; elapsed — при смене каунтера."""
        if progress.phase != self._step_phase:
            self._step_phase = progress.phase
            self._step_started_at = time.monotonic()
            self._last_counter = None
            self._elapsed_seconds = 0.0
            self._estimated_seconds = None

        counter = self._step_counter(progress)
        if counter != self._last_counter:
            self._last_counter = counter
            self._elapsed_seconds = time.monotonic() - self._step_started_at

            ratio = self._step_ratio(progress)
            if ratio is not None and ratio > 0.001 and counter > 0:
                total_estimate = self._elapsed_seconds / ratio
                remaining = max(0.0, total_estimate - self._elapsed_seconds)
                self._estimated_seconds = remaining
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

    def update_progress(self, progress: ScanProgress) -> None:
        """Обновить этап, проценты, счётчики и текущий файл."""
        if self._canceled:
            self.phase_label.configure(text="Canceling...")
            self.status_label.configure(text="Stopping scan, please wait...")
            return

        phase_labels = {
            "enumerating": "Enumerating files...",
            "hashing": "Hashing / comparing files...",
            "matching": "Matching duplicates...",
            "done": "Finishing...",
            "canceled": "Canceled",
        }
        self.phase_label.configure(
            text=phase_labels.get(progress.phase, progress.phase)
        )

        if progress.phase == "enumerating":
            status = (
                progress.status_text
                or f"Scanning Files: {format_count(progress.files_scanned)} file(s) found"
            )
        elif progress.phase in {"hashing", "matching"}:
            status = (
                progress.status_text
                or (
                    f"Comparing Files: {format_count(progress.groups_found)} "
                    f"set(s) of duplicates found"
                )
            )
        else:
            status = progress.status_text or "Working..."
        self.status_label.configure(text=status)

        if progress.total_files > 0 and progress.phase == "hashing":
            ratio = progress.files_hashed / max(progress.total_files, 1)
            self._set_determinate(ratio)
            self.percent_label.configure(
                text=(
                    f"{int(ratio * 100)}%  "
                    f"({format_count(progress.files_hashed)} / "
                    f"{format_count(progress.total_files)})"
                )
            )
        elif progress.percent is not None:
            self._set_determinate(progress.percent)
            self.percent_label.configure(text=f"{int(progress.percent * 100)}%")
        else:
            self._set_indeterminate()
            self.percent_label.configure(text="")

        self._update_timing(progress)

        hashed_part = format_count(progress.files_hashed)
        if progress.total_files:
            hashed_part = f"{hashed_part} / {format_count(progress.total_files)}"

        self.stats_label.configure(
            text=(
                f"Files scanned: {format_count(progress.files_scanned)}  |  "
                f"Hashed: {hashed_part}  |  "
                f"Groups: {format_count(progress.groups_found)}"
            )
        )

        self.path_display.set_path(progress.current_path or "")

    def _set_indeterminate(self) -> None:
        if not self._indeterminate:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
            self._indeterminate = True

    def _set_determinate(self, value: float) -> None:
        if self._indeterminate:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self._indeterminate = False
        self.progress_bar.set(max(0.0, min(1.0, value)))

    def finish(self) -> None:
        """Завершить отображение прогресса."""
        try:
            self.grab_release()
        except Exception:  # noqa: BLE001
            pass
        if self._indeterminate:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self._indeterminate = False
        self.progress_bar.set(1.0)
        self.cancel_btn.configure(state="disabled")
