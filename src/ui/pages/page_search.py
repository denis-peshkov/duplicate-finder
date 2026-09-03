"""
Экран конфигурации поиска дубликатов (шаг 1 визарда).
"""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src.config.app_info import HELP_SEARCH, HELP_TWO_LISTS
from src.config.settings import Settings
from src.core.enumerator import parse_list_item
from src.core.models import SearchConfig
from src.ui.about_window import show_about
from src.ui.components.file_list_panel import FileListPanel
from src.ui.info_dialog import show_info_dialog


class PageSearch(ctk.CTkFrame):
    """Страница настройки поиска дубликатов."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        settings: Settings,
        on_search: Optional[Callable[[SearchConfig], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.on_search = on_search
        self.on_cancel = on_cancel

        self._create_widgets()
        self._load_from_settings()

    def _create_widgets(self) -> None:
        # Footer снизу, контент сверху — чтобы доп. список не уезжал под кнопки
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(
            footer,
            text="?",
            width=28,
            height=28,
            command=self._show_search_help,
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="About",
            width=70,
            height=28,
            command=self._show_about,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="Cancel",
            width=100,
            command=self._handle_cancel,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            footer,
            text="Search",
            width=100,
            command=self._handle_search,
        ).pack(side="right")

        main = ctk.CTkScrollableFrame(self)
        main.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        self._main = main

        ctk.CTkLabel(
            main,
            text="How would you like to search for duplicates?",
            anchor="w",
        ).pack(fill="x", padx=8, pady=(8, 4))

        mode_frame = ctk.CTkFrame(main, fg_color="transparent")
        mode_frame.pack(fill="x", padx=8)

        self.mode_var = ctk.StringVar(value="single_list")
        ctk.CTkRadioButton(
            mode_frame,
            text="Find duplicates within this single list of files",
            variable=self.mode_var,
            value="single_list",
            command=self._on_mode_change,
        ).pack(anchor="w", pady=2)

        row_two = ctk.CTkFrame(mode_frame, fg_color="transparent")
        row_two.pack(anchor="w", fill="x")
        ctk.CTkRadioButton(
            row_two,
            text="Find duplicates within these two lists of files",
            variable=self.mode_var,
            value="two_lists",
            command=self._on_mode_change,
        ).pack(side="left", pady=2)
        ctk.CTkButton(
            row_two,
            text="?",
            width=24,
            height=24,
            command=self._show_two_lists_help,
        ).pack(side="left", padx=(4, 0))

        self.list1_panel = FileListPanel(
            main,
            label="File List 1:",
            include_subfolders=self.settings.include_subfolders1,
        )
        self.list1_panel.pack(fill="x", padx=8, pady=(8, 4))

        self.list2_panel = FileListPanel(
            main,
            label="File List 2:",
            include_subfolders=self.settings.include_subfolders2,
        )
        # Не pack сразу — покажем только в режиме two_lists

        self.match_section = ctk.CTkFrame(main, fg_color="transparent")
        self.match_section.pack(fill="x", padx=8, pady=(4, 4))

        ctk.CTkLabel(
            self.match_section,
            text="What kind of duplicates would you like to find?",
            anchor="w",
        ).pack(fill="x", pady=(4, 4))

        match_frame = ctk.CTkFrame(self.match_section, fg_color="transparent")
        match_frame.pack(fill="x")

        self.match_var = ctk.StringVar(value="exact")
        ctk.CTkRadioButton(
            match_frame,
            text="Exact duplicate (identical files)",
            variable=self.match_var,
            value="exact",
        ).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(
            match_frame,
            text="Same filename",
            variable=self.match_var,
            value="filename",
        ).pack(anchor="w", pady=2)

        self.images_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.match_section,
            text="Find images only",
            variable=self.images_only_var,
        ).pack(anchor="w", pady=(8, 8))

        self._on_mode_change()

    def _on_mode_change(self) -> None:
        """Показать/скрыть File List 2 строго между List 1 и блоком критериев."""
        if self.mode_var.get() == "two_lists":
            self.list2_panel.pack(
                fill="x",
                padx=8,
                pady=(4, 8),
                after=self.list1_panel,
            )
            self.list1_panel.set_list_height(90)
            self.list2_panel.set_list_height(90)
            top = self.winfo_toplevel()
            if top.winfo_height() < 640:
                top.geometry(f"{max(top.winfo_width(), 640)}x680")
        else:
            self.list2_panel.pack_forget()
            self.list1_panel.set_list_height(120)

    def _load_from_settings(self) -> None:
        self.mode_var.set(self.settings.search_mode)
        self.match_var.set(self.settings.match_type)
        self.images_only_var.set(self.settings.images_only)
        self.list1_panel.set_items(self.settings.list1_paths)
        self.list2_panel.set_items(self.settings.list2_paths)
        self.list1_panel.set_include_subfolders(self.settings.include_subfolders1)
        self.list2_panel.set_include_subfolders(self.settings.include_subfolders2)
        self._on_mode_change()

    def save_to_settings(self) -> None:
        """Сохранить текущие значения в settings."""
        self.settings.search_mode = self.mode_var.get()
        self.settings.match_type = self.match_var.get()
        self.settings.images_only = bool(self.images_only_var.get())
        self.settings.list1_paths = self.list1_panel.get_items()
        self.settings.list2_paths = self.list2_panel.get_items()
        self.settings.include_subfolders1 = self.list1_panel.get_include_subfolders()
        self.settings.include_subfolders2 = self.list2_panel.get_include_subfolders()

    def build_config(self) -> SearchConfig | None:
        """Собрать SearchConfig с валидацией."""
        list1_items = self.list1_panel.get_items()
        list2_items = self.list2_panel.get_items()

        if not list1_items:
            messagebox.showwarning("Duplicate Finder", "File List 1 cannot be empty.")
            return None

        if self.mode_var.get() == "two_lists" and not list2_items:
            messagebox.showwarning("Duplicate Finder", "File List 2 cannot be empty in two-list mode.")
            return None

        list1_paths = [parse_list_item(item)[0] for item in list1_items]
        list2_paths = [parse_list_item(item)[0] for item in list2_items]

        return SearchConfig(
            mode=self.mode_var.get(),  # type: ignore[arg-type]
            list1_paths=list1_paths,
            list2_paths=list2_paths,
            include_subfolders1=self.list1_panel.get_include_subfolders(),
            include_subfolders2=self.list2_panel.get_include_subfolders(),
            match_type=self.match_var.get(),  # type: ignore[arg-type]
            images_only=bool(self.images_only_var.get()),
        )

    def _handle_search(self) -> None:
        config = self.build_config()
        if config is None:
            return
        self.save_to_settings()
        if self.on_search:
            self.on_search(config)

    def _handle_cancel(self) -> None:
        if self.on_cancel:
            self.on_cancel()

    def _show_about(self) -> None:
        show_about(self)

    def _show_search_help(self) -> None:
        show_info_dialog(self, "Search", HELP_SEARCH, width=520)

    def _show_two_lists_help(self) -> None:
        show_info_dialog(self, "Two lists", HELP_TWO_LISTS, width=520)
