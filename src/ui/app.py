"""
Главное окно приложения Duplicate Finder.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

from src.config.settings import Settings, save_settings
from src.core.finder import DuplicateFinder
from src.core.models import ScanProgress, ScanResult, SearchConfig
from src.ui.pages.page_results import PageResults
from src.ui.pages.page_search import PageSearch
from src.ui.progress_window import ProgressWindow

logger = logging.getLogger(__name__)


class DuplicateFinderApp(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self, settings: Optional[Settings] = None):
        super().__init__()

        self.settings = settings or Settings()
        self._msg_queue: queue.Queue = queue.Queue()
        self._scan_thread: threading.Thread | None = None
        self._progress_window: ProgressWindow | None = None
        self._cancel_event = threading.Event()
        self._current_config: SearchConfig | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Duplicate Finder")
        self.geometry(f"{self.settings.window_width}x{self.settings.window_height}")
        self.minsize(900, 640)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.page_search = PageSearch(
            self.container,
            settings=self.settings,
            on_search=self._start_scan,
            on_cancel=self._on_close,
        )
        self.page_results = PageResults(
            self.container,
            on_back=self._show_search_page,
            on_cancel=self._on_close,
        )

        self._show_search_page()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._process_queue)

    def run(self) -> None:
        """Запуск главного цикла."""
        self.mainloop()

    def _show_search_page(self) -> None:
        self.page_results.pack_forget()
        self.page_search.pack(fill="both", expand=True)

    def _show_results_page(self, result: ScanResult) -> None:
        self.page_search.pack_forget()
        # Результаты удобнее на более широком окне
        if self.winfo_width() < 1000:
            self.geometry("1100x720")
        self.page_results.pack(fill="both", expand=True)
        self.page_results.show_results(result)

    def _start_scan(self, config: SearchConfig) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            return

        self._current_config = config
        self._cancel_event.clear()
        save_settings(self.settings)

        self._progress_window = ProgressWindow(
            self,
            title="Duplicate Finder",
            on_cancel=self._request_cancel,
        )
        self._progress_window.update()

        self._scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(config,),
            daemon=True,
            name="duplicate-scan",
        )
        self._scan_thread.start()

    def _request_cancel(self) -> None:
        """Сигнал остановки скана — проверяется воркером между файлами."""
        self._cancel_event.set()
        logger.info("Scan cancel requested by user")

    def _scan_worker(self, config: SearchConfig) -> None:
        try:
            def progress_callback(progress: ScanProgress) -> None:
                # Не забиваем очередь сотнями сообщений
                if self._msg_queue.qsize() < 32:
                    self._msg_queue.put(("progress", progress))

            def cancel_check() -> bool:
                return self._cancel_event.is_set()

            finder = DuplicateFinder(
                config,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
            )
            result = finder.scan()
            if self._cancel_event.is_set():
                result.canceled = True
            self._msg_queue.put(("done", result))
        except Exception as exc:
            logger.exception("Scan failed")
            self._msg_queue.put(("error", str(exc)))

    def _process_queue(self) -> None:
        try:
            while True:
                message_type, payload = self._msg_queue.get_nowait()
                if message_type == "progress" and self._progress_window:
                    self._progress_window.update_progress(payload)
                elif message_type == "done":
                    self._on_scan_done(payload)
                elif message_type == "error":
                    self._on_scan_error(str(payload))
        except queue.Empty:
            pass
        self.after(80, self._process_queue)

    def _close_progress(self) -> None:
        if self._progress_window is not None:
            try:
                self._progress_window.finish()
                self._progress_window.destroy()
            except Exception:  # noqa: BLE001
                pass
            self._progress_window = None

    def _on_scan_done(self, result: ScanResult) -> None:
        self._close_progress()

        if result.canceled:
            messagebox.showinfo(
                "Duplicate Finder",
                "Search canceled.",
            )
            self._show_search_page()
            return

        self._show_results_page(result)

    def _on_scan_error(self, message: str) -> None:
        self._close_progress()
        messagebox.showerror("Scan error", message)
        self._show_search_page()

    def _on_close(self) -> None:
        if self._scan_thread and self._scan_thread.is_alive():
            self._request_cancel()
            if self._progress_window is not None:
                self._progress_window.request_cancel()
        self.page_search.save_to_settings()
        save_settings(self.settings)
        self.destroy()
