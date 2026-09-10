"""
Панель списка масок (include / exclude), например *.tmp, Thumbs.db.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk


class MaskListPanel(ctk.CTkFrame):
    """Список масок с Add / Remove."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        label: str = "Exclude masks:",
        on_change: Optional[Callable[[], None]] = None,
    ):
        """Создать панель списка масок с полем ввода и кнопками Add/Remove."""
        super().__init__(parent)
        self.on_change = on_change
        self._masks: list[str] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(5, 0))
        ctk.CTkLabel(header, text=label, anchor="w").pack(side="left")

        entry_row = ctk.CTkFrame(self, fg_color="transparent")
        entry_row.pack(fill="x", padx=5, pady=(4, 0))

        self.mask_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text="e.g. *.jpg, *.tmp, */.git/*",
        )
        self.mask_entry.pack(side="left", fill="x", expand=True)
        self.mask_entry.bind("<Return>", lambda _e: self._add_mask())

        ctk.CTkButton(
            entry_row,
            text="Add",
            width=70,
            command=self._add_mask,
        ).pack(side="left", padx=(8, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=5, pady=5)

        self.listbox = ctk.CTkTextbox(body, height=72, wrap="none")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.configure(state="disabled")
        self.listbox.bind("<Button-1>", self._on_list_click)

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(side="right", fill="y", padx=(8, 0))

        self.remove_btn = ctk.CTkButton(
            buttons,
            text="Remove",
            width=110,
            state="disabled",
            command=self._remove_selected,
        )
        self.remove_btn.pack()

        self._selected_index: int | None = None

    def get_masks(self) -> list[str]:
        """Текущий список масок."""
        return list(self._masks)

    def set_masks(self, masks: list[str]) -> None:
        """Установить список масок."""
        self._masks = [mask.strip() for mask in masks if mask and mask.strip()]
        self._selected_index = None
        self._refresh_listbox()
        self._notify_change()

    def _notify_change(self) -> None:
        """Вызвать колбэк on_change при изменении списка."""
        if self.on_change:
            self.on_change()

    def _refresh_listbox(self) -> None:
        """Перерисовать список масок и состояние Remove."""
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        for index, mask in enumerate(self._masks):
            prefix = "> " if index == self._selected_index else "  "
            self.listbox.insert("end", f"{prefix}{mask}\n")
        self.listbox.configure(state="disabled")
        self.remove_btn.configure(
            state="normal" if self._selected_index is not None else "disabled"
        )

    def _on_list_click(self, event: object) -> None:
        """Выделить маску по клику в списке."""
        try:
            index = int(self.listbox.index(f"@{event.x},{event.y}").split(".")[0]) - 1  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return
        if 0 <= index < len(self._masks):
            self._selected_index = index
            self._refresh_listbox()

    def _add_mask(self) -> None:
        """Добавить маску из поля ввода в список."""
        mask = self.mask_entry.get().strip()
        if not mask:
            return
        if mask in self._masks:
            self._selected_index = self._masks.index(mask)
        else:
            self._masks.append(mask)
            self._selected_index = len(self._masks) - 1
        self.mask_entry.delete(0, "end")
        self._refresh_listbox()
        self._notify_change()

    def _remove_selected(self) -> None:
        """Удалить выделенную маску из списка."""
        if self._selected_index is None:
            return
        if 0 <= self._selected_index < len(self._masks):
            del self._masks[self._selected_index]
        self._selected_index = None
        self._refresh_listbox()
        self._notify_change()
