"""
Вспомогательные виджеты UI.
"""

from __future__ import annotations

import customtkinter as ctk


class PathDisplay(ctk.CTkTextbox):
    """Многострочное поле для длинных путей с автопереносом."""

    def __init__(self, master: ctk.CTkBaseClass, height: int = 96, **kwargs):
        super().__init__(
            master,
            height=height,
            wrap="char",
            activate_scrollbars=True,
            border_width=0,
            fg_color="transparent",
            text_color="gray70",
            font=ctk.CTkFont(size=12),
            **kwargs,
        )
        self.configure(state="disabled")

    def set_path(self, path: str) -> None:
        """Показать путь целиком с переносом по ширине."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        if path:
            self.insert("1.0", path)
            self.see("end")
        self.configure(state="disabled")
