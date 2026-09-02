"""
Панель списка файлов/папок с кнопками управления.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from src.core.enumerator import format_list_item, parse_list_item


class FileListPanel(ctk.CTkFrame):
    """Блок списка путей с кнопками Add/Remove/Modify."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        include_subfolders: bool = True,
        on_change: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.on_change = on_change
        self._items: list[tuple[str, bool]] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 0))

        ctk.CTkLabel(header, text=label, anchor="w").pack(side="left")

        self.subfolders_var = ctk.BooleanVar(value=include_subfolders)
        self.subfolders_cb = ctk.CTkCheckBox(
            header,
            text="Include subfolders",
            variable=self.subfolders_var,
            command=self._notify_change,
        )
        self.subfolders_cb.pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=5, pady=5)

        self.listbox = ctk.CTkTextbox(body, height=120, wrap="none")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.configure(state="disabled")

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(side="right", fill="y", padx=(8, 0))

        self.add_files_btn = ctk.CTkButton(
            buttons, text="Add Files...", width=110, command=self._add_files
        )
        self.add_files_btn.pack(pady=(0, 4))

        self.add_folder_btn = ctk.CTkButton(
            buttons, text="Add Folder...", width=110, command=self._add_folder
        )
        self.add_folder_btn.pack(pady=(0, 4))

        self.remove_btn = ctk.CTkButton(
            buttons,
            text="Remove",
            width=110,
            state="disabled",
            command=self._remove_selected,
        )
        self.remove_btn.pack(pady=(0, 4))

        self.modify_btn = ctk.CTkButton(
            buttons,
            text="Modify...",
            width=110,
            state="disabled",
            command=self._modify_selected,
        )
        self.modify_btn.pack(pady=(0, 4))

        self._selected_index: int | None = None
        self.listbox.bind("<Button-1>", self._on_list_click)

    def set_list_height(self, height: int) -> None:
        """Изменить высоту списка (для режима одного/двух списков)."""
        self.listbox.configure(height=height)

    def get_items(self) -> list[str]:
        """Получить элементы списка в формате отображения."""
        return [format_list_item(Path(path), is_folder) for path, is_folder in self._items]

    def set_items(self, items: list[str]) -> None:
        """Установить элементы списка."""
        self._items = []
        for item in items:
            path, is_folder = parse_list_item(item)
            self._items.append((str(path), is_folder))
        self._refresh_listbox()
        self._notify_change()

    def get_include_subfolders(self) -> bool:
        """Включён ли обход подпапок."""
        return bool(self.subfolders_var.get())

    def set_include_subfolders(self, value: bool) -> None:
        """Установить флаг подпапок."""
        self.subfolders_var.set(value)

    def _notify_change(self) -> None:
        if self.on_change:
            self.on_change()

    def _refresh_listbox(self) -> None:
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        for index, (path, is_folder) in enumerate(self._items):
            prefix = "> " if index == self._selected_index else "  "
            line = format_list_item(Path(path), is_folder)
            self.listbox.insert("end", f"{prefix}{line}\n")
        self.listbox.configure(state="disabled")
        has_selection = self._selected_index is not None and 0 <= self._selected_index < len(self._items)
        state = "normal" if has_selection else "disabled"
        self.remove_btn.configure(state=state)
        self.modify_btn.configure(state=state)

    def _on_list_click(self, _event: object) -> None:
        if not self._items:
            return
        index = self.listbox.index("insert").split(".")[0]
        try:
            self._selected_index = max(0, int(index) - 1)
        except ValueError:
            self._selected_index = 0
        if self._selected_index >= len(self._items):
            self._selected_index = len(self._items) - 1
        self._refresh_listbox()

    def _add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Select files")
        if not paths:
            return
        for path in paths:
            self._items.append((path, False))
        self._selected_index = len(self._items) - 1
        self._refresh_listbox()
        self._notify_change()

    def _add_folder(self) -> None:
        path = filedialog.askdirectory(title="Select folder")
        if not path:
            return
        self._items.append((path, True))
        self._selected_index = len(self._items) - 1
        self._refresh_listbox()
        self._notify_change()

    def _remove_selected(self) -> None:
        if self._selected_index is None or not self._items:
            return
        del self._items[self._selected_index]
        if self._items:
            self._selected_index = min(self._selected_index, len(self._items) - 1)
        else:
            self._selected_index = None
        self._refresh_listbox()
        self._notify_change()

    def _modify_selected(self) -> None:
        if self._selected_index is None:
            return
        path, is_folder = self._items[self._selected_index]
        dialog = ModifyPathDialog(self, path, is_folder)
        self.wait_window(dialog)
        if dialog.result is not None:
            new_path, new_is_folder = dialog.result
            self._items[self._selected_index] = (new_path, new_is_folder)
            self._refresh_listbox()
            self._notify_change()


class ModifyPathDialog(ctk.CTkToplevel):
    """Диалог изменения пути в списке."""

    def __init__(self, parent: ctk.CTkBaseClass, path: str, is_folder: bool):
        super().__init__(parent)
        self.title("Modify path")
        self.geometry("480x160")
        self.resizable(False, False)
        self.result: tuple[str, bool] | None = None

        self.transient(parent.winfo_toplevel())
        self.grab_set()

        ctk.CTkLabel(self, text="Path:").pack(anchor="w", padx=16, pady=(16, 4))
        self.path_entry = ctk.CTkEntry(self, width=440)
        self.path_entry.pack(padx=16)
        self.path_entry.insert(0, path)

        self.folder_var = ctk.BooleanVar(value=is_folder)
        ctk.CTkCheckBox(
            self,
            text="Folder (append * when saved)",
            variable=self.folder_var,
        ).pack(anchor="w", padx=16, pady=8)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=(8, 16))

        ctk.CTkButton(buttons, text="OK", width=90, command=self._ok).pack(side="right", padx=(8, 0))
        ctk.CTkButton(buttons, text="Cancel", width=90, command=self.destroy).pack(side="right")

    def _ok(self) -> None:
        text = self.path_entry.get().strip()
        if not text:
            messagebox.showwarning("Modify path", "Path cannot be empty.")
            return
        self.result = (text.rstrip("*").rstrip("\\").rstrip("/"), bool(self.folder_var.get()))
        self.destroy()
