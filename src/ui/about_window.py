"""
Окно «О программе» / справка.
"""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from src.config.app_info import (
    APP_DESCRIPTION,
    APP_DEVELOPER,
    APP_LICENSE_NAME,
    APP_LICENSE_TEXT,
    APP_NAME,
    APP_VERSION,
    APP_WEBSITE,
    APP_WEBSITE_LABEL,
    HELP_RESULTS,
    HELP_SEARCH,
    HELP_TWO_LISTS,
)


class AboutWindow(ctk.CTkToplevel):
    """Полноценное окно информации о программе."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
        help_topic: str = "general",
    ):
        root = parent.winfo_toplevel()
        super().__init__(root)
        self.title(f"About {APP_NAME}")
        self.geometry("560x580")
        self.minsize(520, 480)
        self.resizable(True, True)

        self.transient(root)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        footer = ctk.CTkFrame(self, fg_color="transparent", height=48)
        footer.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Close",
            width=100,
            command=self.destroy,
        ).pack(side="right")

        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=16, pady=(16, 8))

        ctk.CTkLabel(
            body,
            text=APP_NAME,
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            body,
            text=f"Version {APP_VERSION}",
            anchor="w",
            text_color="gray75",
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Description")
        ctk.CTkLabel(
            body,
            text=APP_DESCRIPTION,
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Developer")
        ctk.CTkLabel(
            body,
            text=APP_DEVELOPER,
            anchor="w",
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "Project website")
        site_row = ctk.CTkFrame(body, fg_color="transparent")
        site_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            site_row,
            text="More projects and contacts:",
            anchor="w",
        ).pack(side="left")
        site_btn = ctk.CTkButton(
            site_row,
            text=APP_WEBSITE_LABEL,
            width=110,
            height=28,
            fg_color="transparent",
            border_width=1,
            text_color="#6cb6ff",
            command=self._open_website,
        )
        site_btn.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(
            body,
            text=APP_WEBSITE,
            anchor="w",
            text_color="gray65",
            font=ctk.CTkFont(size=12),
        ).pack(fill="x", pady=(0, 12))

        self._section_title(body, "License agreement")
        ctk.CTkLabel(
            body,
            text=APP_LICENSE_NAME,
            anchor="w",
            text_color="gray75",
        ).pack(fill="x", pady=(0, 4))
        license_box = ctk.CTkTextbox(body, height=140, wrap="word")
        license_box.pack(fill="x", pady=(0, 12))
        license_box.insert("1.0", APP_LICENSE_TEXT)
        license_box.configure(state="disabled")

        self._section_title(body, "Help")
        help_text = self._help_for_topic(help_topic)
        ctk.CTkLabel(
            body,
            text=help_text,
            anchor="w",
            justify="left",
            wraplength=500,
        ).pack(fill="x", pady=(0, 8))

        self.after(50, self._activate_modal)

    def _section_title(self, parent: ctk.CTkBaseClass, text: str) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", pady=(4, 4))

    def _help_for_topic(self, topic: str) -> str:
        if topic == "two_lists":
            return HELP_TWO_LISTS
        if topic == "results":
            return HELP_RESULTS
        return HELP_SEARCH

    def _open_website(self) -> None:
        webbrowser.open(APP_WEBSITE)

    def _activate_modal(self) -> None:
        try:
            self.lift()
            self.focus_force()
            self.grab_set()
        except Exception:  # noqa: BLE001
            pass


def show_about(
    parent: ctk.CTk | ctk.CTkToplevel | ctk.CTkFrame,
    help_topic: str = "general",
) -> AboutWindow:
    """Открыть окно About (одно на родителя)."""
    window = AboutWindow(parent, help_topic=help_topic)
    return window
